"""
VELAS Presets Manager - управление и генерация пресетов.

Пресеты:
- 20 пар × 3 таймфрейма × 3 режима волатильности = 180 пресетов
- Каждый пресет содержит: параметры индикатора (i1-i5), TP/SL уровни, метаданные
- Хранятся в YAML файлах в data/presets/

Использование:
    manager = PresetManager("C:/velas/data/presets")
    
    # Загрузка пресета
    preset = manager.load("BTCUSDT_1h_normal")
    
    # Получить пресет для текущего режима
    preset = manager.get_adaptive("BTCUSDT", "1h", df)
    
    # Генерация всех пресетов
    generator = PresetGenerator(output_dir)
    generator.generate_all()
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import os
import logging
import yaml
import json

from .volatility import VolatilityRegime, VolatilityAnalyzer, VolatilityConfig


logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS
# ============================================================================

# 20 торговых пар
TRADING_PAIRS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT",
    "LINKUSDT", "UNIUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT",
    "NEARUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "INJUSDT",
]

# 3 таймфрейма
TIMEFRAMES = ["30m", "1h", "2h"]

# 3 режима волатильности
VOLATILITY_REGIMES = ["low", "normal", "high"]

# Секторы для диверсификации
SECTORS = {
    "BTC": ["BTCUSDT"],
    "ETH": ["ETHUSDT"],
    "L1": ["SOLUSDT", "AVAXUSDT", "ATOMUSDT", "NEARUSDT", "APTUSDT"],
    "L2": ["MATICUSDT", "ARBUSDT", "OPUSDT"],
    "DEFI": ["LINKUSDT", "UNIUSDT", "INJUSDT"],
    "OLD": ["XRPUSDT", "ADAUSDT", "DOTUSDT", "LTCUSDT", "ETCUSDT"],
    "MEME": ["DOGEUSDT"],
    "CEX": ["BNBUSDT"],
}


def get_sector(symbol: str) -> str:
    """Получить сектор для символа."""
    for sector, symbols in SECTORS.items():
        if symbol in symbols:
            return sector
    return "UNKNOWN"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class IndicatorParams:
    """Параметры индикатора Velas (i1-i5)."""
    
    i1: int     # Период канала (highest/lowest)
    i2: int     # Период StdDev
    i3: float   # Множитель StdDev
    i4: float   # Множитель ATR
    i5: float   # Процент смещения от середины
    
    def to_dict(self) -> dict:
        return {"i1": self.i1, "i2": self.i2, "i3": self.i3, "i4": self.i4, "i5": self.i5}
    
    @classmethod
    def from_dict(cls, d: dict) -> 'IndicatorParams':
        return cls(i1=d["i1"], i2=d["i2"], i3=d["i3"], i4=d["i4"], i5=d["i5"])


@dataclass
class TPLevels:
    """Уровни Take Profit (проценты от входа)."""
    
    tp1: float = 1.0
    tp2: float = 2.0
    tp3: float = 3.0
    tp4: float = 4.0
    tp5: float = 7.5
    tp6: float = 14.0
    
    def to_list(self) -> List[float]:
        return [self.tp1, self.tp2, self.tp3, self.tp4, self.tp5, self.tp6]
    
    def to_dict(self) -> dict:
        return {"tp1": self.tp1, "tp2": self.tp2, "tp3": self.tp3, 
                "tp4": self.tp4, "tp5": self.tp5, "tp6": self.tp6}
    
    @classmethod
    def from_dict(cls, d: dict) -> 'TPLevels':
        return cls(**d)
    
    def apply_multiplier(self, mult: float) -> 'TPLevels':
        """Применить множитель ко всем уровням."""
        return TPLevels(
            tp1=round(self.tp1 * mult, 2),
            tp2=round(self.tp2 * mult, 2),
            tp3=round(self.tp3 * mult, 2),
            tp4=round(self.tp4 * mult, 2),
            tp5=round(self.tp5 * mult, 2),
            tp6=round(self.tp6 * mult, 2),
        )


@dataclass
class TPDistribution:
    """Распределение позиции по TP (проценты, сумма = 100)."""
    
    tp1: float = 20.0
    tp2: float = 20.0
    tp3: float = 15.0
    tp4: float = 15.0
    tp5: float = 15.0
    tp6: float = 15.0
    
    def to_list(self) -> List[float]:
        return [self.tp1, self.tp2, self.tp3, self.tp4, self.tp5, self.tp6]
    
    def to_dict(self) -> dict:
        return {"tp1": self.tp1, "tp2": self.tp2, "tp3": self.tp3,
                "tp4": self.tp4, "tp5": self.tp5, "tp6": self.tp6}
    
    @classmethod
    def from_dict(cls, d: dict) -> 'TPDistribution':
        return cls(**d)
    
    def __post_init__(self):
        """Нормализовать до 100%."""
        total = sum(self.to_list())
        if total > 0 and abs(total - 100) > 0.01:
            factor = 100 / total
            self.tp1 *= factor
            self.tp2 *= factor
            self.tp3 *= factor
            self.tp4 *= factor
            self.tp5 *= factor
            self.tp6 *= factor


@dataclass
class OptimizationMeta:
    """Метаданные оптимизации пресета."""
    
    train_start: str = ""           # "2024-01-01"
    train_end: str = ""             # "2024-06-30"
    test_start: str = ""            # "2024-07-01"
    test_end: str = ""              # "2024-08-31"
    
    test_sharpe: float = 0.0
    test_winrate_tp1: float = 0.0
    test_profit_factor: float = 0.0
    test_max_drawdown: float = 0.0
    test_total_trades: int = 0
    
    robustness_score: float = 0.0
    walk_forward_efficiency: float = 0.0
    
    generated_at: str = ""          # ISO timestamp
    version: str = "1.0"
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d: dict) -> 'OptimizationMeta':
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class TradingPreset:
    """
    Полный пресет для торговли.
    
    Содержит все параметры для одной комбинации:
    symbol + timeframe + volatility_regime
    """
    
    # Идентификация
    symbol: str                     # "BTCUSDT"
    timeframe: str                  # "1h"
    volatility_regime: str          # "low", "normal", "high"
    
    # Параметры индикатора
    indicator: IndicatorParams = None
    
    # TP/SL
    tp_levels: TPLevels = None
    sl_percent: float = 8.5
    tp_distribution: TPDistribution = None
    
    # Метаданные
    sector: str = ""
    optimization: OptimizationMeta = None
    
    # Статус
    is_active: bool = True
    notes: str = ""
    
    @property
    def preset_id(self) -> str:
        """Уникальный ID пресета."""
        return f"{self.symbol}_{self.timeframe}_{self.volatility_regime}"
    
    @property
    def filename(self) -> str:
        """Имя файла для пресета."""
        return f"{self.preset_id}.yaml"
    
    def __post_init__(self):
        if self.indicator is None:
            # Дефолтные параметры (первый пресет из 60)
            self.indicator = IndicatorParams(i1=40, i2=10, i3=0.3, i4=1.0, i5=1.0)
        if self.tp_levels is None:
            self.tp_levels = TPLevels()
        if self.tp_distribution is None:
            self.tp_distribution = TPDistribution()
        if self.optimization is None:
            self.optimization = OptimizationMeta()
        if not self.sector:
            self.sector = get_sector(self.symbol)
    
    def to_dict(self) -> dict:
        """Конвертация в словарь для YAML."""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "volatility_regime": self.volatility_regime,
            "sector": self.sector,
            "indicator": self.indicator.to_dict(),
            "tp_levels": self.tp_levels.to_dict(),
            "sl_percent": self.sl_percent,
            "tp_distribution": self.tp_distribution.to_dict(),
            "optimization": self.optimization.to_dict(),
            "is_active": self.is_active,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, d: dict) -> 'TradingPreset':
        """Создание из словаря (загрузка из YAML)."""
        return cls(
            symbol=d["symbol"],
            timeframe=d["timeframe"],
            volatility_regime=d["volatility_regime"],
            sector=d.get("sector", ""),
            indicator=IndicatorParams.from_dict(d["indicator"]),
            tp_levels=TPLevels.from_dict(d["tp_levels"]),
            sl_percent=d["sl_percent"],
            tp_distribution=TPDistribution.from_dict(d["tp_distribution"]),
            optimization=OptimizationMeta.from_dict(d.get("optimization", {})),
            is_active=d.get("is_active", True),
            notes=d.get("notes", ""),
        )
    
    def to_yaml(self) -> str:
        """Конвертация в YAML строку."""
        return yaml.dump(self.to_dict(), allow_unicode=True, sort_keys=False, default_flow_style=False)


# ============================================================================
# PRESET MANAGER
# ============================================================================

class PresetManager:
    """
    Менеджер пресетов - загрузка, сохранение, поиск.
    """
    
    def __init__(self, presets_dir: str):
        """
        Args:
            presets_dir: Путь к директории с пресетами
        """
        self.presets_dir = Path(presets_dir)
        self._cache: Dict[str, TradingPreset] = {}
        self._volatility_analyzer: Optional[VolatilityAnalyzer] = None
        
        logger.info(f"PresetManager initialized: {presets_dir}")
    
    def _ensure_dir(self):
        """Создать директорию если не существует."""
        self.presets_dir.mkdir(parents=True, exist_ok=True)
    
    def load(self, preset_id: str) -> Optional[TradingPreset]:
        """
        Загрузить пресет по ID.
        
        Args:
            preset_id: ID пресета (например "BTCUSDT_1h_normal")
            
        Returns:
            TradingPreset или None
        """
        # Проверяем кеш
        if preset_id in self._cache:
            return self._cache[preset_id]
        
        # Загружаем из файла
        filepath = self.presets_dir / f"{preset_id}.yaml"
        if not filepath.exists():
            logger.warning(f"Preset not found: {filepath}")
            return None
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            preset = TradingPreset.from_dict(data)
            self._cache[preset_id] = preset
            return preset
            
        except Exception as e:
            logger.error(f"Error loading preset {preset_id}: {e}")
            return None
    
    def save(self, preset: TradingPreset):
        """
        Сохранить пресет в файл.
        
        Args:
            preset: Пресет для сохранения
        """
        self._ensure_dir()
        
        filepath = self.presets_dir / preset.filename
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(preset.to_yaml())
            
            self._cache[preset.preset_id] = preset
            logger.info(f"Saved preset: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving preset {preset.preset_id}: {e}")
            raise
    
    def get(
        self,
        symbol: str,
        timeframe: str,
        regime: str = "normal",
    ) -> Optional[TradingPreset]:
        """
        Получить пресет для пары/таймфрейма/режима.
        
        Args:
            symbol: Торговая пара
            timeframe: Таймфрейм
            regime: Режим волатильности
            
        Returns:
            TradingPreset или None
        """
        preset_id = f"{symbol}_{timeframe}_{regime}"
        return self.load(preset_id)
    
    def get_adaptive(
        self,
        symbol: str,
        timeframe: str,
        df: Any,  # pd.DataFrame
    ) -> Optional[TradingPreset]:
        """
        Получить пресет с автоматическим определением режима волатильности.
        
        Args:
            symbol: Торговая пара
            timeframe: Таймфрейм
            df: DataFrame с OHLCV данными
            
        Returns:
            TradingPreset для текущего режима волатильности
        """
        # Определяем режим волатильности
        if self._volatility_analyzer is None:
            self._volatility_analyzer = VolatilityAnalyzer()
        
        self._volatility_analyzer.set_data(df)
        regime = self._volatility_analyzer.get_regime()
        
        return self.get(symbol, timeframe, regime.value)
    
    def list_all(self) -> List[str]:
        """Список всех доступных пресетов."""
        if not self.presets_dir.exists():
            return []
        
        return [f.stem for f in self.presets_dir.glob("*.yaml")]
    
    def load_all(self) -> List[TradingPreset]:
        """Загрузить все пресеты."""
        presets = []
        for preset_id in self.list_all():
            preset = self.load(preset_id)
            if preset:
                presets.append(preset)
        return presets
    
    def get_by_symbol(self, symbol: str) -> List[TradingPreset]:
        """Получить все пресеты для символа."""
        return [p for p in self.load_all() if p.symbol == symbol]
    
    def get_by_timeframe(self, timeframe: str) -> List[TradingPreset]:
        """Получить все пресеты для таймфрейма."""
        return [p for p in self.load_all() if p.timeframe == timeframe]
    
    def get_active(self) -> List[TradingPreset]:
        """Получить только активные пресеты."""
        return [p for p in self.load_all() if p.is_active]
    
    def clear_cache(self):
        """Очистить кеш пресетов."""
        self._cache.clear()


# ============================================================================
# PRESET GENERATOR
# ============================================================================

# Дефолтные TP уровни для разных режимов волатильности
DEFAULT_TP_LEVELS = {
    "low": TPLevels(tp1=0.8, tp2=1.6, tp3=2.4, tp4=3.2, tp5=6.0, tp6=11.2),
    "normal": TPLevels(tp1=1.0, tp2=2.0, tp3=3.0, tp4=4.0, tp5=7.5, tp6=14.0),
    "high": TPLevels(tp1=1.3, tp2=2.6, tp3=3.9, tp4=5.2, tp5=9.75, tp6=18.2),
}

DEFAULT_SL_PERCENT = {
    "low": 6.8,    # 8.5 * 0.8
    "normal": 8.5,
    "high": 10.2,  # 8.5 * 1.2
}

# Дефолтные параметры индикатора для разных типов пар
DEFAULT_INDICATOR_PARAMS = {
    # BTC/ETH - большие, медленные
    "BTC": IndicatorParams(i1=60, i2=14, i3=0.8, i4=1.4, i5=1.4),
    "ETH": IndicatorParams(i1=55, i2=14, i3=0.9, i4=1.5, i5=1.5),
    
    # L1 - средняя волатильность
    "L1": IndicatorParams(i1=50, i2=12, i3=1.1, i4=1.6, i5=1.6),
    
    # L2 - быстрее, волатильнее
    "L2": IndicatorParams(i1=45, i2=11, i3=1.3, i4=1.7, i5=1.7),
    
    # DEFI - высокая волатильность
    "DEFI": IndicatorParams(i1=40, i2=10, i3=1.5, i4=1.8, i5=1.8),
    
    # OLD - стабильные монеты
    "OLD": IndicatorParams(i1=65, i2=14, i3=0.7, i4=1.3, i5=1.3),
    
    # MEME - очень волатильные
    "MEME": IndicatorParams(i1=35, i2=10, i3=1.8, i4=2.0, i5=2.0),
    
    # CEX - средне
    "CEX": IndicatorParams(i1=55, i2=13, i3=1.0, i4=1.5, i5=1.5),
}


class PresetGenerator:
    """
    Генератор пресетов для всех комбинаций пар/таймфреймов/режимов.
    
    Создаёт 180 пресетов (20 × 3 × 3) с дефолтными параметрами.
    После генерации пресеты можно оптимизировать через Walk-Forward Analysis.
    """
    
    def __init__(self, output_dir: str):
        """
        Args:
            output_dir: Директория для сохранения пресетов
        """
        self.output_dir = Path(output_dir)
        self.manager = PresetManager(output_dir)
    
    def generate_preset(
        self,
        symbol: str,
        timeframe: str,
        regime: str,
        indicator_params: IndicatorParams = None,
        tp_levels: TPLevels = None,
        sl_percent: float = None,
    ) -> TradingPreset:
        """
        Сгенерировать один пресет.
        
        Args:
            symbol: Торговая пара
            timeframe: Таймфрейм
            regime: Режим волатильности
            indicator_params: Параметры индикатора (опционально)
            tp_levels: Уровни TP (опционально)
            sl_percent: Уровень SL (опционально)
            
        Returns:
            TradingPreset
        """
        sector = get_sector(symbol)
        
        # Параметры индикатора
        if indicator_params is None:
            indicator_params = DEFAULT_INDICATOR_PARAMS.get(
                sector, 
                DEFAULT_INDICATOR_PARAMS["L1"]
            )
        
        # TP уровни для режима
        if tp_levels is None:
            tp_levels = DEFAULT_TP_LEVELS.get(regime, DEFAULT_TP_LEVELS["normal"])
        
        # SL для режима
        if sl_percent is None:
            sl_percent = DEFAULT_SL_PERCENT.get(regime, DEFAULT_SL_PERCENT["normal"])
        
        preset = TradingPreset(
            symbol=symbol,
            timeframe=timeframe,
            volatility_regime=regime,
            sector=sector,
            indicator=indicator_params,
            tp_levels=tp_levels,
            sl_percent=sl_percent,
            tp_distribution=TPDistribution(),
            optimization=OptimizationMeta(
                generated_at=datetime.utcnow().isoformat(),
                version="1.0",
            ),
            is_active=True,
            notes="Auto-generated preset. Needs optimization.",
        )
        
        return preset
    
    def generate_for_symbol(self, symbol: str) -> List[TradingPreset]:
        """
        Сгенерировать все пресеты для одного символа.
        
        Args:
            symbol: Торговая пара
            
        Returns:
            Список из 9 пресетов (3 TF × 3 режима)
        """
        presets = []
        
        for tf in TIMEFRAMES:
            for regime in VOLATILITY_REGIMES:
                preset = self.generate_preset(symbol, tf, regime)
                presets.append(preset)
        
        return presets
    
    def generate_all(self, save: bool = True) -> List[TradingPreset]:
        """
        Сгенерировать все 180 пресетов.
        
        Args:
            save: Сохранять ли в файлы
            
        Returns:
            Список всех пресетов
        """
        logger.info(f"Generating {len(TRADING_PAIRS)} × {len(TIMEFRAMES)} × {len(VOLATILITY_REGIMES)} = 180 presets")
        
        presets = []
        
        for symbol in TRADING_PAIRS:
            symbol_presets = self.generate_for_symbol(symbol)
            presets.extend(symbol_presets)
            
            if save:
                for preset in symbol_presets:
                    self.manager.save(preset)
        
        logger.info(f"Generated {len(presets)} presets")
        
        if save:
            logger.info(f"Saved to: {self.output_dir}")
        
        return presets
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Сгенерировать сводку по пресетам.
        
        Returns:
            Словарь со статистикой
        """
        presets = self.manager.load_all()
        
        return {
            "total_presets": len(presets),
            "active_presets": len([p for p in presets if p.is_active]),
            "by_symbol": {s: len([p for p in presets if p.symbol == s]) for s in TRADING_PAIRS},
            "by_timeframe": {tf: len([p for p in presets if p.timeframe == tf]) for tf in TIMEFRAMES},
            "by_regime": {r: len([p for p in presets if p.volatility_regime == r]) for r in VOLATILITY_REGIMES},
            "by_sector": {s: len([p for p in presets if p.sector == s]) for s in SECTORS.keys()},
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_default_presets(output_dir: str) -> int:
    """
    Создать все дефолтные пресеты.
    
    Args:
        output_dir: Директория для сохранения
        
    Returns:
        Количество созданных пресетов
    """
    generator = PresetGenerator(output_dir)
    presets = generator.generate_all(save=True)
    return len(presets)


def load_preset(presets_dir: str, symbol: str, timeframe: str, regime: str = "normal") -> Optional[TradingPreset]:
    """
    Загрузить один пресет.
    
    Args:
        presets_dir: Директория с пресетами
        symbol: Торговая пара
        timeframe: Таймфрейм
        regime: Режим волатильности
        
    Returns:
        TradingPreset или None
    """
    manager = PresetManager(presets_dir)
    return manager.get(symbol, timeframe, regime)


def get_preset_count() -> int:
    """Получить общее количество комбинаций пресетов."""
    return len(TRADING_PAIRS) * len(TIMEFRAMES) * len(VOLATILITY_REGIMES)
