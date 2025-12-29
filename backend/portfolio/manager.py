"""
VELAS Portfolio Manager - главный менеджер портфеля.

Объединяет:
- Управление позициями
- Риск-менеджмент (position sizing, portfolio heat)
- Фильтры (корреляция, секторы)
- Мониторинг и статистика

Использование:
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
        direction="long",
    )
    
    # Открываем позицию
    position = manager.open_position(...)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import logging

from .correlation import (
    CorrelationCalculator,
    CorrelationFilter,
    SectorFilter,
    CorrelationMethod,
    get_symbol_sector,
    SECTORS,
)
from .risk import (
    PositionSizer,
    PortfolioHeatTracker,
    PositionRisk,
    PortfolioRiskMetrics,
    RiskLimits,
    RiskLevel,
)

logger = logging.getLogger(__name__)


class PositionStatus(Enum):
    """Статус позиции."""
    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"


@dataclass
class Position:
    """Активная позиция в портфеле."""
    
    # Идентификация
    id: str = ""
    symbol: str = ""
    timeframe: str = ""
    preset_id: str = ""
    
    # Направление и цены
    direction: str = "long"  # "long" или "short"
    entry_price: float = 0.0
    current_price: float = 0.0
    
    # TP/SL
    tp_prices: List[float] = field(default_factory=list)
    sl_price: float = 0.0
    current_sl: float = 0.0
    
    # Размер
    quantity: float = 0.0
    notional_value: float = 0.0
    leverage: int = 10
    
    # Состояние
    status: PositionStatus = PositionStatus.OPEN
    tp_hits: List[int] = field(default_factory=list)  # Индексы достигнутых TP
    position_remaining: float = 100.0  # Оставшаяся позиция в %
    
    # Трекинг
    entry_time: datetime = None
    last_update: datetime = None
    realized_pnl: float = 0.0
    
    def __post_init__(self):
        if self.entry_time is None:
            self.entry_time = datetime.now()
        if self.last_update is None:
            self.last_update = datetime.now()
        if self.current_sl == 0 and self.sl_price > 0:
            self.current_sl = self.sl_price
    
    @property
    def is_long(self) -> bool:
        return self.direction == "long"
    
    @property
    def is_open(self) -> bool:
        return self.status == PositionStatus.OPEN
    
    @property
    def unrealized_pnl_percent(self) -> float:
        """Нереализованный PnL в %."""
        if self.entry_price <= 0:
            return 0.0
        
        if self.is_long:
            return (self.current_price - self.entry_price) / self.entry_price * 100
        else:
            return (self.entry_price - self.current_price) / self.entry_price * 100
    
    @property
    def unrealized_pnl_amount(self) -> float:
        """Нереализованный PnL в USDT."""
        return self.notional_value * self.unrealized_pnl_percent / 100
    
    @property
    def risk_percent(self) -> float:
        """Риск позиции в %."""
        if self.entry_price <= 0 or self.current_sl <= 0:
            return 0.0
        
        if self.is_long:
            return (self.entry_price - self.current_sl) / self.entry_price * 100
        else:
            return (self.current_sl - self.entry_price) / self.entry_price * 100
    
    @property
    def sector(self) -> str:
        """Сектор пары."""
        return get_symbol_sector(self.symbol)
    
    @property
    def signal_id(self) -> str:
        """Уникальный ID сигнала в формате Cornix."""
        direction = "Long" if self.is_long else "Short"
        ts = self.entry_time.strftime("%d_%m_%Y_%H_%M") if self.entry_time else "unknown"
        return f"#{direction}_{self.symbol}_{ts}"
    
    def update_price(self, price: float) -> None:
        """Обновить текущую цену."""
        self.current_price = price
        self.last_update = datetime.now()
    
    def to_position_risk(self) -> PositionRisk:
        """Конвертировать в PositionRisk для трекера."""
        return PositionRisk(
            symbol=self.symbol,
            direction=self.direction,
            entry_price=self.entry_price,
            current_price=self.current_price,
            stop_loss=self.current_sl,
            quantity=self.quantity,
            notional_value=self.notional_value,
        )
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "preset_id": self.preset_id,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "tp_prices": self.tp_prices,
            "sl_price": self.sl_price,
            "current_sl": self.current_sl,
            "quantity": self.quantity,
            "notional_value": round(self.notional_value, 2),
            "leverage": self.leverage,
            "status": self.status.value,
            "tp_hits": self.tp_hits,
            "position_remaining": self.position_remaining,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "realized_pnl": round(self.realized_pnl, 2),
            "unrealized_pnl_percent": round(self.unrealized_pnl_percent, 2),
            "unrealized_pnl_amount": round(self.unrealized_pnl_amount, 2),
            "risk_percent": round(self.risk_percent, 2),
            "sector": self.sector,
            "signal_id": self.signal_id,
        }


class PortfolioManager:
    """
    Главный менеджер портфеля.
    
    Ответственность:
    - Управление позициями (открытие, обновление, закрытие)
    - Риск-менеджмент (position sizing, portfolio heat)
    - Фильтры входа (корреляция, секторы, лимиты)
    - Статистика и мониторинг
    """
    
    def __init__(
        self,
        balance: float,
        risk_limits: RiskLimits = None,
        leverage: int = 10,
    ):
        """
        Args:
            balance: Начальный баланс в USDT
            risk_limits: Лимиты риска
            leverage: Плечо по умолчанию
        """
        self.balance = balance
        self.initial_balance = balance
        self.leverage = leverage
        self.risk_limits = risk_limits or RiskLimits()
        
        # Компоненты
        self._positions: Dict[str, Position] = {}
        
        self.position_sizer = PositionSizer(
            balance=balance,
            risk_per_trade=self.risk_limits.risk_per_trade,
            max_position_size=self.risk_limits.max_position_size,
        )
        
        self.heat_tracker = PortfolioHeatTracker(
            balance=balance,
            max_heat=self.risk_limits.max_portfolio_heat,
            max_positions=self.risk_limits.max_positions,
        )
        
        self.correlation_calc = CorrelationCalculator(
            method=CorrelationMethod.PEARSON,
            period_days=30,
        )
        
        self.correlation_filter = CorrelationFilter(
            calculator=self.correlation_calc,
            threshold=self.risk_limits.correlation_threshold,
        )
        
        self.sector_filter = SectorFilter(
            max_per_sector=self.risk_limits.max_per_sector,
        )
        
        # Статистика
        self._total_trades = 0
        self._winning_trades = 0
        self._total_pnl = 0.0
        self._peak_balance = balance
        self._max_drawdown = 0.0
    
    # ========== Balance Management ==========
    
    def update_balance(self, balance: float) -> None:
        """Обновить баланс."""
        self.balance = balance
        self.position_sizer.update_balance(balance)
        self.heat_tracker.update_balance(balance)
        
        if balance > self._peak_balance:
            self._peak_balance = balance
    
    def get_balance(self) -> float:
        """Получить текущий баланс."""
        return self.balance
    
    def get_equity(self) -> float:
        """Получить equity (баланс + unrealized PnL)."""
        unrealized = sum(p.unrealized_pnl_amount for p in self._positions.values())
        return self.balance + unrealized
    
    # ========== Position Filters ==========
    
    def can_open_position(
        self,
        symbol: str,
        check_correlation: bool = True,
        check_sector: bool = True,
    ) -> Tuple[bool, str]:
        """
        Проверить можно ли открыть позицию по символу.
        
        Returns:
            (can_open, reason)
        """
        open_symbols = list(self._positions.keys())
        
        # 1. Проверяем уже открытую позицию
        if symbol in self._positions:
            return False, f"Position already open for {symbol}"
        
        # 2. Проверяем лимит позиций
        if len(self._positions) >= self.risk_limits.max_positions:
            return False, f"Max positions reached ({self.risk_limits.max_positions})"
        
        # 3. Проверяем portfolio heat
        can_heat, reason = self.heat_tracker.can_open_position()
        if not can_heat:
            return False, reason
        
        # 4. Проверяем сектор
        if check_sector:
            if not self.sector_filter.can_open_position(symbol, open_symbols):
                sector = get_symbol_sector(symbol)
                return False, f"Sector limit reached for {sector}"
        
        # 5. Проверяем корреляцию
        if check_correlation and open_symbols:
            can_corr, blocking = self.correlation_filter.can_open_position(symbol, open_symbols)
            if not can_corr:
                return False, f"High correlation with {blocking}"
        
        return True, "OK"
    
    # ========== Position Sizing ==========
    
    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        direction: str = "long",
        leverage: int = None,
        atr: float = None,
        avg_atr: float = None,
    ) -> dict:
        """
        Рассчитать размер позиции.
        
        Args:
            symbol: Символ
            entry_price: Цена входа
            stop_loss: Стоп-лосс
            direction: Направление
            leverage: Плечо (или default)
            atr: Текущий ATR (для волатильной корректировки)
            avg_atr: Средний ATR
            
        Returns:
            dict с размерами и метриками
        """
        lev = leverage or self.leverage
        
        # Базовый расчёт или с волатильностью
        if atr and avg_atr:
            size_info = self.position_sizer.calculate_volatility_adjusted(
                entry_price=entry_price,
                stop_loss=stop_loss,
                atr=atr,
                avg_atr=avg_atr,
                leverage=lev,
                direction=direction,
            )
        else:
            size_info = self.position_sizer.calculate_position_size(
                entry_price=entry_price,
                stop_loss=stop_loss,
                leverage=lev,
                direction=direction,
            )
        
        size_info["symbol"] = symbol
        return size_info
    
    # ========== Position Management ==========
    
    def open_position(
        self,
        symbol: str,
        timeframe: str,
        direction: str,
        entry_price: float,
        tp_prices: List[float],
        sl_price: float,
        quantity: float = None,
        notional_value: float = None,
        leverage: int = None,
        preset_id: str = "",
        position_id: str = None,
    ) -> Optional[Position]:
        """
        Открыть новую позицию.
        
        Args:
            symbol: Символ
            timeframe: Таймфрейм
            direction: "long" или "short"
            entry_price: Цена входа
            tp_prices: Список цен TP
            sl_price: Цена SL
            quantity: Количество (или рассчитать по notional)
            notional_value: Размер позиции в USDT
            leverage: Плечо
            preset_id: ID пресета
            position_id: ID позиции (или генерируется)
            
        Returns:
            Position или None если нельзя открыть
        """
        # Проверяем можно ли открыть
        can_open, reason = self.can_open_position(symbol)
        if not can_open:
            logger.warning(f"Cannot open position for {symbol}: {reason}")
            return None
        
        # Рассчитываем размер если не указан
        if quantity is None and notional_value is None:
            size_info = self.calculate_position_size(
                symbol=symbol,
                entry_price=entry_price,
                stop_loss=sl_price,
                direction=direction,
                leverage=leverage,
            )
            quantity = size_info["quantity"]
            notional_value = size_info["position_size"]
        elif quantity is None:
            quantity = notional_value / entry_price
        elif notional_value is None:
            notional_value = quantity * entry_price
        
        # Создаём позицию
        import uuid
        position = Position(
            id=position_id or str(uuid.uuid4())[:8],
            symbol=symbol,
            timeframe=timeframe,
            preset_id=preset_id,
            direction=direction,
            entry_price=entry_price,
            current_price=entry_price,
            tp_prices=tp_prices,
            sl_price=sl_price,
            current_sl=sl_price,
            quantity=quantity,
            notional_value=notional_value,
            leverage=leverage or self.leverage,
            status=PositionStatus.OPEN,
        )
        
        # Добавляем в трекер
        position_risk = position.to_position_risk()
        if not self.heat_tracker.add_position(position_risk):
            logger.warning(f"Failed to add position to heat tracker: {symbol}")
            return None
        
        # Сохраняем
        self._positions[symbol] = position
        
        logger.info(f"Opened position: {position.signal_id} - Entry: {entry_price}, Size: {notional_value:.2f}")
        
        return position
    
    def update_position_price(self, symbol: str, price: float) -> Optional[Position]:
        """Обновить текущую цену позиции."""
        position = self._positions.get(symbol)
        if position:
            position.update_price(price)
            
            # Обновляем в трекере
            self.heat_tracker.update_position(position.to_position_risk())
        
        return position
    
    def update_position_sl(self, symbol: str, new_sl: float) -> Optional[Position]:
        """Обновить стоп-лосс позиции."""
        position = self._positions.get(symbol)
        if position:
            # Стоп может только улучшаться
            if position.is_long:
                position.current_sl = max(position.current_sl, new_sl)
            else:
                position.current_sl = min(position.current_sl, new_sl)
            
            position.last_update = datetime.now()
            
            # Обновляем в трекере
            self.heat_tracker.update_position(position.to_position_risk())
        
        return position
    
    def record_tp_hit(
        self,
        symbol: str,
        tp_index: int,
        close_percent: float,
        realized_pnl: float,
    ) -> Optional[Position]:
        """
        Записать достижение TP.
        
        Args:
            symbol: Символ
            tp_index: Индекс TP (1-6)
            close_percent: % закрытой позиции
            realized_pnl: Реализованный PnL в USDT
        """
        position = self._positions.get(symbol)
        if position:
            position.tp_hits.append(tp_index)
            position.position_remaining -= close_percent
            position.realized_pnl += realized_pnl
            position.last_update = datetime.now()
            
            self._total_pnl += realized_pnl
        
        return position
    
    def close_position(
        self,
        symbol: str,
        close_price: float,
        reason: str = "manual",
        realized_pnl: float = None,
    ) -> Optional[Position]:
        """
        Закрыть позицию.
        
        Args:
            symbol: Символ
            close_price: Цена закрытия
            reason: Причина закрытия
            realized_pnl: Реализованный PnL (или рассчитать)
            
        Returns:
            Закрытая позиция
        """
        position = self._positions.get(symbol)
        if not position:
            return None
        
        # Рассчитываем PnL если не указан
        if realized_pnl is None:
            remaining_notional = position.notional_value * position.position_remaining / 100
            
            if position.is_long:
                pnl_percent = (close_price - position.entry_price) / position.entry_price * 100
            else:
                pnl_percent = (position.entry_price - close_price) / position.entry_price * 100
            
            realized_pnl = remaining_notional * pnl_percent / 100
        
        # Обновляем позицию
        position.status = PositionStatus.CLOSED
        position.current_price = close_price
        position.realized_pnl += realized_pnl
        position.position_remaining = 0
        position.last_update = datetime.now()
        
        # Обновляем статистику
        self._total_trades += 1
        self._total_pnl += realized_pnl
        
        if position.realized_pnl > 0:
            self._winning_trades += 1
        
        # Обновляем баланс
        self.update_balance(self.balance + realized_pnl)
        
        # Удаляем из активных
        self.heat_tracker.remove_position(symbol)
        del self._positions[symbol]
        
        logger.info(f"Closed position: {position.signal_id} - PnL: {realized_pnl:.2f} ({reason})")
        
        return position
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Получить позицию."""
        return self._positions.get(symbol)
    
    def get_all_positions(self) -> List[Position]:
        """Получить все позиции."""
        return list(self._positions.values())
    
    def get_open_symbols(self) -> List[str]:
        """Получить список символов с открытыми позициями."""
        return list(self._positions.keys())
    
    # ========== Statistics & Metrics ==========
    
    def get_risk_metrics(self) -> PortfolioRiskMetrics:
        """Получить метрики риска."""
        return self.heat_tracker.get_metrics()
    
    def get_portfolio_stats(self) -> dict:
        """Получить статистику портфеля."""
        equity = self.get_equity()
        unrealized = sum(p.unrealized_pnl_amount for p in self._positions.values())
        
        drawdown = 0.0
        if self._peak_balance > 0:
            drawdown = (self._peak_balance - equity) / self._peak_balance * 100
            if drawdown > self._max_drawdown:
                self._max_drawdown = drawdown
        
        win_rate = 0.0
        if self._total_trades > 0:
            win_rate = self._winning_trades / self._total_trades * 100
        
        return {
            "balance": round(self.balance, 2),
            "equity": round(equity, 2),
            "initial_balance": round(self.initial_balance, 2),
            "total_pnl": round(self._total_pnl, 2),
            "total_pnl_percent": round(self._total_pnl / self.initial_balance * 100, 2) if self.initial_balance > 0 else 0,
            "unrealized_pnl": round(unrealized, 2),
            "open_positions": len(self._positions),
            "max_positions": self.risk_limits.max_positions,
            "total_trades": self._total_trades,
            "winning_trades": self._winning_trades,
            "win_rate": round(win_rate, 2),
            "current_drawdown": round(max(0, drawdown), 2),
            "max_drawdown": round(self._max_drawdown, 2),
            "portfolio_heat": round(self.heat_tracker.current_heat, 2),
            "risk_level": self.heat_tracker.get_risk_level().value,
        }
    
    def get_sector_stats(self) -> Dict[str, dict]:
        """Получить статистику по секторам."""
        return self.sector_filter.get_sector_stats(list(self._positions.keys()))
    
    # ========== Correlation Data ==========
    
    def add_price_data(self, symbol: str, df) -> None:
        """Добавить ценовые данные для корреляций."""
        self.correlation_calc.add_price_data(symbol, df)
    
    def get_correlation_matrix(self):
        """Получить матрицу корреляций."""
        return self.correlation_calc.calculate_matrix()
    
    # ========== Serialization ==========
    
    def to_dict(self) -> dict:
        """Сериализовать состояние."""
        return {
            "balance": self.balance,
            "initial_balance": self.initial_balance,
            "leverage": self.leverage,
            "risk_limits": self.risk_limits.to_dict(),
            "positions": {s: p.to_dict() for s, p in self._positions.items()},
            "stats": self.get_portfolio_stats(),
            "risk_metrics": self.get_risk_metrics().to_dict(),
        }
