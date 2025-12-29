# VELAS-02: Data Layer

## Overview

This phase implements the data layer for VELAS Trading System:
- Binance REST API client for historical data
- Binance WebSocket client for real-time data
- Parquet storage for efficient OHLCV data management

## Components

### 1. Binance REST Client (`backend/data/binance_rest.py`)

Async client for Binance public API (no API keys required).

**Features:**
- Rate limiting with automatic backoff
- Pagination for large historical downloads
- Supports both Spot and Futures endpoints
- DataFrame conversion for pandas integration

**Usage:**
```python
from backend.data import BinanceRestClient

async with BinanceRestClient() as client:
    # Get recent klines
    klines = await client.get_klines("BTCUSDT", "1h", limit=100)
    
    # Download full history
    klines = await client.get_historical_klines(
        symbol="BTCUSDT",
        interval="1h",
        start_time=start_ms,
    )
    
    # Convert to DataFrame
    df = client.klines_to_dataframe(klines)
```

### 2. Binance WebSocket Client (`backend/data/binance_ws.py`)

Real-time market data streaming via WebSocket.

**Features:**
- Multi-stream subscription (combined streams)
- Automatic reconnection with exponential backoff
- Heartbeat/ping-pong for connection health
- Callback-based event handling

**Usage:**
```python
from backend.data import BinanceWebSocketClient, KlineEvent

client = BinanceWebSocketClient()

def handle_kline(event: KlineEvent):
    if event.is_closed:
        print(f"New candle: {event.symbol} {event.close}")

client.on_kline = handle_kline
client.subscribe_klines(["BTCUSDT", "ETHUSDT"], ["1h", "30m"])

await client.run()
```

### 3. Parquet Storage (`backend/data/storage.py`)

Efficient storage for OHLCV candlestick data.

**Features:**
- Parquet format for compression and fast reads
- Automatic partitioning by symbol/interval
- Incremental updates (append new data)
- Gap detection and validation

**Usage:**
```python
from backend.data import CandleStorage

storage = CandleStorage("./data/candles")

# Save data
storage.save(df, "BTCUSDT", "1h")

# Load with filters
df = storage.load("BTCUSDT", "1h", start_time=start_ms)

# Append new data
storage.append(new_df, "BTCUSDT", "1h")

# Get statistics
stats = storage.get_stats("BTCUSDT", "1h")
```

### 4. Download Script (`scripts/download_history.py`)

Command-line tool for downloading historical data.

**Usage:**
```bash
# Download all pairs (20) × all timeframes (30m, 1h, 2h)
python scripts/download_history.py

# Download single symbol
python scripts/download_history.py --symbol BTCUSDT

# Download 6 months instead of default 12
python scripts/download_history.py --months 6

# Incremental update (download only new data)
python scripts/download_history.py --update

# Parallel downloads
python scripts/download_history.py --parallel 5
```

## Configuration

### pairs.yaml
Defines trading pairs and their sectors for portfolio diversification.

### config.example.yaml
Main configuration file. Copy to `config.yaml` and adjust:
- Storage paths
- API settings
- Trading parameters
- Volatility regimes

## Directory Structure

```
velas-02/
├── backend/
│   └── data/
│       ├── __init__.py
│       ├── binance_rest.py    # REST API client
│       ├── binance_ws.py      # WebSocket client
│       └── storage.py         # Parquet storage
├── config/
│   ├── pairs.yaml             # Trading pairs
│   └── config.example.yaml    # Configuration template
├── scripts/
│   └── download_history.py    # Download script
├── tests/
│   └── test_data_layer.py     # Unit tests
├── requirements.txt
├── run_tests.bat              # Windows test runner
├── run_tests.sh               # Unix test runner
└── README.md
```

## Testing

### Run all tests:
```bash
# Windows
run_tests.bat

# Unix/Linux/Mac
./run_tests.sh

# Or directly with pytest
python -m pytest tests/ -v
```

### Run with network tests:
```bash
SKIP_NETWORK_TESTS=0 python -m pytest tests/ -v
```

## Data Format

### Parquet Schema
| Column | Type | Description |
|--------|------|-------------|
| timestamp | int64 | Open time (ms) |
| open | float64 | Open price |
| high | float64 | High price |
| low | float64 | Low price |
| close | float64 | Close price |
| volume | float64 | Volume (base asset) |
| close_time | int64 | Close time (ms) |
| quote_volume | float64 | Volume (quote asset) |
| trades | int64 | Number of trades |
| taker_buy_base | float64 | Taker buy volume (base) |
| taker_buy_quote | float64 | Taker buy volume (quote) |

### Storage Structure
```
data/candles/
├── BTCUSDT/
│   ├── 30m.parquet
│   ├── 1h.parquet
│   └── 2h.parquet
├── ETHUSDT/
│   ├── 30m.parquet
│   └── ...
└── ...
```

## Next Steps

After completing VELAS-02, proceed to:
- **VELAS-03**: Backtesting Engine
- **VELAS-04**: Strategy Optimization

## Dependencies

- Python 3.11+
- pandas, numpy, pyarrow
- aiohttp, websockets
- pyyaml

Install with:
```bash
pip install -r requirements.txt
```
