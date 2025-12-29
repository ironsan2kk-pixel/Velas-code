"""
VELAS - Скачивание исторических данных с Binance.

Скачивает свечи для всех 20 пар и 3 таймфреймов.
Сохраняет в формате Parquet.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import aiohttp

# Конфигурация
PAIRS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT",
    "LINKUSDT", "UNIUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT",
    "NEARUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "INJUSDT",
]

TIMEFRAMES = {
    "30m": 30,
    "1h": 60,
    "2h": 120,
}

# Binance API
BINANCE_API = "https://api.binance.com/api/v3/klines"
RATE_LIMIT_DELAY = 0.1  # секунды между запросами

# Сколько данных скачивать (в днях)
HISTORY_DAYS = 365  # 1 год


async def fetch_klines(
    session: aiohttp.ClientSession,
    symbol: str,
    interval: str,
    start_time: int,
    end_time: int,
    limit: int = 1000,
) -> List[list]:
    """Получить свечи с Binance API."""
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": limit,
    }
    
    try:
        async with session.get(BINANCE_API, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"  ⚠️ Ошибка {response.status} для {symbol} {interval}")
                return []
    except Exception as e:
        print(f"  ⚠️ Исключение для {symbol} {interval}: {e}")
        return []


async def download_pair_timeframe(
    session: aiohttp.ClientSession,
    symbol: str,
    timeframe: str,
    output_dir: Path,
) -> Optional[str]:
    """Скачать данные для одной пары и таймфрейма."""
    
    # Временной диапазон
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=HISTORY_DAYS)
    
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)
    
    all_klines = []
    current_start = start_ms
    
    # Binance возвращает максимум 1000 свечей за запрос
    interval_minutes = TIMEFRAMES[timeframe]
    max_candles_per_request = 1000
    interval_ms = interval_minutes * 60 * 1000
    
    while current_start < end_ms:
        chunk_end = min(current_start + (max_candles_per_request * interval_ms), end_ms)
        
        klines = await fetch_klines(
            session, symbol, timeframe, current_start, chunk_end
        )
        
        if not klines:
            break
            
        all_klines.extend(klines)
        current_start = klines[-1][0] + interval_ms
        
        await asyncio.sleep(RATE_LIMIT_DELAY)
    
    if not all_klines:
        return None
    
    # Преобразование в DataFrame
    df = pd.DataFrame(all_klines, columns=[
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades", "taker_buy_base",
        "taker_buy_quote", "ignore"
    ])
    
    # Типы данных
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    
    for col in ["open", "high", "low", "close", "volume", "quote_volume"]:
        df[col] = df[col].astype(float)
    
    df["trades"] = df["trades"].astype(int)
    
    # Удаление дубликатов
    df = df.drop_duplicates(subset=["open_time"])
    df = df.sort_values("open_time")
    df = df.reset_index(drop=True)
    
    # Выбор нужных колонок
    df = df[["open_time", "open", "high", "low", "close", "volume", "trades"]]
    df.columns = ["timestamp", "open", "high", "low", "close", "volume", "trades"]
    
    # Сохранение в Parquet
    output_file = output_dir / f"{symbol}_{timeframe}.parquet"
    df.to_parquet(output_file, engine="pyarrow", index=False)
    
    return f"{len(df)} свечей"


async def main():
    """Главная функция."""
    print()
    print("═" * 60)
    print("  VELAS - Скачивание исторических данных")
    print("═" * 60)
    print()
    print(f"  Пар: {len(PAIRS)}")
    print(f"  Таймфреймов: {len(TIMEFRAMES)}")
    print(f"  История: {HISTORY_DAYS} дней")
    print(f"  Всего файлов: {len(PAIRS) * len(TIMEFRAMES)}")
    print()
    print("─" * 60)
    
    # Создание директории
    output_dir = ROOT / "data" / "candles"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Счётчики
    total = len(PAIRS) * len(TIMEFRAMES)
    completed = 0
    failed = 0
    
    async with aiohttp.ClientSession() as session:
        for symbol in PAIRS:
            for timeframe in TIMEFRAMES.keys():
                completed += 1
                print(f"  [{completed:3}/{total}] {symbol} {timeframe}...", end=" ", flush=True)
                
                result = await download_pair_timeframe(
                    session, symbol, timeframe, output_dir
                )
                
                if result:
                    print(f"✅ {result}")
                else:
                    print("❌ Ошибка")
                    failed += 1
    
    print()
    print("─" * 60)
    print()
    print(f"  ✅ Успешно: {completed - failed}")
    print(f"  ❌ Ошибок: {failed}")
    print(f"  📁 Сохранено в: {output_dir}")
    print()
    
    # Статистика по файлам
    files = list(output_dir.glob("*.parquet"))
    total_size = sum(f.stat().st_size for f in files)
    print(f"  📊 Всего файлов: {len(files)}")
    print(f"  💾 Общий размер: {total_size / 1024 / 1024:.1f} MB")
    print()
    print("═" * 60)
    print("  СКАЧИВАНИЕ ЗАВЕРШЕНО")
    print("═" * 60)
    print()


if __name__ == "__main__":
    asyncio.run(main())
