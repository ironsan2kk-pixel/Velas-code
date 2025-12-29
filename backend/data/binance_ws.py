"""
VELAS Trading System - Binance WebSocket Client

Real-time market data streaming via WebSocket.
Supports kline/candlestick streams for multiple symbols and timeframes.

Features:
- Multi-stream subscription (combined streams)
- Automatic reconnection with exponential backoff
- Heartbeat/ping-pong for connection health
- Callback-based event handling
- Thread-safe message queue
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

import websockets
from websockets.exceptions import (
    ConnectionClosed,
    ConnectionClosedError,
    ConnectionClosedOK,
)

logger = logging.getLogger(__name__)


class StreamType(Enum):
    """WebSocket stream types."""
    KLINE = "kline"
    TRADE = "trade"
    TICKER = "ticker"
    MINI_TICKER = "miniTicker"
    BOOK_TICKER = "bookTicker"
    DEPTH = "depth"


@dataclass
class KlineEvent:
    """Real-time kline/candlestick event."""
    event_type: str
    event_time: int
    symbol: str
    interval: str
    start_time: int
    close_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    trades: int
    is_closed: bool
    quote_volume: float
    taker_buy_base: float
    taker_buy_quote: float
    
    @classmethod
    def from_ws_message(cls, data: Dict[str, Any]) -> "KlineEvent":
        """Create KlineEvent from WebSocket message."""
        k = data["k"]
        return cls(
            event_type=data["e"],
            event_time=data["E"],
            symbol=data["s"],
            interval=k["i"],
            start_time=k["t"],
            close_time=k["T"],
            open=float(k["o"]),
            high=float(k["h"]),
            low=float(k["l"]),
            close=float(k["c"]),
            volume=float(k["v"]),
            trades=k["n"],
            is_closed=k["x"],
            quote_volume=float(k["q"]),
            taker_buy_base=float(k["V"]),
            taker_buy_quote=float(k["Q"]),
        )


@dataclass
class TickerEvent:
    """24hr ticker event."""
    symbol: str
    price_change: float
    price_change_percent: float
    weighted_avg_price: float
    last_price: float
    last_qty: float
    open_price: float
    high_price: float
    low_price: float
    volume: float
    quote_volume: float
    open_time: int
    close_time: int
    trades: int
    
    @classmethod
    def from_ws_message(cls, data: Dict[str, Any]) -> "TickerEvent":
        """Create TickerEvent from WebSocket message."""
        return cls(
            symbol=data["s"],
            price_change=float(data["p"]),
            price_change_percent=float(data["P"]),
            weighted_avg_price=float(data["w"]),
            last_price=float(data["c"]),
            last_qty=float(data["Q"]),
            open_price=float(data["o"]),
            high_price=float(data["h"]),
            low_price=float(data["l"]),
            volume=float(data["v"]),
            quote_volume=float(data["q"]),
            open_time=data["O"],
            close_time=data["C"],
            trades=data["n"],
        )


@dataclass
class ConnectionState:
    """WebSocket connection state."""
    connected: bool = False
    connecting: bool = False
    reconnect_count: int = 0
    last_message_time: float = 0
    last_pong_time: float = 0
    subscriptions: Set[str] = field(default_factory=set)


# Type aliases for callbacks
KlineCallback = Callable[[KlineEvent], None]
TickerCallback = Callable[[TickerEvent], None]
ErrorCallback = Callable[[Exception], None]
ConnectCallback = Callable[[], None]


class BinanceWebSocketClient:
    """
    Async WebSocket client for Binance real-time data.
    
    Usage:
        client = BinanceWebSocketClient()
        
        # Register callbacks
        client.on_kline = lambda e: print(f"Kline: {e.symbol} {e.close}")
        
        # Subscribe to streams
        await client.subscribe_klines(["BTCUSDT", "ETHUSDT"], ["1h", "30m"])
        
        # Run (blocking)
        await client.run()
    """
    
    # WebSocket endpoints
    SPOT_WS = "wss://stream.binance.com:9443/ws"
    SPOT_COMBINED_WS = "wss://stream.binance.com:9443/stream"
    FUTURES_WS = "wss://fstream.binance.com/ws"
    FUTURES_COMBINED_WS = "wss://fstream.binance.com/stream"
    
    def __init__(
        self,
        use_futures: bool = False,
        ping_interval: float = 180.0,
        ping_timeout: float = 10.0,
        reconnect_delay: float = 5.0,
        max_reconnects: int = 10,
    ):
        """
        Initialize WebSocket client.
        
        Args:
            use_futures: Use Futures WebSocket endpoint
            ping_interval: Interval between ping messages (seconds)
            ping_timeout: Timeout for pong response (seconds)
            reconnect_delay: Initial delay between reconnects (seconds)
            max_reconnects: Maximum reconnection attempts
        """
        self.use_futures = use_futures
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.reconnect_delay = reconnect_delay
        self.max_reconnects = max_reconnects
        
        # Set endpoints
        if use_futures:
            self.ws_url = self.FUTURES_WS
            self.combined_url = self.FUTURES_COMBINED_WS
        else:
            self.ws_url = self.SPOT_WS
            self.combined_url = self.SPOT_COMBINED_WS
        
        # Connection state
        self.state = ConnectionState()
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._running = False
        self._stop_event = asyncio.Event()
        
        # Stream subscriptions
        self._streams: Set[str] = set()
        
        # Callbacks
        self.on_kline: Optional[KlineCallback] = None
        self.on_ticker: Optional[TickerCallback] = None
        self.on_error: Optional[ErrorCallback] = None
        self.on_connect: Optional[ConnectCallback] = None
        self.on_disconnect: Optional[ConnectCallback] = None
        
        # Message queue for processing
        self._message_queue: asyncio.Queue = asyncio.Queue()
        
        # Tasks
        self._receive_task: Optional[asyncio.Task] = None
        self._process_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
    
    def _build_stream_url(self) -> str:
        """Build WebSocket URL with streams."""
        if not self._streams:
            return self.ws_url
        
        streams = "/".join(sorted(self._streams))
        return f"{self.combined_url}?streams={streams}"
    
    @staticmethod
    def kline_stream_name(symbol: str, interval: str) -> str:
        """Get kline stream name."""
        return f"{symbol.lower()}@kline_{interval}"
    
    @staticmethod
    def ticker_stream_name(symbol: str) -> str:
        """Get 24hr ticker stream name."""
        return f"{symbol.lower()}@ticker"
    
    @staticmethod
    def mini_ticker_stream_name(symbol: str) -> str:
        """Get mini ticker stream name."""
        return f"{symbol.lower()}@miniTicker"
    
    def subscribe_klines(
        self, 
        symbols: List[str], 
        intervals: List[str]
    ) -> None:
        """
        Subscribe to kline streams.
        
        Args:
            symbols: List of trading pairs (e.g., ["BTCUSDT", "ETHUSDT"])
            intervals: List of intervals (e.g., ["1h", "30m"])
        """
        for symbol in symbols:
            for interval in intervals:
                stream = self.kline_stream_name(symbol, interval)
                self._streams.add(stream)
                self.state.subscriptions.add(stream)
        
        logger.info(f"Subscribed to {len(self._streams)} kline streams")
    
    def subscribe_tickers(self, symbols: List[str]) -> None:
        """
        Subscribe to 24hr ticker streams.
        
        Args:
            symbols: List of trading pairs
        """
        for symbol in symbols:
            stream = self.ticker_stream_name(symbol)
            self._streams.add(stream)
            self.state.subscriptions.add(stream)
        
        logger.info(f"Subscribed to {len(symbols)} ticker streams")
    
    def unsubscribe_all(self) -> None:
        """Remove all subscriptions."""
        self._streams.clear()
        self.state.subscriptions.clear()
    
    async def connect(self) -> bool:
        """
        Establish WebSocket connection.
        
        Returns:
            True if connected successfully
        """
        if self.state.connected:
            logger.warning("Already connected")
            return True
        
        self.state.connecting = True
        url = self._build_stream_url()
        
        try:
            logger.info(f"Connecting to {url}")
            
            self._websocket = await websockets.connect(
                url,
                ping_interval=None,  # We handle pings manually
                ping_timeout=None,
                close_timeout=10,
            )
            
            self.state.connected = True
            self.state.connecting = False
            self.state.last_message_time = time.time()
            self.state.last_pong_time = time.time()
            
            logger.info("WebSocket connected successfully")
            
            # Call connect callback
            if self.on_connect:
                try:
                    self.on_connect()
                except Exception as e:
                    logger.error(f"Connect callback error: {e}")
            
            return True
            
        except Exception as e:
            self.state.connecting = False
            logger.error(f"Connection failed: {e}")
            
            if self.on_error:
                try:
                    self.on_error(e)
                except Exception as cb_err:
                    logger.error(f"Error callback failed: {cb_err}")
            
            return False
    
    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        self.state.connected = False
        self.state.connecting = False
        
        if self._websocket:
            try:
                await self._websocket.close()
            except Exception as e:
                logger.debug(f"Error closing websocket: {e}")
            finally:
                self._websocket = None
        
        # Call disconnect callback
        if self.on_disconnect:
            try:
                self.on_disconnect()
            except Exception as e:
                logger.error(f"Disconnect callback error: {e}")
        
        logger.info("WebSocket disconnected")
    
    async def _reconnect(self) -> bool:
        """
        Attempt to reconnect with exponential backoff.
        
        Returns:
            True if reconnected successfully
        """
        await self.disconnect()
        
        delay = self.reconnect_delay
        
        for attempt in range(self.max_reconnects):
            self.state.reconnect_count = attempt + 1
            
            logger.info(
                f"Reconnection attempt {attempt + 1}/{self.max_reconnects} "
                f"in {delay:.1f}s"
            )
            await asyncio.sleep(delay)
            
            if await self.connect():
                self.state.reconnect_count = 0
                return True
            
            # Exponential backoff with max 5 minutes
            delay = min(delay * 2, 300)
        
        logger.error(f"Failed to reconnect after {self.max_reconnects} attempts")
        return False
    
    async def _receive_messages(self) -> None:
        """Receive messages from WebSocket and put in queue."""
        while self._running and self.state.connected:
            try:
                if not self._websocket:
                    break
                
                message = await asyncio.wait_for(
                    self._websocket.recv(),
                    timeout=self.ping_interval + 10
                )
                
                self.state.last_message_time = time.time()
                
                # Parse and queue message
                data = json.loads(message)
                await self._message_queue.put(data)
                
            except asyncio.TimeoutError:
                logger.warning("Receive timeout, connection may be stale")
                break
                
            except ConnectionClosed as e:
                logger.warning(f"Connection closed: {e}")
                break
                
            except Exception as e:
                logger.error(f"Receive error: {e}")
                if self.on_error:
                    self.on_error(e)
                break
    
    async def _process_messages(self) -> None:
        """Process messages from queue."""
        while self._running:
            try:
                # Wait for message with timeout
                try:
                    data = await asyncio.wait_for(
                        self._message_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Handle combined stream format
                if "stream" in data and "data" in data:
                    stream = data["stream"]
                    payload = data["data"]
                else:
                    stream = None
                    payload = data
                
                # Dispatch to appropriate handler
                event_type = payload.get("e", "")
                
                if event_type == "kline":
                    await self._handle_kline(payload)
                elif event_type in ("24hrTicker", "24hrMiniTicker"):
                    await self._handle_ticker(payload)
                else:
                    logger.debug(f"Unknown event type: {event_type}")
                
            except Exception as e:
                logger.error(f"Message processing error: {e}")
                if self.on_error:
                    try:
                        self.on_error(e)
                    except Exception:
                        pass
    
    async def _handle_kline(self, data: Dict[str, Any]) -> None:
        """Handle kline event."""
        if not self.on_kline:
            return
        
        try:
            event = KlineEvent.from_ws_message(data)
            self.on_kline(event)
        except Exception as e:
            logger.error(f"Kline handler error: {e}")
    
    async def _handle_ticker(self, data: Dict[str, Any]) -> None:
        """Handle ticker event."""
        if not self.on_ticker:
            return
        
        try:
            event = TickerEvent.from_ws_message(data)
            self.on_ticker(event)
        except Exception as e:
            logger.error(f"Ticker handler error: {e}")
    
    async def _heartbeat(self) -> None:
        """Send periodic pings to keep connection alive."""
        while self._running and self.state.connected:
            try:
                await asyncio.sleep(self.ping_interval)
                
                if not self._websocket or not self.state.connected:
                    break
                
                # Send ping
                pong_waiter = await self._websocket.ping()
                
                try:
                    await asyncio.wait_for(pong_waiter, timeout=self.ping_timeout)
                    self.state.last_pong_time = time.time()
                    logger.debug("Pong received")
                except asyncio.TimeoutError:
                    logger.warning("Pong timeout, connection may be dead")
                    break
                    
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break
    
    async def run(self) -> None:
        """
        Run the WebSocket client (blocking).
        
        Handles connection, message receiving, and auto-reconnection.
        """
        self._running = True
        self._stop_event.clear()
        
        while self._running:
            # Connect
            if not await self.connect():
                if not await self._reconnect():
                    logger.error("Giving up on reconnection")
                    break
                continue
            
            # Start tasks
            self._receive_task = asyncio.create_task(self._receive_messages())
            self._process_task = asyncio.create_task(self._process_messages())
            self._heartbeat_task = asyncio.create_task(self._heartbeat())
            
            # Wait for any task to complete (usually means disconnection)
            done, pending = await asyncio.wait(
                [self._receive_task, self._heartbeat_task, self._stop_event.wait()],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                if isinstance(task, asyncio.Task):
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Stop the process task
            if self._process_task and not self._process_task.done():
                self._process_task.cancel()
                try:
                    await self._process_task
                except asyncio.CancelledError:
                    pass
            
            # Check if we should stop
            if self._stop_event.is_set():
                logger.info("Stop requested")
                break
            
            # Try to reconnect
            if not await self._reconnect():
                break
        
        await self.disconnect()
        self._running = False
    
    async def stop(self) -> None:
        """Stop the WebSocket client."""
        logger.info("Stopping WebSocket client...")
        self._running = False
        self._stop_event.set()


class MultiSymbolKlineAggregator:
    """
    Aggregates kline events for multiple symbols and timeframes.
    
    Useful for building real-time OHLCV DataFrames.
    """
    
    def __init__(self, max_candles: int = 500):
        """
        Initialize aggregator.
        
        Args:
            max_candles: Maximum candles to keep per symbol/interval
        """
        self.max_candles = max_candles
        self._data: Dict[str, Dict[str, List[KlineEvent]]] = {}
        self._lock = asyncio.Lock()
    
    async def add_kline(self, event: KlineEvent) -> None:
        """Add or update kline data."""
        async with self._lock:
            symbol = event.symbol
            interval = event.interval
            
            if symbol not in self._data:
                self._data[symbol] = {}
            if interval not in self._data[symbol]:
                self._data[symbol][interval] = []
            
            candles = self._data[symbol][interval]
            
            # Find or append
            if candles and candles[-1].start_time == event.start_time:
                # Update existing candle
                candles[-1] = event
            else:
                # Add new candle
                candles.append(event)
                
                # Trim if too many
                if len(candles) > self.max_candles:
                    self._data[symbol][interval] = candles[-self.max_candles:]
    
    async def get_latest(
        self, 
        symbol: str, 
        interval: str
    ) -> Optional[KlineEvent]:
        """Get latest kline for symbol/interval."""
        async with self._lock:
            if symbol in self._data and interval in self._data[symbol]:
                candles = self._data[symbol][interval]
                if candles:
                    return candles[-1]
            return None
    
    async def get_candles(
        self, 
        symbol: str, 
        interval: str, 
        count: int = 100
    ) -> List[KlineEvent]:
        """Get recent candles for symbol/interval."""
        async with self._lock:
            if symbol in self._data and interval in self._data[symbol]:
                return self._data[symbol][interval][-count:]
            return []


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
        """Example: Subscribe to BTC and ETH klines."""
        print("VELAS Data Layer - Binance WebSocket Test")
        print("=" * 50)
        
        client = BinanceWebSocketClient()
        aggregator = MultiSymbolKlineAggregator()
        
        # Stats
        stats = {"klines": 0, "closed": 0}
        
        async def on_kline(event: KlineEvent):
            """Handle kline event."""
            stats["klines"] += 1
            await aggregator.add_kline(event)
            
            # Log closed candles
            if event.is_closed:
                stats["closed"] += 1
                dt = datetime.fromtimestamp(event.start_time / 1000, tz=timezone.utc)
                print(
                    f"[CLOSED] {event.symbol} {event.interval} {dt.strftime('%H:%M')} | "
                    f"O:{event.open:.2f} H:{event.high:.2f} "
                    f"L:{event.low:.2f} C:{event.close:.2f} V:{event.volume:.2f}"
                )
            else:
                # Print live updates less frequently
                if stats["klines"] % 10 == 0:
                    print(
                        f"[LIVE] {event.symbol} {event.interval} | "
                        f"Price: {event.close:.2f} | "
                        f"Events: {stats['klines']} | "
                        f"Closed: {stats['closed']}"
                    )
        
        def on_connect():
            print("✅ Connected to Binance WebSocket")
        
        def on_disconnect():
            print("❌ Disconnected from Binance WebSocket")
        
        def on_error(e: Exception):
            print(f"⚠️ Error: {e}")
        
        # Set callbacks
        client.on_kline = lambda e: asyncio.create_task(on_kline(e))
        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_error = on_error
        
        # Subscribe to streams
        symbols = ["BTCUSDT", "ETHUSDT"]
        intervals = ["1m", "1h"]  # Use 1m for faster testing
        
        client.subscribe_klines(symbols, intervals)
        
        print(f"Subscribing to: {symbols} @ {intervals}")
        print("Press Ctrl+C to stop\n")
        
        # Run for 60 seconds for testing
        try:
            run_task = asyncio.create_task(client.run())
            await asyncio.sleep(60)
            await client.stop()
            await run_task
        except KeyboardInterrupt:
            print("\nStopping...")
            await client.stop()
        
        print(f"\n📊 Final stats: {stats['klines']} events, {stats['closed']} closed candles")
        print("✅ WebSocket test completed!")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
