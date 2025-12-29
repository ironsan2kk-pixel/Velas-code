"""
VELAS Core Module - индикаторы, сигналы, TP/SL.

Компоненты:
- VelasIndicator: Расчёт индикатора Велас
- SignalGenerator: Генерация торговых сигналов
- TPSLManager: Управление TP/SL уровнями
- PresetManager: Управление пресетами
- VolatilityAnalyzer: Анализ волатильности
"""

from .velas_indicator import VelasIndicator, VelasPreset, VelasResult
from .signals import Signal, SignalType, SignalStrength, SignalGenerator, FilterConfig
from .tpsl import TPSLManager, TPSLConfig, TPSLLevels, TPLevel, StopManagement
from .presets import PresetManager, TradingPreset, PresetGenerator, IndicatorParams
from .volatility import VolatilityAnalyzer, VolatilityRegime, VolatilityResult

__all__ = [
    # Indicator
    "VelasIndicator",
    "VelasPreset",
    "VelasResult",
    # Signals
    "Signal",
    "SignalType",
    "SignalStrength",
    "SignalGenerator",
    "FilterConfig",
    # TP/SL
    "TPSLManager",
    "TPSLConfig",
    "TPSLLevels",
    "TPLevel",
    "StopManagement",
    # Presets
    "PresetManager",
    "TradingPreset",
    "PresetGenerator",
    "IndicatorParams",
    # Volatility
    "VolatilityAnalyzer",
    "VolatilityRegime",
    "VolatilityResult",
]
