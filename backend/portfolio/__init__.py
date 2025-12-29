"""
VELAS Portfolio Module - управление портфелем и риск-менеджмент.

Компоненты:
- PortfolioManager: Главный менеджер портфеля
- CorrelationCalculator: Расчёт корреляций между парами
- PositionSizer: Расчёт размера позиций
- PortfolioHeatTracker: Трекинг общего риска портфеля

Использование:
    from backend.portfolio import PortfolioManager, RiskLimits
    
    manager = PortfolioManager(
        balance=10000,
        risk_limits=RiskLimits(max_positions=5, risk_per_trade=2.0)
    )
    
    # Проверяем можно ли открыть позицию
    can_open, reason = manager.can_open_position("BTCUSDT")
    
    # Рассчитываем размер
    size_info = manager.calculate_position_size(
        symbol="BTCUSDT",
        entry_price=42000,
        stop_loss=41000,
    )
    
    # Открываем позицию
    position = manager.open_position(...)
"""

# Correlation
from .correlation import (
    CorrelationMethod,
    CorrelationResult,
    CorrelationMatrix,
    CorrelationCalculator,
    CorrelationFilter,
    SectorFilter,
    SECTORS,
    get_symbol_sector,
    get_sector_symbols,
    are_same_sector,
)

# Risk Management
from .risk import (
    RiskLevel,
    PositionRisk,
    PortfolioRiskMetrics,
    PositionSizer,
    PortfolioHeatTracker,
    RiskLimits,
)

# Portfolio Manager
from .manager import (
    PositionStatus,
    Position,
    PortfolioManager,
)

__all__ = [
    # Correlation
    "CorrelationMethod",
    "CorrelationResult",
    "CorrelationMatrix",
    "CorrelationCalculator",
    "CorrelationFilter",
    "SectorFilter",
    "SECTORS",
    "get_symbol_sector",
    "get_sector_symbols",
    "are_same_sector",
    
    # Risk
    "RiskLevel",
    "PositionRisk",
    "PortfolioRiskMetrics",
    "PositionSizer",
    "PortfolioHeatTracker",
    "RiskLimits",
    
    # Manager
    "PositionStatus",
    "Position",
    "PortfolioManager",
]
