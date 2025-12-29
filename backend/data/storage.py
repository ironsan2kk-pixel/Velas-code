"""
VELAS Trading System - Data Storage

Parquet-based storage for OHLCV candlestick data.
Organized by symbol and timeframe with efficient append and query operations.

Features:
- Parquet format for compression and fast reads
- Automatic partitioning by symbol/interval
- Incremental updates (append new data)
- Gap detection and validation
- Memory-efficient loading with filters
"""

import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


@dataclass
class DataStats:
    """Statistics for stored data."""
    symbol: str
    interval: str
    rows: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    file_size_mb: float
    has_gaps: bool
    gap_count: int


class CandleStorage:
    """
    Parquet storage for candlestick data.
    
    Directory structure:
        storage_path/
        ├── BTCUSDT/
        │   ├── 30m.parquet
        │   ├── 1h.parquet
        │   └── 2h.parquet
        ├── ETHUSDT/
        │   ├── 30m.parquet
        │   └── ...
        └── ...
    
    Usage:
        storage = CandleStorage("./data/candles")
        
        # Save data
        storage.save(df, "BTCUSDT", "1h")
        
        # Load data
        df = storage.load("BTCUSDT", "1h")
        
        # Append new data
        storage.append(new_df, "BTCUSDT", "1h")
    """
    
    # Column schema
    COLUMNS = [
        "timestamp",      # Open time (ms)
        "open",           # Open price
        "high",           # High price
        "low",            # Low price
        "close",          # Close price
        "volume",         # Volume (base asset)
        "close_time",     # Close time (ms)
        "quote_volume",   # Volume (quote asset)
        "trades",         # Number of trades
        "taker_buy_base", # Taker buy volume (base)
        "taker_buy_quote" # Taker buy volume (quote)
    ]
    
    # Data types
    DTYPES = {
        "timestamp": "int64",
        "open": "float64",
        "high": "float64",
        "low": "float64",
        "close": "float64",
        "volume": "float64",
        "close_time": "int64",
        "quote_volume": "float64",
        "trades": "int64",
        "taker_buy_base": "float64",
        "taker_buy_quote": "float64",
    }
    
    # Interval to milliseconds mapping
    INTERVAL_MS = {
        "1m": 60 * 1000,
        "3m": 3 * 60 * 1000,
        "5m": 5 * 60 * 1000,
        "15m": 15 * 60 * 1000,
        "30m": 30 * 60 * 1000,
        "1h": 60 * 60 * 1000,
        "2h": 2 * 60 * 60 * 1000,
        "4h": 4 * 60 * 60 * 1000,
        "6h": 6 * 60 * 60 * 1000,
        "8h": 8 * 60 * 60 * 1000,
        "12h": 12 * 60 * 60 * 1000,
        "1d": 24 * 60 * 60 * 1000,
        "3d": 3 * 24 * 60 * 60 * 1000,
        "1w": 7 * 24 * 60 * 60 * 1000,
    }
    
    def __init__(
        self,
        storage_path: Union[str, Path],
        compression: str = "snappy",
    ):
        """
        Initialize candle storage.
        
        Args:
            storage_path: Base directory for data files
            compression: Parquet compression (snappy, gzip, zstd)
        """
        self.storage_path = Path(storage_path)
        self.compression = compression
        
        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"CandleStorage initialized at {self.storage_path}")
    
    def _get_file_path(self, symbol: str, interval: str) -> Path:
        """Get file path for symbol/interval."""
        symbol_dir = self.storage_path / symbol.upper()
        symbol_dir.mkdir(exist_ok=True)
        return symbol_dir / f"{interval}.parquet"
    
    def _validate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and normalize DataFrame schema.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Validated DataFrame with correct schema
            
        Raises:
            ValueError: If required columns are missing
        """
        # Check required columns
        required = ["timestamp", "open", "high", "low", "close", "volume"]
        missing = [col for col in required if col not in df.columns]
        
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Add optional columns with defaults
        for col, dtype in self.DTYPES.items():
            if col not in df.columns:
                df[col] = 0 if dtype == "int64" else 0.0
        
        # Select and order columns
        df = df[self.COLUMNS].copy()
        
        # Apply dtypes
        for col, dtype in self.DTYPES.items():
            df[col] = df[col].astype(dtype)
        
        # Sort by timestamp
        df.sort_values("timestamp", inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        return df
    
    def exists(self, symbol: str, interval: str) -> bool:
        """Check if data exists for symbol/interval."""
        return self._get_file_path(symbol, interval).exists()
    
    def save(
        self,
        df: pd.DataFrame,
        symbol: str,
        interval: str,
        overwrite: bool = False,
    ) -> int:
        """
        Save DataFrame to Parquet file.
        
        Args:
            df: OHLCV DataFrame
            symbol: Trading pair symbol
            interval: Timeframe interval
            overwrite: Overwrite existing file
            
        Returns:
            Number of rows saved
        """
        file_path = self._get_file_path(symbol, interval)
        
        if file_path.exists() and not overwrite:
            logger.warning(f"File exists: {file_path}. Use overwrite=True or append()")
            return 0
        
        # Validate and save
        df = self._validate_dataframe(df)
        
        if df.empty:
            logger.warning(f"Empty DataFrame for {symbol} {interval}")
            return 0
        
        # Write to parquet
        table = pa.Table.from_pandas(df, preserve_index=False)
        pq.write_table(
            table,
            file_path,
            compression=self.compression,
        )
        
        logger.info(f"Saved {len(df)} candles to {file_path}")
        return len(df)
    
    def load(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Load data from Parquet file.
        
        Args:
            symbol: Trading pair symbol
            interval: Timeframe interval
            start_time: Start timestamp filter (ms)
            end_time: End timestamp filter (ms)
            columns: Columns to load (None = all)
            
        Returns:
            DataFrame with OHLCV data
        """
        file_path = self._get_file_path(symbol, interval)
        
        if not file_path.exists():
            logger.warning(f"No data found: {file_path}")
            return pd.DataFrame(columns=self.COLUMNS)
        
        # Build filters
        filters = []
        if start_time is not None:
            filters.append(("timestamp", ">=", start_time))
        if end_time is not None:
            filters.append(("timestamp", "<=", end_time))
        
        # Read parquet
        table = pq.read_table(
            file_path,
            columns=columns,
            filters=filters if filters else None,
        )
        
        df = table.to_pandas()
        
        # Add datetime column for convenience
        if "timestamp" in df.columns:
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        
        logger.debug(f"Loaded {len(df)} candles from {file_path}")
        return df
    
    def append(
        self,
        df: pd.DataFrame,
        symbol: str,
        interval: str,
        deduplicate: bool = True,
    ) -> int:
        """
        Append new data to existing file.
        
        Args:
            df: New OHLCV data
            symbol: Trading pair symbol
            interval: Timeframe interval
            deduplicate: Remove duplicate timestamps
            
        Returns:
            Number of new rows added
        """
        file_path = self._get_file_path(symbol, interval)
        
        # Validate new data
        new_df = self._validate_dataframe(df)
        
        if new_df.empty:
            return 0
        
        # Load existing data if present
        if file_path.exists():
            existing = self.load(symbol, interval)
            
            # Combine
            combined = pd.concat([existing, new_df], ignore_index=True)
            
            # Deduplicate
            if deduplicate:
                combined.drop_duplicates(
                    subset=["timestamp"],
                    keep="last",
                    inplace=True,
                )
            
            # Sort
            combined.sort_values("timestamp", inplace=True)
            combined.reset_index(drop=True, inplace=True)
            
            new_rows = len(combined) - len(existing)
        else:
            combined = new_df
            new_rows = len(new_df)
        
        # Save
        self.save(combined, symbol, interval, overwrite=True)
        
        logger.info(f"Appended {new_rows} new candles for {symbol} {interval}")
        return new_rows
    
    def get_time_range(
        self,
        symbol: str,
        interval: str,
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Get timestamp range for stored data.
        
        Args:
            symbol: Trading pair symbol
            interval: Timeframe interval
            
        Returns:
            (start_timestamp, end_timestamp) or (None, None) if no data
        """
        file_path = self._get_file_path(symbol, interval)
        
        if not file_path.exists():
            return None, None
        
        # Read only timestamp column
        table = pq.read_table(file_path, columns=["timestamp"])
        timestamps = table.column("timestamp").to_pylist()
        
        if not timestamps:
            return None, None
        
        return min(timestamps), max(timestamps)
    
    def find_gaps(
        self,
        symbol: str,
        interval: str,
        tolerance_ms: int = 1000,
    ) -> List[Tuple[int, int]]:
        """
        Find gaps in candlestick data.
        
        Args:
            symbol: Trading pair symbol
            interval: Timeframe interval
            tolerance_ms: Tolerance for gap detection
            
        Returns:
            List of (gap_start, gap_end) timestamps
        """
        df = self.load(symbol, interval, columns=["timestamp"])
        
        if df.empty or len(df) < 2:
            return []
        
        expected_interval = self.INTERVAL_MS.get(interval)
        if expected_interval is None:
            logger.warning(f"Unknown interval: {interval}")
            return []
        
        gaps = []
        timestamps = df["timestamp"].values
        
        for i in range(1, len(timestamps)):
            diff = timestamps[i] - timestamps[i-1]
            expected = expected_interval
            
            if diff > expected + tolerance_ms:
                gaps.append((int(timestamps[i-1]), int(timestamps[i])))
        
        return gaps
    
    def get_stats(self, symbol: str, interval: str) -> Optional[DataStats]:
        """
        Get statistics for stored data.
        
        Args:
            symbol: Trading pair symbol
            interval: Timeframe interval
            
        Returns:
            DataStats object or None if no data
        """
        file_path = self._get_file_path(symbol, interval)
        
        if not file_path.exists():
            return None
        
        # Get row count and time range
        start_ts, end_ts = self.get_time_range(symbol, interval)
        
        # Count rows
        metadata = pq.read_metadata(file_path)
        rows = metadata.num_rows
        
        # File size
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        
        # Check for gaps
        gaps = self.find_gaps(symbol, interval)
        
        # Convert timestamps
        start_dt = datetime.fromtimestamp(start_ts / 1000, tz=timezone.utc) if start_ts else None
        end_dt = datetime.fromtimestamp(end_ts / 1000, tz=timezone.utc) if end_ts else None
        
        return DataStats(
            symbol=symbol,
            interval=interval,
            rows=rows,
            start_time=start_dt,
            end_time=end_dt,
            file_size_mb=file_size_mb,
            has_gaps=len(gaps) > 0,
            gap_count=len(gaps),
        )
    
    def list_symbols(self) -> List[str]:
        """List all stored symbols."""
        symbols = []
        for path in self.storage_path.iterdir():
            if path.is_dir():
                symbols.append(path.name)
        return sorted(symbols)
    
    def list_intervals(self, symbol: str) -> List[str]:
        """List available intervals for a symbol."""
        symbol_dir = self.storage_path / symbol.upper()
        
        if not symbol_dir.exists():
            return []
        
        intervals = []
        for file_path in symbol_dir.glob("*.parquet"):
            intervals.append(file_path.stem)
        
        return sorted(intervals)
    
    def list_all(self) -> Dict[str, List[str]]:
        """
        List all symbols and their intervals.
        
        Returns:
            Dict mapping symbol -> list of intervals
        """
        result = {}
        for symbol in self.list_symbols():
            result[symbol] = self.list_intervals(symbol)
        return result
    
    def delete(self, symbol: str, interval: Optional[str] = None) -> bool:
        """
        Delete stored data.
        
        Args:
            symbol: Trading pair symbol
            interval: Specific interval (None = all intervals)
            
        Returns:
            True if deleted successfully
        """
        if interval:
            # Delete single file
            file_path = self._get_file_path(symbol, interval)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted {file_path}")
                return True
        else:
            # Delete entire symbol directory
            symbol_dir = self.storage_path / symbol.upper()
            if symbol_dir.exists():
                shutil.rmtree(symbol_dir)
                logger.info(f"Deleted {symbol_dir}")
                return True
        
        return False
    
    def get_latest_timestamp(self, symbol: str, interval: str) -> Optional[int]:
        """Get the latest timestamp for incremental updates."""
        _, end_ts = self.get_time_range(symbol, interval)
        return end_ts
    
    def export_csv(
        self,
        symbol: str,
        interval: str,
        output_path: Union[str, Path],
    ) -> bool:
        """
        Export data to CSV file.
        
        Args:
            symbol: Trading pair symbol
            interval: Timeframe interval
            output_path: Output CSV file path
            
        Returns:
            True if exported successfully
        """
        df = self.load(symbol, interval)
        
        if df.empty:
            logger.warning(f"No data to export for {symbol} {interval}")
            return False
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        df.to_csv(output_path, index=False)
        logger.info(f"Exported {len(df)} rows to {output_path}")
        
        return True
    
    def import_csv(
        self,
        input_path: Union[str, Path],
        symbol: str,
        interval: str,
        overwrite: bool = False,
    ) -> int:
        """
        Import data from CSV file.
        
        Args:
            input_path: Input CSV file path
            symbol: Trading pair symbol
            interval: Timeframe interval
            overwrite: Overwrite existing data
            
        Returns:
            Number of rows imported
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"CSV file not found: {input_path}")
        
        df = pd.read_csv(input_path)
        
        return self.save(df, symbol, interval, overwrite=overwrite)


class MultiStorageManager:
    """
    Manager for multiple symbols and timeframes.
    
    Provides batch operations and summary statistics.
    """
    
    def __init__(self, storage: CandleStorage):
        """
        Initialize manager.
        
        Args:
            storage: CandleStorage instance
        """
        self.storage = storage
    
    def get_all_stats(self) -> List[DataStats]:
        """Get statistics for all stored data."""
        stats = []
        
        for symbol, intervals in self.storage.list_all().items():
            for interval in intervals:
                stat = self.storage.get_stats(symbol, interval)
                if stat:
                    stats.append(stat)
        
        return stats
    
    def print_summary(self) -> None:
        """Print summary of all stored data."""
        stats = self.get_all_stats()
        
        if not stats:
            print("No data stored")
            return
        
        print("\n" + "=" * 80)
        print("VELAS Data Storage Summary")
        print("=" * 80)
        print(f"{'Symbol':<12} {'Interval':<8} {'Rows':>10} {'Size (MB)':>10} "
              f"{'Start':>12} {'End':>12} {'Gaps':>6}")
        print("-" * 80)
        
        total_rows = 0
        total_size = 0.0
        
        for s in sorted(stats, key=lambda x: (x.symbol, x.interval)):
            start = s.start_time.strftime("%Y-%m-%d") if s.start_time else "N/A"
            end = s.end_time.strftime("%Y-%m-%d") if s.end_time else "N/A"
            
            print(f"{s.symbol:<12} {s.interval:<8} {s.rows:>10,} {s.file_size_mb:>10.2f} "
                  f"{start:>12} {end:>12} {s.gap_count:>6}")
            
            total_rows += s.rows
            total_size += s.file_size_mb
        
        print("-" * 80)
        print(f"{'Total':<12} {'':<8} {total_rows:>10,} {total_size:>10.2f}")
        print("=" * 80)
    
    def validate_all(self) -> Dict[str, List[Tuple[int, int]]]:
        """
        Validate all stored data and find gaps.
        
        Returns:
            Dict mapping "symbol/interval" -> list of gaps
        """
        all_gaps = {}
        
        for symbol, intervals in self.storage.list_all().items():
            for interval in intervals:
                gaps = self.storage.find_gaps(symbol, interval)
                if gaps:
                    key = f"{symbol}/{interval}"
                    all_gaps[key] = gaps
        
        return all_gaps


# -----------------------------------------------------------------------------
# Example usage
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import tempfile
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    def main():
        """Test storage operations."""
        print("VELAS Data Layer - Storage Test")
        print("=" * 50)
        
        # Create temporary storage
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = CandleStorage(tmpdir)
            
            # Create sample data
            print("\n📝 Creating sample data...")
            
            timestamps = [
                1704067200000 + i * 3600000  # Hourly from 2024-01-01
                for i in range(100)
            ]
            
            df = pd.DataFrame({
                "timestamp": timestamps,
                "open": [100 + i * 0.1 for i in range(100)],
                "high": [101 + i * 0.1 for i in range(100)],
                "low": [99 + i * 0.1 for i in range(100)],
                "close": [100.5 + i * 0.1 for i in range(100)],
                "volume": [1000 + i * 10 for i in range(100)],
            })
            
            # Save data
            print("\n💾 Saving data...")
            rows = storage.save(df, "BTCUSDT", "1h", overwrite=True)
            print(f"Saved {rows} rows")
            
            # Load data
            print("\n📥 Loading data...")
            loaded = storage.load("BTCUSDT", "1h")
            print(f"Loaded {len(loaded)} rows")
            print(f"Columns: {list(loaded.columns)}")
            print(f"\nFirst 3 rows:")
            print(loaded.head(3))
            
            # Append new data
            print("\n➕ Appending new data...")
            new_timestamps = [timestamps[-1] + (i + 1) * 3600000 for i in range(10)]
            new_df = pd.DataFrame({
                "timestamp": new_timestamps,
                "open": [110 + i * 0.1 for i in range(10)],
                "high": [111 + i * 0.1 for i in range(10)],
                "low": [109 + i * 0.1 for i in range(10)],
                "close": [110.5 + i * 0.1 for i in range(10)],
                "volume": [1100 + i * 10 for i in range(10)],
            })
            added = storage.append(new_df, "BTCUSDT", "1h")
            print(f"Added {added} new rows")
            
            # Get statistics
            print("\n📊 Statistics:")
            stats = storage.get_stats("BTCUSDT", "1h")
            if stats:
                print(f"  Rows: {stats.rows}")
                print(f"  Start: {stats.start_time}")
                print(f"  End: {stats.end_time}")
                print(f"  Size: {stats.file_size_mb:.2f} MB")
                print(f"  Gaps: {stats.gap_count}")
            
            # List all
            print("\n📋 All stored data:")
            manager = MultiStorageManager(storage)
            manager.print_summary()
            
            # Test filtered load
            print("\n🔍 Filtered load (first 50 candles):")
            start_ts, end_ts = storage.get_time_range("BTCUSDT", "1h")
            mid_ts = start_ts + (end_ts - start_ts) // 2
            filtered = storage.load("BTCUSDT", "1h", end_time=mid_ts)
            print(f"Loaded {len(filtered)} rows with filter")
            
            print("\n✅ Storage test completed successfully!")
    
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
