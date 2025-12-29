"""
VELAS Live Module - компоненты для реальной торговли.

Компоненты:
- LiveEngine: Главный движок
- SignalManager: Управление сигналами
- PositionTracker: Отслеживание позиций
- StateManager: Персистентное состояние

Использование:
    from backend.live import LiveEngine, EngineConfig
    
    config = EngineConfig(
        trading_mode="paper",
        initial_balance=10000,
    )
    
    engine = LiveEngine(config)
    
    # Callbacks
    engine.on_signal = lambda s: print(f"Signal: {s}")
    engine.on_position_event = lambda e: print(f"Event: {e}")
    
    # Запуск
    await engine.start()
"""

# State
from .state import (
    SystemStatus,
    StateConfig,
    StateManager,
)

# Signal Manager
from .signal_manager import (
    SignalStatus,
    EnrichedSignal,
    SignalManager,
)

# Position Tracker
from .position_tracker import (
    PositionEvent,
    TrackingEvent,
    PositionTracker,
)

# Engine (может не импортироваться если нет binance_ws)
try:
    from .engine import (
        EngineStatus,
        EngineConfig,
        LiveEngine,
    )
    HAS_ENGINE = True
except ImportError as e:
    import logging
    logging.warning(f"LiveEngine not available: {e}")
    EngineStatus = None
    EngineConfig = None
    LiveEngine = None
    HAS_ENGINE = False

__all__ = [
    # State
    "SystemStatus",
    "StateConfig",
    "StateManager",
    
    # Signal Manager
    "SignalStatus",
    "EnrichedSignal",
    "SignalManager",
    
    # Position Tracker
    "PositionEvent",
    "TrackingEvent",
    "PositionTracker",
    
    # Engine
    "EngineStatus",
    "EngineConfig",
    "LiveEngine",
    "HAS_ENGINE",
]
