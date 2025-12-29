"""
VELAS Trading System - Data Layer Tests

Tests for:
- BinanceRestClient: REST API functionality
- CandleStorage: Parquet storage operations
- BinanceWebSocketClient: WebSocket connection (mock)
"""

import asyncio
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.data.binance_rest import (
    BinanceRestClient,
    BinanceAPIError,
    KlineData,
    MarketType,
    RateLimiter,
)
from backend.data.storage import (
    CandleStorage,
    DataStats,
    MultiStorageManager,
)
from backend.data.binance_ws import (
    BinanceWebSocketClient,
    KlineEvent,
    TickerEvent,
)


class TestRateLimiter(unittest.TestCase):
    """Tests for rate limiter."""
    
    def test_init(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(max_weight=1200, window_seconds=60)
        self.assertEqual(limiter.max_weight, 1200)
        self.assertEqual(limiter.window_seconds, 60)
    
    def test_acquire_no_wait(self):
        """Test acquiring without hitting limit."""
        async def run():
            limiter = RateLimiter(max_weight=100)
            # Should not wait
            await limiter.acquire(1)
            self.assertEqual(len(limiter.requests), 1)
        
        asyncio.run(run())
    
    def test_acquire_multiple(self):
        """Test multiple acquires."""
        async def run():
            limiter = RateLimiter(max_weight=100)
            for _ in range(10):
                await limiter.acquire(1)
            self.assertEqual(len(limiter.requests), 10)
        
        asyncio.run(run())


class TestBinanceRestClient(unittest.TestCase):
    """Tests for Binance REST client."""
    
    def test_init_spot(self):
        """Test client initialization for spot market."""
        client = BinanceRestClient(market_type=MarketType.SPOT)
        self.assertEqual(client.market_type, MarketType.SPOT)
        self.assertEqual(client.base_url, "https://api.binance.com")
    
    def test_init_futures(self):
        """Test client initialization for futures market."""
        client = BinanceRestClient(market_type=MarketType.FUTURES)
        self.assertEqual(client.market_type, MarketType.FUTURES)
        self.assertEqual(client.base_url, "https://fapi.binance.com")
    
    def test_interval_to_ms(self):
        """Test interval string to milliseconds conversion."""
        self.assertEqual(BinanceRestClient._interval_to_ms("1m"), 60000)
        self.assertEqual(BinanceRestClient._interval_to_ms("30m"), 30 * 60000)
        self.assertEqual(BinanceRestClient._interval_to_ms("1h"), 3600000)
        self.assertEqual(BinanceRestClient._interval_to_ms("1d"), 86400000)
    
    def test_klines_to_dataframe(self):
        """Test converting klines to DataFrame."""
        klines = [
            KlineData(
                open_time=1704067200000,
                open=42000.0,
                high=42500.0,
                low=41800.0,
                close=42300.0,
                volume=1000.0,
                close_time=1704070799999,
                quote_volume=42150000.0,
                trades=5000,
                taker_buy_base=600.0,
                taker_buy_quote=25290000.0,
            ),
            KlineData(
                open_time=1704070800000,
                open=42300.0,
                high=42600.0,
                low=42200.0,
                close=42500.0,
                volume=800.0,
                close_time=1704074399999,
                quote_volume=34000000.0,
                trades=4000,
                taker_buy_base=500.0,
                taker_buy_quote=21250000.0,
            ),
        ]
        
        client = BinanceRestClient()
        df = client.klines_to_dataframe(klines)
        
        self.assertEqual(len(df), 2)
        self.assertIn("open", df.columns)
        self.assertIn("close", df.columns)
        self.assertIn("datetime", df.index.names or [df.index.name])
        self.assertEqual(df.iloc[0]["open"], 42000.0)
        self.assertEqual(df.iloc[1]["close"], 42500.0)
    
    def test_klines_to_dataframe_empty(self):
        """Test converting empty klines list."""
        client = BinanceRestClient()
        df = client.klines_to_dataframe([])
        self.assertTrue(df.empty)


class TestCandleStorage(unittest.TestCase):
    """Tests for candle storage."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = CandleStorage(self.temp_dir)
        
        # Create sample data
        self.sample_df = pd.DataFrame({
            "timestamp": [1704067200000 + i * 3600000 for i in range(100)],
            "open": [100 + i * 0.1 for i in range(100)],
            "high": [101 + i * 0.1 for i in range(100)],
            "low": [99 + i * 0.1 for i in range(100)],
            "close": [100.5 + i * 0.1 for i in range(100)],
            "volume": [1000 + i * 10 for i in range(100)],
        })
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load(self):
        """Test saving and loading data."""
        rows = self.storage.save(self.sample_df, "BTCUSDT", "1h", overwrite=True)
        self.assertEqual(rows, 100)
        
        loaded = self.storage.load("BTCUSDT", "1h")
        self.assertEqual(len(loaded), 100)
    
    def test_exists(self):
        """Test checking if data exists."""
        self.assertFalse(self.storage.exists("BTCUSDT", "1h"))
        
        self.storage.save(self.sample_df, "BTCUSDT", "1h", overwrite=True)
        
        self.assertTrue(self.storage.exists("BTCUSDT", "1h"))
        self.assertFalse(self.storage.exists("ETHUSDT", "1h"))
    
    def test_append(self):
        """Test appending new data."""
        self.storage.save(self.sample_df, "BTCUSDT", "1h", overwrite=True)
        
        # Create new data
        new_timestamps = [1704067200000 + (100 + i) * 3600000 for i in range(10)]
        new_df = pd.DataFrame({
            "timestamp": new_timestamps,
            "open": [110 + i * 0.1 for i in range(10)],
            "high": [111 + i * 0.1 for i in range(10)],
            "low": [109 + i * 0.1 for i in range(10)],
            "close": [110.5 + i * 0.1 for i in range(10)],
            "volume": [1100 + i * 10 for i in range(10)],
        })
        
        added = self.storage.append(new_df, "BTCUSDT", "1h")
        self.assertEqual(added, 10)
        
        loaded = self.storage.load("BTCUSDT", "1h")
        self.assertEqual(len(loaded), 110)
    
    def test_append_with_duplicates(self):
        """Test appending with duplicate timestamps."""
        self.storage.save(self.sample_df, "BTCUSDT", "1h", overwrite=True)
        
        # Create data with overlapping timestamps
        new_df = pd.DataFrame({
            "timestamp": [1704067200000 + (90 + i) * 3600000 for i in range(20)],
            "open": [190 + i * 0.1 for i in range(20)],
            "high": [191 + i * 0.1 for i in range(20)],
            "low": [189 + i * 0.1 for i in range(20)],
            "close": [190.5 + i * 0.1 for i in range(20)],
            "volume": [1900 + i * 10 for i in range(20)],
        })
        
        added = self.storage.append(new_df, "BTCUSDT", "1h", deduplicate=True)
        
        loaded = self.storage.load("BTCUSDT", "1h")
        # Should have 100 original + 10 new (10 were duplicates)
        self.assertEqual(len(loaded), 110)
    
    def test_get_time_range(self):
        """Test getting time range."""
        self.storage.save(self.sample_df, "BTCUSDT", "1h", overwrite=True)
        
        start, end = self.storage.get_time_range("BTCUSDT", "1h")
        
        self.assertEqual(start, 1704067200000)
        self.assertEqual(end, 1704067200000 + 99 * 3600000)
    
    def test_find_gaps(self):
        """Test gap detection."""
        # Create data with gap
        timestamps = (
            [1704067200000 + i * 3600000 for i in range(50)] +
            [1704067200000 + (55 + i) * 3600000 for i in range(45)]  # 5 hour gap
        )
        
        df = pd.DataFrame({
            "timestamp": timestamps,
            "open": [100] * 95,
            "high": [101] * 95,
            "low": [99] * 95,
            "close": [100] * 95,
            "volume": [1000] * 95,
        })
        
        self.storage.save(df, "BTCUSDT", "1h", overwrite=True)
        gaps = self.storage.find_gaps("BTCUSDT", "1h")
        
        self.assertEqual(len(gaps), 1)
    
    def test_get_stats(self):
        """Test getting statistics."""
        self.storage.save(self.sample_df, "BTCUSDT", "1h", overwrite=True)
        
        stats = self.storage.get_stats("BTCUSDT", "1h")
        
        self.assertIsInstance(stats, DataStats)
        self.assertEqual(stats.symbol, "BTCUSDT")
        self.assertEqual(stats.interval, "1h")
        self.assertEqual(stats.rows, 100)
        self.assertFalse(stats.has_gaps)
    
    def test_list_symbols(self):
        """Test listing symbols."""
        self.storage.save(self.sample_df, "BTCUSDT", "1h", overwrite=True)
        self.storage.save(self.sample_df, "ETHUSDT", "1h", overwrite=True)
        
        symbols = self.storage.list_symbols()
        
        self.assertIn("BTCUSDT", symbols)
        self.assertIn("ETHUSDT", symbols)
    
    def test_list_intervals(self):
        """Test listing intervals."""
        self.storage.save(self.sample_df, "BTCUSDT", "1h", overwrite=True)
        self.storage.save(self.sample_df, "BTCUSDT", "30m", overwrite=True)
        
        intervals = self.storage.list_intervals("BTCUSDT")
        
        self.assertIn("1h", intervals)
        self.assertIn("30m", intervals)
    
    def test_delete(self):
        """Test deleting data."""
        self.storage.save(self.sample_df, "BTCUSDT", "1h", overwrite=True)
        self.assertTrue(self.storage.exists("BTCUSDT", "1h"))
        
        self.storage.delete("BTCUSDT", "1h")
        self.assertFalse(self.storage.exists("BTCUSDT", "1h"))
    
    def test_filtered_load(self):
        """Test loading with time filters."""
        self.storage.save(self.sample_df, "BTCUSDT", "1h", overwrite=True)
        
        start_ts = 1704067200000 + 20 * 3600000
        end_ts = 1704067200000 + 40 * 3600000
        
        filtered = self.storage.load(
            "BTCUSDT", "1h",
            start_time=start_ts,
            end_time=end_ts
        )
        
        self.assertTrue(len(filtered) <= 21)  # 20 to 40 inclusive
        self.assertTrue(filtered["timestamp"].min() >= start_ts)
        self.assertTrue(filtered["timestamp"].max() <= end_ts)


class TestKlineEvent(unittest.TestCase):
    """Tests for KlineEvent."""
    
    def test_from_ws_message(self):
        """Test creating KlineEvent from WebSocket message."""
        message = {
            "e": "kline",
            "E": 1704067200000,
            "s": "BTCUSDT",
            "k": {
                "t": 1704067200000,
                "T": 1704070799999,
                "s": "BTCUSDT",
                "i": "1h",
                "f": 100,
                "L": 200,
                "o": "42000.00",
                "c": "42300.00",
                "h": "42500.00",
                "l": "41800.00",
                "v": "1000.00",
                "n": 5000,
                "x": True,
                "q": "42150000.00",
                "V": "600.00",
                "Q": "25290000.00",
            }
        }
        
        event = KlineEvent.from_ws_message(message)
        
        self.assertEqual(event.symbol, "BTCUSDT")
        self.assertEqual(event.interval, "1h")
        self.assertEqual(event.open, 42000.0)
        self.assertEqual(event.close, 42300.0)
        self.assertTrue(event.is_closed)


class TestBinanceWebSocketClient(unittest.TestCase):
    """Tests for WebSocket client."""
    
    def test_init(self):
        """Test client initialization."""
        client = BinanceWebSocketClient()
        self.assertFalse(client.use_futures)
        self.assertEqual(client.ws_url, BinanceWebSocketClient.SPOT_WS)
    
    def test_init_futures(self):
        """Test futures client initialization."""
        client = BinanceWebSocketClient(use_futures=True)
        self.assertTrue(client.use_futures)
        self.assertEqual(client.ws_url, BinanceWebSocketClient.FUTURES_WS)
    
    def test_stream_names(self):
        """Test stream name generation."""
        self.assertEqual(
            BinanceWebSocketClient.kline_stream_name("BTCUSDT", "1h"),
            "btcusdt@kline_1h"
        )
        self.assertEqual(
            BinanceWebSocketClient.ticker_stream_name("ETHUSDT"),
            "ethusdt@ticker"
        )
    
    def test_subscribe_klines(self):
        """Test subscribing to kline streams."""
        client = BinanceWebSocketClient()
        client.subscribe_klines(["BTCUSDT", "ETHUSDT"], ["1h", "30m"])
        
        self.assertIn("btcusdt@kline_1h", client._streams)
        self.assertIn("btcusdt@kline_30m", client._streams)
        self.assertIn("ethusdt@kline_1h", client._streams)
        self.assertIn("ethusdt@kline_30m", client._streams)
        self.assertEqual(len(client._streams), 4)
    
    def test_unsubscribe_all(self):
        """Test unsubscribing from all streams."""
        client = BinanceWebSocketClient()
        client.subscribe_klines(["BTCUSDT"], ["1h"])
        self.assertTrue(len(client._streams) > 0)
        
        client.unsubscribe_all()
        self.assertEqual(len(client._streams), 0)
    
    def test_build_stream_url(self):
        """Test building stream URL."""
        client = BinanceWebSocketClient()
        
        # No streams
        self.assertEqual(client._build_stream_url(), client.ws_url)
        
        # With streams
        client.subscribe_klines(["BTCUSDT"], ["1h"])
        url = client._build_stream_url()
        self.assertIn("streams=", url)
        self.assertIn("btcusdt@kline_1h", url)


class TestMultiStorageManager(unittest.TestCase):
    """Tests for multi-storage manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = CandleStorage(self.temp_dir)
        self.manager = MultiStorageManager(self.storage)
        
        # Create sample data
        self.sample_df = pd.DataFrame({
            "timestamp": [1704067200000 + i * 3600000 for i in range(50)],
            "open": [100] * 50,
            "high": [101] * 50,
            "low": [99] * 50,
            "close": [100] * 50,
            "volume": [1000] * 50,
        })
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_all_stats(self):
        """Test getting all statistics."""
        self.storage.save(self.sample_df, "BTCUSDT", "1h", overwrite=True)
        self.storage.save(self.sample_df, "ETHUSDT", "1h", overwrite=True)
        
        stats = self.manager.get_all_stats()
        
        self.assertEqual(len(stats), 2)
        symbols = [s.symbol for s in stats]
        self.assertIn("BTCUSDT", symbols)
        self.assertIn("ETHUSDT", symbols)
    
    def test_validate_all(self):
        """Test validating all data."""
        self.storage.save(self.sample_df, "BTCUSDT", "1h", overwrite=True)
        
        # No gaps
        all_gaps = self.manager.validate_all()
        self.assertEqual(len(all_gaps), 0)


class TestIntegration(unittest.TestCase):
    """Integration tests (requires network)."""
    
    @unittest.skipIf(
        os.environ.get("SKIP_NETWORK_TESTS", "1") == "1",
        "Skipping network tests"
    )
    def test_live_api_connection(self):
        """Test live connection to Binance API."""
        async def run():
            async with BinanceRestClient() as client:
                server_time = await client.get_server_time()
                self.assertIsInstance(server_time, int)
                self.assertGreater(server_time, 0)
        
        asyncio.run(run())
    
    @unittest.skipIf(
        os.environ.get("SKIP_NETWORK_TESTS", "1") == "1",
        "Skipping network tests"
    )
    def test_live_klines_download(self):
        """Test downloading klines from live API."""
        async def run():
            async with BinanceRestClient() as client:
                klines = await client.get_klines("BTCUSDT", "1h", limit=10)
                self.assertEqual(len(klines), 10)
                self.assertIsInstance(klines[0], KlineData)
        
        asyncio.run(run())


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRateLimiter))
    suite.addTests(loader.loadTestsFromTestCase(TestBinanceRestClient))
    suite.addTests(loader.loadTestsFromTestCase(TestCandleStorage))
    suite.addTests(loader.loadTestsFromTestCase(TestKlineEvent))
    suite.addTests(loader.loadTestsFromTestCase(TestBinanceWebSocketClient))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiStorageManager))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
