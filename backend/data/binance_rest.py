"""
VELAS Trading System - Binance REST API Client

Public API client for fetching market data (no API keys required).
Supports both Spot and Futures endpoints.

Features:
- Klines/candlesticks download with pagination
- Ticker prices and 24h statistics
- Exchange info and trading rules
- Rate limiting and retry logic
- Async/await pattern for efficiency
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import aiohttp
import pandas as pd

logger = logging.getLogger(__name__)


class MarketType(Enum):
    """Market type for API endpoints."""
    SPOT = "spot"
    FUTURES = "futures"


class BinanceInterval(Enum):
    """Supported Binance kline intervals."""
    M1 = "1m"
    M3 = "3m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H2 = "2h"
    H4 = "4h"
    H6 = "6h"
    H8 = "8h"
    H12 = "12h"
    D1 = "1d"
    D3 = "3d"
    W1 = "1w"
    MO1 = "1M"


@dataclass
class KlineData:
    """Container for kline/candlestick data."""
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_volume: float
    trades: int
    taker_buy_base: float
    taker_buy_quote: float


class RateLimiter:
    """
    Rate limiter for Binance API.
    
    Binance has weight-based rate limits:
    - Spot: 1200 weight/minute
    - Futures: 2400 weight/minute
    """
    
    def __init__(self, max_weight: int = 1200, window_seconds: int = 60):
        self.max_weight = max_weight
        self.window_seconds = window_seconds
        self.requests: List[Tuple[float, int]] = []
        self._lock = asyncio.Lock()
    
    async def acquire(self, weight: int = 1) -> None:
        """Wait if necessary to respect rate limits."""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            
            # Remove old requests outside the window
            cutoff = now - self.window_seconds
            self.requests = [
                (ts, w) for ts, w in self.requests 
                if ts > cutoff
            ]
            
            # Calculate current weight
            current_weight = sum(w for _, w in self.requests)
            
            # Wait if we would exceed the limit
            if current_weight + weight > self.max_weight:
                if self.requests:
                    oldest_ts = self.requests[0][0]
                    wait_time = oldest_ts + self.window_seconds - now + 0.1
                    if wait_time > 0:
                        logger.debug(f"Rate limit: waiting {wait_time:.2f}s")
                        await asyncio.sleep(wait_time)
                        # Recursive call after waiting
                        return await self.acquire(weight)
            
            # Record this request
            self.requests.append((now, weight))


class BinanceAPIError(Exception):
    """Binance API error."""
    
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error {code}: {message}")


class BinanceRestClient:
    """
    Async REST client for Binance public API.
    
    Usage:
        async with BinanceRestClient() as client:
            klines = await client.get_klines("BTCUSDT", "1h", limit=100)
    """
    
    # API endpoints
    SPOT_BASE = "https://api.binance.com"
    FUTURES_BASE = "https://fapi.binance.com"
    
    # Endpoint paths
    SPOT_KLINES = "/api/v3/klines"
    SPOT_TICKER_PRICE = "/api/v3/ticker/price"
    SPOT_TICKER_24H = "/api/v3/ticker/24hr"
    SPOT_EXCHANGE_INFO = "/api/v3/exchangeInfo"
    SPOT_TIME = "/api/v3/time"
    
    FUTURES_KLINES = "/fapi/v1/klines"
    FUTURES_TICKER_PRICE = "/fapi/v1/ticker/price"
    FUTURES_TICKER_24H = "/fapi/v1/ticker/24hr"
    FUTURES_EXCHANGE_INFO = "/fapi/v1/exchangeInfo"
    FUTURES_TIME = "/fapi/v1/time"
    
    # Weight for endpoints
    WEIGHTS = {
        "klines": 1,  # 1 weight for up to 100-500 candles, 2 for 500-1000
        "ticker_price": 1,
        "ticker_24h": 1,  # Single symbol
        "ticker_24h_all": 40,  # All symbols
        "exchange_info": 10,
        "time": 1,
    }
    
    # Max candles per request
    MAX_KLINES = 1000
    
    def __init__(
        self,
        market_type: MarketType = MarketType.SPOT,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize Binance REST client.
        
        Args:
            market_type: SPOT or FUTURES market
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.market_type = market_type
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Set base URL based on market type
        if market_type == MarketType.SPOT:
            self.base_url = self.SPOT_BASE
            self.klines_path = self.SPOT_KLINES
            self.ticker_price_path = self.SPOT_TICKER_PRICE
            self.ticker_24h_path = self.SPOT_TICKER_24H
            self.exchange_info_path = self.SPOT_EXCHANGE_INFO
            self.time_path = self.SPOT_TIME
            max_weight = 1200
        else:
            self.base_url = self.FUTURES_BASE
            self.klines_path = self.FUTURES_KLINES
            self.ticker_price_path = self.FUTURES_TICKER_PRICE
            self.ticker_24h_path = self.FUTURES_TICKER_24H
            self.exchange_info_path = self.FUTURES_EXCHANGE_INFO
            self.time_path = self.FUTURES_TIME
            max_weight = 2400
        
        self.rate_limiter = RateLimiter(max_weight=max_weight)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self) -> "BinanceRestClient":
        """Async context manager entry."""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        if self._session:
            await self._session.close()
            self._session = None
    
    @property
    def session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None:
            raise RuntimeError(
                "Client not initialized. Use 'async with BinanceRestClient()' "
                "or call connect() first."
            )
        return self._session
    
    async def connect(self) -> None:
        """Initialize HTTP session (alternative to context manager)."""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
    
    async def close(self) -> None:
        """Close HTTP session."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        weight: int = 1,
    ) -> Any:
        """
        Make HTTP request with rate limiting and retries.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            params: Query parameters
            weight: Request weight for rate limiting
            
        Returns:
            JSON response data
            
        Raises:
            BinanceAPIError: On API error response
            aiohttp.ClientError: On network error
        """
        url = urljoin(self.base_url, path)
        
        for attempt in range(self.max_retries):
            try:
                # Wait for rate limit
                await self.rate_limiter.acquire(weight)
                
                async with self.session.request(
                    method, url, params=params
                ) as response:
                    data = await response.json()
                    
                    # Check for API errors
                    if isinstance(data, dict) and "code" in data:
                        raise BinanceAPIError(data["code"], data.get("msg", ""))
                    
                    return data
                    
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise
    
    async def get_server_time(self) -> int:
        """
        Get Binance server time.
        
        Returns:
            Server timestamp in milliseconds
        """
        data = await self._request("GET", self.time_path, weight=1)
        return data["serverTime"]
    
    async def get_exchange_info(
        self, symbols: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get exchange trading rules and symbol information.
        
        Args:
            symbols: Optional list of symbols to filter
            
        Returns:
            Exchange info dictionary
        """
        params = {}
        if symbols:
            # Use JSON array format for multiple symbols
            import json
            params["symbols"] = json.dumps(symbols)
        
        return await self._request(
            "GET", self.exchange_info_path, params=params, weight=10
        )
    
    async def get_ticker_price(
        self, symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current price(s).
        
        Args:
            symbol: Optional symbol (returns all if None)
            
        Returns:
            Price data (single dict or list of dicts)
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        
        return await self._request(
            "GET", self.ticker_price_path, params=params, weight=1
        )
    
    async def get_ticker_24h(
        self, symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get 24hr ticker statistics.
        
        Args:
            symbol: Optional symbol (returns all if None)
            
        Returns:
            24hr ticker data
        """
        params = {}
        weight = 40 if symbol is None else 1
        if symbol:
            params["symbol"] = symbol
        
        return await self._request(
            "GET", self.ticker_24h_path, params=params, weight=weight
        )
    
    async def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> List[KlineData]:
        """
        Get klines/candlestick data.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            interval: Kline interval (e.g., "1h", "30m")
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            limit: Number of candles (max 1000)
            
        Returns:
            List of KlineData objects
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": min(limit, self.MAX_KLINES),
        }
        
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        
        # Weight depends on limit
        weight = 2 if limit > 500 else 1
        
        data = await self._request(
            "GET", self.klines_path, params=params, weight=weight
        )
        
        return [
            KlineData(
                open_time=int(k[0]),
                open=float(k[1]),
                high=float(k[2]),
                low=float(k[3]),
                close=float(k[4]),
                volume=float(k[5]),
                close_time=int(k[6]),
                quote_volume=float(k[7]),
                trades=int(k[8]),
                taker_buy_base=float(k[9]),
                taker_buy_quote=float(k[10]),
            )
            for k in data
        ]
    
    async def get_historical_klines(
        self,
        symbol: str,
        interval: str,
        start_time: int,
        end_time: Optional[int] = None,
        progress_callback: Optional[callable] = None,
    ) -> List[KlineData]:
        """
        Download historical klines with pagination.
        
        Automatically handles pagination for large date ranges.
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds (default: now)
            progress_callback: Optional callback(downloaded, total_estimate)
            
        Returns:
            List of all KlineData in the range
        """
        if end_time is None:
            end_time = int(datetime.now(timezone.utc).timestamp() * 1000)
        
        # Calculate interval in milliseconds
        interval_ms = self._interval_to_ms(interval)
        
        all_klines: List[KlineData] = []
        current_start = start_time
        
        # Estimate total candles
        total_estimate = (end_time - start_time) // interval_ms
        
        while current_start < end_time:
            klines = await self.get_klines(
                symbol=symbol,
                interval=interval,
                start_time=current_start,
                end_time=end_time,
                limit=self.MAX_KLINES,
            )
            
            if not klines:
                break
            
            all_klines.extend(klines)
            
            # Progress callback
            if progress_callback:
                progress_callback(len(all_klines), total_estimate)
            
            # Move start time to after the last candle
            last_close_time = klines[-1].close_time
            current_start = last_close_time + 1
            
            # Small delay between paginated requests
            await asyncio.sleep(0.1)
            
            # Break if we got less than limit (end of data)
            if len(klines) < self.MAX_KLINES:
                break
        
        return all_klines
    
    @staticmethod
    def _interval_to_ms(interval: str) -> int:
        """Convert interval string to milliseconds."""
        unit = interval[-1]
        value = int(interval[:-1])
        
        multipliers = {
            "m": 60 * 1000,
            "h": 60 * 60 * 1000,
            "d": 24 * 60 * 60 * 1000,
            "w": 7 * 24 * 60 * 60 * 1000,
            "M": 30 * 24 * 60 * 60 * 1000,
        }
        
        return value * multipliers.get(unit, 60 * 1000)
    
    def klines_to_dataframe(self, klines: List[KlineData]) -> pd.DataFrame:
        """
        Convert klines list to pandas DataFrame.
        
        Args:
            klines: List of KlineData objects
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume, etc.
        """
        if not klines:
            return pd.DataFrame()
        
        df = pd.DataFrame([
            {
                "timestamp": k.open_time,
                "open": k.open,
                "high": k.high,
                "low": k.low,
                "close": k.close,
                "volume": k.volume,
                "close_time": k.close_time,
                "quote_volume": k.quote_volume,
                "trades": k.trades,
                "taker_buy_base": k.taker_buy_base,
                "taker_buy_quote": k.taker_buy_quote,
            }
            for k in klines
        ])
        
        # Convert timestamp to datetime
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        
        # Set datetime as index
        df.set_index("datetime", inplace=True)
        
        return df


async def download_pair_history(
    symbol: str,
    interval: str,
    months: int = 12,
    market_type: MarketType = MarketType.SPOT,
) -> pd.DataFrame:
    """
    Convenience function to download historical data for a symbol.
    
    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        interval: Timeframe (e.g., "1h", "30m")
        months: Number of months of history
        market_type: SPOT or FUTURES
        
    Returns:
        DataFrame with OHLCV data
    """
    # Calculate start time
    now = datetime.now(timezone.utc)
    start = now - pd.DateOffset(months=months)
    start_ms = int(start.timestamp() * 1000)
    
    async with BinanceRestClient(market_type=market_type) as client:
        def progress(downloaded: int, total: int):
            pct = min(100, downloaded * 100 // max(1, total))
            logger.info(f"Downloading {symbol} {interval}: {pct}% ({downloaded}/{total})")
        
        klines = await client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_time=start_ms,
            progress_callback=progress,
        )
        
        return client.klines_to_dataframe(klines)


# -----------------------------------------------------------------------------
# Example usage
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    async def main():
        """Example: Download BTC 1h data."""
        print("VELAS Data Layer - Binance REST Client Test")
        print("=" * 50)
        
        async with BinanceRestClient() as client:
            # Test server time
            server_time = await client.get_server_time()
            dt = datetime.fromtimestamp(server_time / 1000, tz=timezone.utc)
            print(f"Server time: {dt.isoformat()}")
            
            # Test current price
            price = await client.get_ticker_price("BTCUSDT")
            print(f"BTC price: ${float(price['price']):,.2f}")
            
            # Test klines
            klines = await client.get_klines("BTCUSDT", "1h", limit=10)
            print(f"\nLast 10 candles:")
            for k in klines[-3:]:
                dt = datetime.fromtimestamp(k.open_time / 1000, tz=timezone.utc)
                print(f"  {dt.strftime('%Y-%m-%d %H:%M')} | "
                      f"O:{k.open:.2f} H:{k.high:.2f} L:{k.low:.2f} C:{k.close:.2f}")
            
            # Test historical download (1 month)
            print(f"\nDownloading 1 month of BTCUSDT 1h data...")
            df = await download_pair_history("BTCUSDT", "1h", months=1)
            print(f"Downloaded {len(df)} candles")
            print(f"Date range: {df.index.min()} to {df.index.max()}")
            print(f"\nDataFrame preview:")
            print(df.tail())
        
        print("\n✅ REST Client test completed successfully!")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
