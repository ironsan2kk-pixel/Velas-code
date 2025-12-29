"""
VELAS API Models - Pydantic схемы.
"""

from datetime import datetime
from typing import List, Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from enum import Enum


class SideEnum(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class PositionStatusEnum(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    PARTIAL = "partial"


class SignalStatusEnum(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    FILLED = "filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class VolatilityRegimeEnum(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class TimeframeEnum(str, Enum):
    M30 = "30m"
    H1 = "1h"
    H2 = "2h"


class SystemStatusEnum(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class PositionResponse(BaseModel):
    id: int
    symbol: str
    side: SideEnum
    timeframe: TimeframeEnum
    preset_id: Optional[str] = None
    entry_price: float
    current_price: Optional[float] = None
    close_price: Optional[float] = None
    sl_price: float
    current_sl: Optional[float] = None
    tp1_price: Optional[float] = None
    tp2_price: Optional[float] = None
    tp3_price: Optional[float] = None
    tp4_price: Optional[float] = None
    tp5_price: Optional[float] = None
    tp6_price: Optional[float] = None
    tp1_hit: bool = False
    tp2_hit: bool = False
    tp3_hit: bool = False
    tp4_hit: bool = False
    tp5_hit: bool = False
    tp6_hit: bool = False
    quantity: Optional[float] = None
    notional_value: Optional[float] = None
    leverage: int = 10
    position_remaining: float = 100.0
    realized_pnl: float = 0.0
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_percent: Optional[float] = None
    status: PositionStatusEnum = PositionStatusEnum.OPEN
    close_reason: Optional[str] = None
    entry_time: Optional[datetime] = None
    close_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PositionSummary(BaseModel):
    total_positions: int
    open_positions: int
    total_pnl: float
    total_pnl_percent: float
    winning_positions: int
    losing_positions: int
    portfolio_heat: float
    max_heat: float = 15.0


class SignalResponse(BaseModel):
    id: int
    symbol: str
    side: SideEnum
    timeframe: TimeframeEnum
    entry_price: float
    sl_price: float
    tp1_price: Optional[float] = None
    tp2_price: Optional[float] = None
    tp3_price: Optional[float] = None
    tp4_price: Optional[float] = None
    tp5_price: Optional[float] = None
    tp6_price: Optional[float] = None
    preset_id: Optional[str] = None
    volatility_regime: VolatilityRegimeEnum = VolatilityRegimeEnum.NORMAL
    confidence: Optional[float] = None
    status: SignalStatusEnum = SignalStatusEnum.PENDING
    position_id: Optional[int] = None
    telegram_sent: bool = False
    filter_passed: bool = True
    filter_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TradeHistoryResponse(BaseModel):
    id: int
    position_id: Optional[int] = None
    symbol: str
    side: SideEnum
    timeframe: TimeframeEnum
    entry_price: float
    exit_price: float
    pnl_percent: float
    pnl_usd: float
    exit_reason: str
    tp_hits: int = 0
    duration_minutes: Optional[int] = None
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class HistoryStats(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_pnl: float
    max_win: float
    max_loss: float
    profit_factor: float
    avg_duration_minutes: Optional[float] = None


class DashboardSummary(BaseModel):
    status: SystemStatusEnum
    balance: float
    total_pnl: float
    total_pnl_percent: float
    open_positions: int
    max_positions: int
    signals_today: int
    win_rate: float
    portfolio_heat: float
    max_heat: float


class DashboardMetrics(BaseModel):
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    avg_trade_duration: Optional[float] = None
    best_pair: Optional[str] = None
    worst_pair: Optional[str] = None


class EquityPoint(BaseModel):
    timestamp: datetime
    equity: float
    drawdown: float


class ComponentStatus(BaseModel):
    name: str
    status: SystemStatusEnum
    uptime_seconds: Optional[int] = None
    last_error: Optional[str] = None
    details: Optional[dict] = None


class SystemStatusResponse(BaseModel):
    status: SystemStatusEnum
    trading_active: bool
    uptime_seconds: int
    version: str
    components: List[ComponentStatus]
    last_signal_time: Optional[datetime] = None
    last_trade_time: Optional[datetime] = None


class LogEntry(BaseModel):
    id: int
    level: str
    component: str
    message: str
    details: Optional[dict] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
