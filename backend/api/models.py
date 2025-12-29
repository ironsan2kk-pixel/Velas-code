"""
VELAS API Models - Pydantic схемы.

Все модели для API endpoints.
"""

from datetime import datetime
from typing import List, Optional, Generic, TypeVar
from pydantic import BaseModel, Field
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

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


# Алиасы для совместимости с routes
Side = SideEnum
Timeframe = TimeframeEnum
VolatilityRegime = VolatilityRegimeEnum
SignalStatus = SignalStatusEnum


# =============================================================================
# GENERIC RESPONSES
# =============================================================================

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


# =============================================================================
# POSITION MODELS
# =============================================================================

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


# =============================================================================
# SIGNAL MODELS
# =============================================================================

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


class Signal(BaseModel):
    """Signal model для pairs.py"""
    id: int
    symbol: str
    side: SideEnum
    timeframe: TimeframeEnum
    entry_price: float
    current_price: Optional[float] = None
    sl_price: float
    tp1_price: Optional[float] = None
    tp2_price: Optional[float] = None
    tp3_price: Optional[float] = None
    tp4_price: Optional[float] = None
    tp5_price: Optional[float] = None
    tp6_price: Optional[float] = None
    status: SignalStatusEnum = SignalStatusEnum.PENDING
    preset_id: Optional[str] = None
    volatility_regime: VolatilityRegimeEnum = VolatilityRegimeEnum.NORMAL
    confidence: Optional[float] = None
    filters_passed: List[str] = Field(default_factory=list)
    filters_failed: List[str] = Field(default_factory=list)
    telegram_sent: bool = False
    cornix_sent: bool = False
    created_at: Optional[str] = None


# =============================================================================
# TRADE / HISTORY MODELS
# =============================================================================

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


# =============================================================================
# DASHBOARD MODELS
# =============================================================================

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


# =============================================================================
# PAIRS MODELS
# =============================================================================

class Pair(BaseModel):
    """Торговая пара."""
    symbol: str
    name: str
    sector: str
    current_price: float
    price_change_24h: float
    price_change_percent_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    volatility_regime: VolatilityRegimeEnum = VolatilityRegimeEnum.NORMAL
    atr_ratio: float = 1.0
    has_active_position: bool = False
    active_position_side: Optional[SideEnum] = None
    last_signal_time: Optional[str] = None


class PairDetail(Pair):
    """Детальная информация о паре."""
    signals_count_24h: int = 0
    trades_count_24h: int = 0
    win_rate_30d: float = 0.0
    total_pnl_30d: float = 0.0
    avg_trade_duration: int = 0
    correlation_group: str = "Other"
    active_timeframes: List[TimeframeEnum] = Field(default_factory=list)
    preset_ids: List[str] = Field(default_factory=list)


class OHLCV(BaseModel):
    """Свеча OHLCV."""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


# =============================================================================
# ANALYTICS MODELS
# =============================================================================

class EquityPoint(BaseModel):
    """Точка на графике equity."""
    timestamp: str
    equity: float
    drawdown: float


class MonthlyStats(BaseModel):
    """Статистика за месяц."""
    month: str
    year: int
    trades: int
    win_rate: float
    pnl: float
    pnl_percent: float
    best_day: float
    worst_day: float
    max_drawdown: float


class PairStats(BaseModel):
    """Статистика по паре."""
    symbol: str
    trades: int
    win_rate: float
    pnl: float
    avg_pnl: float
    profit_factor: float
    sharpe: float
    max_drawdown: float


class CorrelationMatrix(BaseModel):
    """Матрица корреляций."""
    symbols: List[str]
    matrix: List[List[float]]


# =============================================================================
# BACKTEST MODELS
# =============================================================================

class BacktestConfig(BaseModel):
    """Конфигурация бэктеста."""
    symbols: List[str] = Field(default_factory=list)
    timeframes: List[TimeframeEnum] = Field(default_factory=list)
    start_date: str
    end_date: str
    initial_capital: float = 10000.0
    position_size_percent: float = 2.0
    use_filters: bool = True
    walk_forward: bool = False


class BacktestResult(BaseModel):
    """Результат бэктеста."""
    id: str
    config: BacktestConfig
    status: str = "pending"  # pending, running, completed, failed
    progress: int = 0
    total_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    equity_curve: List[EquityPoint] = Field(default_factory=list)
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


# =============================================================================
# SETTINGS MODELS
# =============================================================================

class TelegramSettings(BaseModel):
    """Настройки Telegram."""
    enabled: bool = True
    send_signals: bool = True
    send_tp_hits: bool = True
    send_sl_hits: bool = True
    send_daily_summary: bool = True
    quiet_hours_start: Optional[int] = None  # 0-23
    quiet_hours_end: Optional[int] = None


class NotificationSettings(BaseModel):
    """Настройки уведомлений."""
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    sound_enabled: bool = True
    push_enabled: bool = True


class TradingSettings(BaseModel):
    """Настройки торговли."""
    enabled: bool = True
    max_positions: int = 5
    position_size_percent: float = 2.0
    max_portfolio_heat: float = 15.0
    use_correlation_filter: bool = True
    max_correlated_positions: int = 2


class AllSettings(BaseModel):
    """Все настройки системы."""
    trading: TradingSettings = Field(default_factory=TradingSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    theme: str = "dark"
    language: str = "ru"


class Preset(BaseModel):
    """Пресет для пары."""
    id: str
    symbol: str
    timeframe: TimeframeEnum
    volatility_regime: VolatilityRegimeEnum
    i1: int = 20
    i2: int = 40
    i3: int = 10
    i4: int = 15
    i5: int = 12
    tp1: float = 1.0
    tp2: float = 2.0
    tp3: float = 3.0
    tp4: float = 4.0
    tp5: float = 7.5
    tp6: float = 14.0
    sl: float = 8.5
    tp_distribution: List[float] = Field(default_factory=lambda: [10.0, 10.0, 10.0, 20.0, 25.0, 25.0])
    filters: List[str] = Field(default_factory=lambda: ["volume", "rsi", "adx"])
    enabled: bool = True
    last_updated: Optional[str] = None


# =============================================================================
# SYSTEM MODELS
# =============================================================================

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
