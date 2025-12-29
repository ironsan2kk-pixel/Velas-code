#!/usr/bin/env python3
"""
VELAS Trading System - Historical Data Download Script

Downloads historical candlestick data for all configured pairs and timeframes.
Supports incremental updates and parallel downloads.

Usage:
    python download_history.py                    # Download all
    python download_history.py --symbol BTCUSDT   # Single symbol
    python download_history.py --months 6         # 6 months history
    python download_history.py --update           # Incremental update
"""

import argparse
import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.data.binance_rest import BinanceRestClient, MarketType
from backend.data.storage import CandleStorage, MultiStorageManager

# Default configuration
DEFAULT_CONFIG = {
    "storage_path": "./data/candles",
    "history_months": 12,
    "parallel_downloads": 3,
    "pairs": [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
        "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT",
        "LINKUSDT", "UNIUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT",
        "NEARUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "INJUSDT",
    ],
    "timeframes": ["30m", "1h", "2h"],
}

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_path: Optional[str] = None) -> dict:
    """Load configuration from file or use defaults."""
    if config_path and Path(config_path).exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
            return {**DEFAULT_CONFIG, **config}
    
    # Try default locations
    for path in ["config/config.yaml", "config.yaml", "../config/config.yaml"]:
        if Path(path).exists():
            with open(path) as f:
                config = yaml.safe_load(f)
                return {**DEFAULT_CONFIG, **config}
    
    return DEFAULT_CONFIG


def load_pairs(pairs_path: Optional[str] = None) -> List[str]:
    """Load pairs list from configuration."""
    for path in [pairs_path, "config/pairs.yaml", "pairs.yaml", "../config/pairs.yaml"]:
        if path and Path(path).exists():
            with open(path) as f:
                data = yaml.safe_load(f)
                if "pairs" in data:
                    return [p["symbol"] for p in data["pairs"] if p.get("enabled", True)]
    
    return DEFAULT_CONFIG["pairs"]


class DownloadProgress:
    """Track download progress."""
    
    def __init__(self, total_tasks: int):
        self.total_tasks = total_tasks
        self.completed = 0
        self.failed = 0
        self.skipped = 0
        self.total_candles = 0
        self.start_time = time.time()
    
    def complete(self, candles: int = 0):
        """Mark task as complete."""
        self.completed += 1
        self.total_candles += candles
        self._print_progress()
    
    def fail(self):
        """Mark task as failed."""
        self.failed += 1
        self._print_progress()
    
    def skip(self):
        """Mark task as skipped."""
        self.skipped += 1
        self._print_progress()
    
    def _print_progress(self):
        """Print progress bar."""
        done = self.completed + self.failed + self.skipped
        pct = done * 100 // self.total_tasks
        elapsed = time.time() - self.start_time
        
        # Estimate remaining time
        if done > 0:
            eta = elapsed * (self.total_tasks - done) / done
            eta_str = f"{eta:.0f}s"
        else:
            eta_str = "?"
        
        bar_width = 30
        filled = int(bar_width * done / self.total_tasks)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        status = f"✓{self.completed} ✗{self.failed} ⊘{self.skipped}"
        
        print(f"\r[{bar}] {pct}% ({done}/{self.total_tasks}) {status} ETA: {eta_str}  ", 
              end="", flush=True)
    
    def summary(self) -> str:
        """Get final summary."""
        elapsed = time.time() - self.start_time
        return (
            f"\n{'='*60}\n"
            f"Download Complete\n"
            f"{'='*60}\n"
            f"  Completed: {self.completed}\n"
            f"  Failed:    {self.failed}\n"
            f"  Skipped:   {self.skipped}\n"
            f"  Candles:   {self.total_candles:,}\n"
            f"  Time:      {elapsed:.1f}s\n"
            f"{'='*60}"
        )


async def download_symbol_interval(
    client: BinanceRestClient,
    storage: CandleStorage,
    symbol: str,
    interval: str,
    months: int,
    update_only: bool = False,
    progress: Optional[DownloadProgress] = None,
) -> Tuple[bool, int]:
    """
    Download data for a single symbol/interval.
    
    Args:
        client: Binance REST client
        storage: Data storage
        symbol: Trading pair
        interval: Timeframe
        months: Months of history
        update_only: Only download new data
        progress: Progress tracker
        
    Returns:
        (success, candle_count)
    """
    try:
        # Calculate time range
        now = datetime.now(timezone.utc)
        
        if update_only and storage.exists(symbol, interval):
            # Get latest stored timestamp
            latest_ts = storage.get_latest_timestamp(symbol, interval)
            if latest_ts:
                # Start from last candle + interval
                interval_ms = storage.INTERVAL_MS.get(interval, 3600000)
                start_ms = latest_ts + interval_ms
                
                # Skip if already up to date
                if start_ms >= int(now.timestamp() * 1000) - interval_ms:
                    logger.debug(f"{symbol} {interval}: Already up to date")
                    if progress:
                        progress.skip()
                    return True, 0
            else:
                # Calculate start from months
                start_dt = now - pd.DateOffset(months=months)
                start_ms = int(start_dt.timestamp() * 1000)
        else:
            # Full download from start
            import pandas as pd
            start_dt = now - pd.DateOffset(months=months)
            start_ms = int(start_dt.timestamp() * 1000)
        
        logger.info(f"Downloading {symbol} {interval}...")
        
        # Download klines
        klines = await client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_time=start_ms,
        )
        
        if not klines:
            logger.warning(f"No data received for {symbol} {interval}")
            if progress:
                progress.fail()
            return False, 0
        
        # Convert to DataFrame
        df = client.klines_to_dataframe(klines)
        
        # Save or append
        if update_only and storage.exists(symbol, interval):
            added = storage.append(df, symbol, interval)
        else:
            added = storage.save(df, symbol, interval, overwrite=True)
        
        logger.info(f"✓ {symbol} {interval}: {added} candles")
        
        if progress:
            progress.complete(added)
        
        return True, added
        
    except Exception as e:
        logger.error(f"✗ {symbol} {interval}: {e}")
        if progress:
            progress.fail()
        return False, 0


async def download_all(
    symbols: List[str],
    intervals: List[str],
    storage_path: str,
    months: int = 12,
    parallel: int = 3,
    update_only: bool = False,
    market_type: MarketType = MarketType.SPOT,
) -> bool:
    """
    Download data for all symbols and intervals.
    
    Args:
        symbols: List of trading pairs
        intervals: List of timeframes
        storage_path: Path to data storage
        months: Months of history
        parallel: Number of parallel downloads
        update_only: Only download new data
        market_type: SPOT or FUTURES
        
    Returns:
        True if all downloads succeeded
    """
    # Initialize storage
    storage = CandleStorage(storage_path)
    
    # Build task list
    tasks = []
    for symbol in symbols:
        for interval in intervals:
            tasks.append((symbol, interval))
    
    total = len(tasks)
    progress = DownloadProgress(total)
    
    print(f"\n{'='*60}")
    print(f"VELAS Data Download")
    print(f"{'='*60}")
    print(f"  Symbols:    {len(symbols)}")
    print(f"  Intervals:  {intervals}")
    print(f"  Total:      {total} downloads")
    print(f"  Months:     {months}")
    print(f"  Parallel:   {parallel}")
    print(f"  Mode:       {'Update' if update_only else 'Full'}")
    print(f"  Storage:    {storage_path}")
    print(f"{'='*60}\n")
    
    # Create semaphore for parallel control
    semaphore = asyncio.Semaphore(parallel)
    
    async def download_with_semaphore(client, symbol, interval):
        async with semaphore:
            return await download_symbol_interval(
                client, storage, symbol, interval,
                months, update_only, progress
            )
    
    # Download with shared client
    async with BinanceRestClient(market_type=market_type) as client:
        # Create coroutines
        coros = [
            download_with_semaphore(client, symbol, interval)
            for symbol, interval in tasks
        ]
        
        # Run all
        results = await asyncio.gather(*coros, return_exceptions=True)
    
    # Print summary
    print(progress.summary())
    
    # Show storage summary
    manager = MultiStorageManager(storage)
    manager.print_summary()
    
    # Check for failures
    success = progress.failed == 0
    
    if not success:
        logger.warning(f"{progress.failed} downloads failed")
    
    return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download historical candlestick data for VELAS"
    )
    
    parser.add_argument(
        "-s", "--symbol",
        help="Download single symbol only"
    )
    parser.add_argument(
        "-i", "--interval",
        help="Download single interval only"
    )
    parser.add_argument(
        "-m", "--months",
        type=int,
        default=12,
        help="Months of history to download (default: 12)"
    )
    parser.add_argument(
        "-p", "--parallel",
        type=int,
        default=3,
        help="Number of parallel downloads (default: 3)"
    )
    parser.add_argument(
        "-u", "--update",
        action="store_true",
        help="Incremental update (download new data only)"
    )
    parser.add_argument(
        "-o", "--output",
        default="./data/candles",
        help="Storage path (default: ./data/candles)"
    )
    parser.add_argument(
        "-c", "--config",
        help="Path to config file"
    )
    parser.add_argument(
        "--futures",
        action="store_true",
        help="Use Futures API"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load config
    config = load_config(args.config)
    
    # Determine symbols
    if args.symbol:
        symbols = [args.symbol.upper()]
    else:
        symbols = load_pairs()
    
    # Determine intervals
    if args.interval:
        intervals = [args.interval]
    else:
        intervals = config.get("timeframes", DEFAULT_CONFIG["timeframes"])
    
    # Storage path
    storage_path = args.output or config.get("storage_path", DEFAULT_CONFIG["storage_path"])
    
    # Months
    months = args.months or config.get("history_months", DEFAULT_CONFIG["history_months"])
    
    # Parallel
    parallel = args.parallel or config.get("parallel_downloads", DEFAULT_CONFIG["parallel_downloads"])
    
    # Market type
    market_type = MarketType.FUTURES if args.futures else MarketType.SPOT
    
    # Import pandas here to support --help without pandas
    import pandas as pd
    
    # Run download
    try:
        success = asyncio.run(download_all(
            symbols=symbols,
            intervals=intervals,
            storage_path=storage_path,
            months=months,
            parallel=parallel,
            update_only=args.update,
            market_type=market_type,
        ))
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
