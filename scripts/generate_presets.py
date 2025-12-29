#!/usr/bin/env python
"""
VELAS Preset Generator Script

Генерирует все 180 пресетов (20 пар × 3 TF × 3 режима волатильности)
и сохраняет их в YAML файлы.

Использование:
    python scripts/generate_presets.py
    python scripts/generate_presets.py --output C:/velas/data/presets
    python scripts/generate_presets.py --symbol BTCUSDT --only

Опции:
    --output    Директория для сохранения (default: data/presets)
    --symbol    Генерировать только для одного символа
    --only      Не перезаписывать существующие файлы
    --dry-run   Показать что будет создано, но не создавать
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

# Добавляем backend в путь
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.presets import (
    PresetGenerator,
    PresetManager,
    TRADING_PAIRS,
    TIMEFRAMES,
    VOLATILITY_REGIMES,
    get_preset_count,
)


def print_banner():
    """Вывод баннера."""
    print("=" * 60)
    print("  VELAS Preset Generator")
    print("=" * 60)
    print(f"  Пары: {len(TRADING_PAIRS)}")
    print(f"  Таймфреймы: {', '.join(TIMEFRAMES)}")
    print(f"  Режимы: {', '.join(VOLATILITY_REGIMES)}")
    print(f"  Всего пресетов: {get_preset_count()}")
    print("=" * 60)
    print()


def generate_all_presets(output_dir: str, dry_run: bool = False, skip_existing: bool = False):
    """
    Генерация всех пресетов.
    
    Args:
        output_dir: Директория для сохранения
        dry_run: Только показать, не создавать
        skip_existing: Пропускать существующие файлы
    """
    output_path = Path(output_dir)
    
    if dry_run:
        print(f"[DRY RUN] Будет создано {get_preset_count()} пресетов в {output_path}")
        print()
        
        for symbol in TRADING_PAIRS:
            for tf in TIMEFRAMES:
                for regime in VOLATILITY_REGIMES:
                    print(f"  - {symbol}_{tf}_{regime}.yaml")
        
        print(f"\nВсего файлов: {get_preset_count()}")
        return
    
    # Создаём директорию
    output_path.mkdir(parents=True, exist_ok=True)
    
    generator = PresetGenerator(str(output_path))
    manager = generator.manager
    
    created = 0
    skipped = 0
    
    for symbol in TRADING_PAIRS:
        print(f"\n🔄 {symbol}")
        
        for tf in TIMEFRAMES:
            for regime in VOLATILITY_REGIMES:
                preset_id = f"{symbol}_{tf}_{regime}"
                filepath = output_path / f"{preset_id}.yaml"
                
                if skip_existing and filepath.exists():
                    print(f"  ⏭ {preset_id} (существует)")
                    skipped += 1
                    continue
                
                preset = generator.generate_preset(symbol, tf, regime)
                manager.save(preset)
                print(f"  ✅ {preset_id}")
                created += 1
    
    print("\n" + "=" * 60)
    print(f"✅ Создано: {created}")
    print(f"⏭ Пропущено: {skipped}")
    print(f"📁 Директория: {output_path}")
    print("=" * 60)


def generate_for_symbol(symbol: str, output_dir: str, dry_run: bool = False):
    """
    Генерация пресетов для одного символа.
    
    Args:
        symbol: Торговая пара
        output_dir: Директория для сохранения
        dry_run: Только показать, не создавать
    """
    if symbol not in TRADING_PAIRS:
        print(f"❌ Неизвестный символ: {symbol}")
        print(f"   Доступные: {', '.join(TRADING_PAIRS)}")
        sys.exit(1)
    
    output_path = Path(output_dir)
    
    if dry_run:
        print(f"[DRY RUN] Будет создано 9 пресетов для {symbol}")
        for tf in TIMEFRAMES:
            for regime in VOLATILITY_REGIMES:
                print(f"  - {symbol}_{tf}_{regime}.yaml")
        return
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    generator = PresetGenerator(str(output_path))
    presets = generator.generate_for_symbol(symbol)
    
    for preset in presets:
        generator.manager.save(preset)
        print(f"✅ {preset.preset_id}")
    
    print(f"\n📁 Создано {len(presets)} пресетов в {output_path}")


def show_summary(presets_dir: str):
    """
    Показать сводку по существующим пресетам.
    
    Args:
        presets_dir: Директория с пресетами
    """
    manager = PresetManager(presets_dir)
    presets = manager.load_all()
    
    print(f"\n📊 Сводка по пресетам в {presets_dir}")
    print("=" * 60)
    
    if not presets:
        print("❌ Пресеты не найдены")
        return
    
    print(f"Всего пресетов: {len(presets)}")
    print(f"Активных: {len([p for p in presets if p.is_active])}")
    
    # По символам
    print("\n📈 По символам:")
    symbols = {}
    for p in presets:
        symbols[p.symbol] = symbols.get(p.symbol, 0) + 1
    for symbol, count in sorted(symbols.items()):
        print(f"  {symbol}: {count}")
    
    # По таймфреймам
    print("\n⏱ По таймфреймам:")
    for tf in TIMEFRAMES:
        count = len([p for p in presets if p.timeframe == tf])
        print(f"  {tf}: {count}")
    
    # По режимам
    print("\n🌡 По режимам волатильности:")
    for regime in VOLATILITY_REGIMES:
        count = len([p for p in presets if p.volatility_regime == regime])
        print(f"  {regime}: {count}")
    
    # По секторам
    print("\n🏷 По секторам:")
    sectors = {}
    for p in presets:
        sectors[p.sector] = sectors.get(p.sector, 0) + 1
    for sector, count in sorted(sectors.items()):
        print(f"  {sector}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="VELAS Preset Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python generate_presets.py                    # Создать все 180 пресетов
  python generate_presets.py --symbol BTCUSDT   # Только для BTCUSDT
  python generate_presets.py --dry-run          # Показать без создания
  python generate_presets.py --summary          # Сводка по существующим
        """
    )
    
    parser.add_argument(
        "--output", "-o",
        default="data/presets",
        help="Директория для сохранения пресетов (default: data/presets)"
    )
    
    parser.add_argument(
        "--symbol", "-s",
        help="Генерировать только для одного символа"
    )
    
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Не перезаписывать существующие файлы"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Показать что будет создано, но не создавать"
    )
    
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Показать сводку по существующим пресетам"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Определяем абсолютный путь
    output_dir = args.output
    if not os.path.isabs(output_dir):
        output_dir = str(PROJECT_ROOT / output_dir)
    
    if args.summary:
        show_summary(output_dir)
        return
    
    if args.symbol:
        generate_for_symbol(args.symbol, output_dir, args.dry_run)
    else:
        generate_all_presets(output_dir, args.dry_run, args.skip_existing)


if __name__ == "__main__":
    main()
