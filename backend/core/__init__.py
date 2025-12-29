"""
VELAS Core Module - индикаторы, сигналы, TP/SL.

Компоненты:
- VelasIndicator: Расчёт индикатора Велас
- SignalGenerator: Генерация торговых сигналов
- TPSLManager: Управление TP/SL уровнями
- PresetManager: Управление пресетами
- VolatilityAnalyzer: Анализ волатильности
"""

from .velas_indicator import VelasIndicator, VelasPreset
from .signals import Signal, SignalType, SignalGenerator, FilterConfig
from .tpsl import TPSLManager, TPSLConfig, TPSLLevels
from .presets import PresetManager, TradingPreset, PresetGenerator
from .volatility import VolatilityAnalyzer, VolatilityRegime

__all__ = [
    "VelasIndicator",
    "VelasPreset",
    "Signal",
    "SignalType",
    "SignalGenerator",
    "FilterConfig",
    "TPSLManager",
    "TPSLConfig",
    "TPSLLevels",
    "PresetManager",
    "TradingPreset",
    "PresetGenerator",
    "VolatilityAnalyzer",
    "VolatilityRegime",
]
