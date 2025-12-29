# VELAS Trading System - Core Module
# Ядро системы: индикатор Velas, сигналы, TP/SL

__version__ = "0.3.0"

from .velas_indicator import VelasIndicator, VelasPreset, VELAS_PRESETS_60
from .signals import SignalGenerator, Signal, SignalType
from .tpsl import TPSLManager, TPSLConfig, StopManagement

__all__ = [
    "VelasIndicator",
    "VelasPreset", 
    "VELAS_PRESETS_60",
    "SignalGenerator",
    "Signal",
    "SignalType",
    "TPSLManager",
    "TPSLConfig",
    "StopManagement",
]
