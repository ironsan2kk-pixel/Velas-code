"""
VELAS Core Module - Индикатор, сигналы, TP/SL, волатильность, пресеты.

Exports:
    - VolatilityRegime, VolatilityAnalyzer - анализ волатильности
    - PresetManager, PresetGenerator - управление пресетами
    - TradingPreset, IndicatorParams, TPLevels - структуры данных
    - TRADING_PAIRS, TIMEFRAMES, VOLATILITY_REGIMES - константы
"""

from .volatility import (
    VolatilityRegime,
    VolatilityConfig,
    VolatilityResult,
    VolatilityAnalyzer,
    get_volatility_regime,
    analyze_volatility,
    calculate_volatility_stats,
)

from .presets import (
    # Constants
    TRADING_PAIRS,
    TIMEFRAMES,
    VOLATILITY_REGIMES,
    SECTORS,
    get_sector,
    get_preset_count,
    
    # Data classes
    IndicatorParams,
    TPLevels,
    TPDistribution,
    OptimizationMeta,
    TradingPreset,
    
    # Managers
    PresetManager,
    PresetGenerator,
    
    # Defaults
    DEFAULT_TP_LEVELS,
    DEFAULT_SL_PERCENT,
    DEFAULT_INDICATOR_PARAMS,
    
    # Helper functions
    create_default_presets,
    load_preset,
)

__all__ = [
    # Volatility
    "VolatilityRegime",
    "VolatilityConfig",
    "VolatilityResult",
    "VolatilityAnalyzer",
    "get_volatility_regime",
    "analyze_volatility",
    "calculate_volatility_stats",
    
    # Constants
    "TRADING_PAIRS",
    "TIMEFRAMES",
    "VOLATILITY_REGIMES",
    "SECTORS",
    "get_sector",
    "get_preset_count",
    
    # Data classes
    "IndicatorParams",
    "TPLevels",
    "TPDistribution",
    "OptimizationMeta",
    "TradingPreset",
    
    # Managers
    "PresetManager",
    "PresetGenerator",
    
    # Defaults
    "DEFAULT_TP_LEVELS",
    "DEFAULT_SL_PERCENT",
    "DEFAULT_INDICATOR_PARAMS",
    
    # Functions
    "create_default_presets",
    "load_preset",
]
