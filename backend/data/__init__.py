"""
VELAS Trading System - Data Layer

Provides data access components:
- BinanceRestClient: REST API for historical data
- BinanceWebSocketClient: WebSocket for real-time data
- CandleStorage: Parquet storage for OHLCV data

Usage:
    from backend.data import BinanceRestClient, CandleStorage
    
    # Download historical data
    async with BinanceRestClient() as client:
        klines = await client.get_historical_klines("BTCUSDT", "1h", start_ms)
        df = client.klines_to_dataframe(klines)
    
    # Save to storage
    storage = CandleStorage("./data/candles")
    storage.save(df, "BTCUSDT", "1h")
    
    # Real-time streaming
    ws = BinanceWebSocketClient()
    ws.on_kline = handle_kline
    ws.subscribe_klines(["BTCUSDT"], ["1h"])
    await ws.run()
"""

from .binance_rest import (
    BinanceRestClient,
    BinanceAPIError,
    KlineData,
    MarketType,
    BinanceInterval,
    download_pair_history,
)

from .binance_ws import (
    BinanceWebSocketClient,
    KlineEvent,
    TickerEvent,
    MultiSymbolKlineAggregator,
)

from .storage import (
    CandleStorage,
    DataStats,
    MultiStorageManager,
)

__all__ = [
    # REST Client
    "BinanceRestClient",
    "BinanceAPIError",
    "KlineData",
    "MarketType",
    "BinanceInterval",
    "download_pair_history",
    
    # WebSocket Client
    "BinanceWebSocketClient",
    "KlineEvent",
    "TickerEvent",
    "MultiSymbolKlineAggregator",
    
    # Storage
    "CandleStorage",
    "DataStats",
    "MultiStorageManager",
]

__version__ = "0.2.0"
