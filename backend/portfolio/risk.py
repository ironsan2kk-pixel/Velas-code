"""
VELAS Risk Management - управление рисками портфеля.

Включает:
- Position sizing (расчёт размера позиции)
- Portfolio heat tracking (общий риск портфеля)
- Drawdown monitoring (мониторинг просадки)
- Risk limits (лимиты риска)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np


class RiskLevel(Enum):
    """Уровень риска."""
    LOW = "low"           # 0-3% portfolio heat
    NORMAL = "normal"     # 3-5% portfolio heat
    HIGH = "high"         # 5-8% portfolio heat
    CRITICAL = "critical" # >8% portfolio heat


@dataclass
class PositionRisk:
    """Риск отдельной позиции."""
    
    symbol: str
    direction: str  # "long" или "short"
    entry_price: float
    current_price: float
    stop_loss: float
    quantity: float
    notional_value: float  # В USDT
    
    @property
    def risk_percent(self) -> float:
        """Риск позиции в % от входа."""
        if self.direction == "long":
            return (self.entry_price - self.stop_loss) / self.entry_price * 100
        else:
            return (self.stop_loss - self.entry_price) / self.entry_price * 100
    
    @property
    def risk_amount(self) -> float:
        """Риск позиции в USDT."""
        return self.notional_value * self.risk_percent / 100
    
    @property
    def unrealized_pnl_percent(self) -> float:
        """Нереализованный PnL в %."""
        if self.direction == "long":
            return (self.current_price - self.entry_price) / self.entry_price * 100
        else:
            return (self.entry_price - self.current_price) / self.entry_price * 100
    
    @property
    def unrealized_pnl_amount(self) -> float:
        """Нереализованный PnL в USDT."""
        return self.notional_value * self.unrealized_pnl_percent / 100
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "stop_loss": self.stop_loss,
            "quantity": self.quantity,
            "notional_value": self.notional_value,
            "risk_percent": round(self.risk_percent, 2),
            "risk_amount": round(self.risk_amount, 2),
            "unrealized_pnl_percent": round(self.unrealized_pnl_percent, 2),
            "unrealized_pnl_amount": round(self.unrealized_pnl_amount, 2),
        }


@dataclass
class PortfolioRiskMetrics:
    """Метрики риска портфеля."""
    
    total_balance: float
    used_margin: float
    free_margin: float
    
    portfolio_heat: float  # Суммарный риск в %
    max_portfolio_heat: float = 8.0
    
    total_unrealized_pnl: float = 0.0
    position_count: int = 0
    
    drawdown_current: float = 0.0
    drawdown_max: float = 0.0
    
    risk_level: RiskLevel = RiskLevel.LOW
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def heat_percent_of_limit(self) -> float:
        """Portfolio heat как % от лимита."""
        if self.max_portfolio_heat <= 0:
            return 0.0
        return self.portfolio_heat / self.max_portfolio_heat * 100
    
    @property
    def margin_usage_percent(self) -> float:
        """Использование маржи в %."""
        if self.total_balance <= 0:
            return 0.0
        return self.used_margin / self.total_balance * 100
    
    @property
    def can_open_more(self) -> bool:
        """Можно ли открывать новые позиции."""
        return self.portfolio_heat < self.max_portfolio_heat
    
    def to_dict(self) -> dict:
        return {
            "total_balance": round(self.total_balance, 2),
            "used_margin": round(self.used_margin, 2),
            "free_margin": round(self.free_margin, 2),
            "portfolio_heat": round(self.portfolio_heat, 2),
            "max_portfolio_heat": self.max_portfolio_heat,
            "heat_percent_of_limit": round(self.heat_percent_of_limit, 2),
            "total_unrealized_pnl": round(self.total_unrealized_pnl, 2),
            "position_count": self.position_count,
            "drawdown_current": round(self.drawdown_current, 2),
            "drawdown_max": round(self.drawdown_max, 2),
            "risk_level": self.risk_level.value,
            "can_open_more": self.can_open_more,
            "margin_usage_percent": round(self.margin_usage_percent, 2),
            "timestamp": self.timestamp.isoformat(),
        }


class PositionSizer:
    """
    Калькулятор размера позиции.
    
    Методы:
    1. Fixed Percent Risk - фиксированный % риска на сделку
    2. Volatility Adjusted - корректировка по волатильности
    3. Kelly Criterion - оптимальный размер по формуле Келли
    
    Использование:
        sizer = PositionSizer(balance=10000, risk_per_trade=2.0)
        
        # Рассчитать размер позиции
        size = sizer.calculate_position_size(
            entry_price=42000,
            stop_loss=41000,
            leverage=10,
        )
    """
    
    def __init__(
        self,
        balance: float,
        risk_per_trade: float = 2.0,  # % от баланса
        max_position_size: float = 20.0,  # % от баланса
        min_position_size: float = 10.0,  # Минимум в USDT
    ):
        """
        Args:
            balance: Общий баланс в USDT
            risk_per_trade: Риск на сделку в % от баланса
            max_position_size: Максимальный размер позиции в % от баланса
            min_position_size: Минимальный размер позиции в USDT
        """
        self.balance = balance
        self.risk_per_trade = risk_per_trade
        self.max_position_size = max_position_size
        self.min_position_size = min_position_size
    
    def update_balance(self, balance: float) -> None:
        """Обновить баланс."""
        self.balance = balance
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        leverage: int = 1,
        direction: str = "long",
    ) -> dict:
        """
        Рассчитать размер позиции методом Fixed Percent Risk.
        
        Args:
            entry_price: Цена входа
            stop_loss: Уровень стоп-лосса
            leverage: Плечо
            direction: Направление ("long" или "short")
            
        Returns:
            dict с размерами и метриками
        """
        if entry_price <= 0 or self.balance <= 0:
            return self._empty_result()
        
        # Риск в % от входа
        if direction == "long":
            risk_percent = (entry_price - stop_loss) / entry_price * 100
        else:
            risk_percent = (stop_loss - entry_price) / entry_price * 100
        
        if risk_percent <= 0:
            return self._empty_result()
        
        # Максимальный риск в USDT
        max_risk_usd = self.balance * self.risk_per_trade / 100
        
        # Размер позиции (notional value)
        position_size = max_risk_usd / (risk_percent / 100)
        
        # Применяем плечо (требуемая маржа)
        required_margin = position_size / leverage
        
        # Проверяем лимиты
        max_pos = self.balance * self.max_position_size / 100
        position_size = min(position_size, max_pos)
        position_size = max(position_size, self.min_position_size)
        
        # Количество монет
        quantity = position_size / entry_price
        
        return {
            "position_size": round(position_size, 2),  # Notional value
            "quantity": round(quantity, 8),
            "required_margin": round(required_margin, 2),
            "risk_amount": round(max_risk_usd, 2),
            "risk_percent": round(self.risk_per_trade, 2),
            "sl_distance_percent": round(risk_percent, 2),
            "leverage": leverage,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
        }
    
    def calculate_volatility_adjusted(
        self,
        entry_price: float,
        stop_loss: float,
        atr: float,
        avg_atr: float,
        leverage: int = 1,
        direction: str = "long",
    ) -> dict:
        """
        Рассчитать размер позиции с корректировкой по волатильности.
        
        При высокой волатильности размер уменьшается.
        При низкой - увеличивается.
        """
        # Базовый расчёт
        base = self.calculate_position_size(entry_price, stop_loss, leverage, direction)
        
        if atr <= 0 or avg_atr <= 0:
            return base
        
        # Коэффициент волатильности
        vol_ratio = atr / avg_atr
        
        # Корректировка (обратная зависимость)
        if vol_ratio > 1.3:
            adjustment = 0.7  # Уменьшаем при высокой волатильности
        elif vol_ratio < 0.7:
            adjustment = 1.2  # Увеличиваем при низкой
        else:
            adjustment = 1.0
        
        # Применяем корректировку
        adjusted_size = base["position_size"] * adjustment
        adjusted_size = max(adjusted_size, self.min_position_size)
        adjusted_size = min(adjusted_size, self.balance * self.max_position_size / 100)
        
        base["position_size"] = round(adjusted_size, 2)
        base["quantity"] = round(adjusted_size / entry_price, 8)
        base["required_margin"] = round(adjusted_size / leverage, 2)
        base["volatility_adjustment"] = round(adjustment, 2)
        base["volatility_ratio"] = round(vol_ratio, 2)
        
        return base
    
    def calculate_kelly(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        max_kelly_fraction: float = 0.25,
    ) -> float:
        """
        Рассчитать оптимальный размер по формуле Келли.
        
        Args:
            win_rate: Винрейт (0-1)
            avg_win: Средний выигрыш в %
            avg_loss: Средний проигрыш в % (положительное число)
            max_kelly_fraction: Максимальная доля от полного Келли
            
        Returns:
            Оптимальный % от баланса
        """
        if win_rate <= 0 or win_rate >= 1 or avg_loss <= 0:
            return self.risk_per_trade
        
        # Kelly = W - (1-W)/R, где R = avg_win/avg_loss
        win_loss_ratio = avg_win / avg_loss
        kelly = win_rate - (1 - win_rate) / win_loss_ratio
        
        # Ограничиваем и применяем fraction
        kelly = max(0, kelly)
        kelly = min(kelly, 1.0)
        kelly = kelly * max_kelly_fraction
        
        # Переводим в %
        kelly_percent = kelly * 100
        
        # Ограничиваем разумными пределами
        kelly_percent = min(kelly_percent, self.max_position_size)
        kelly_percent = max(kelly_percent, self.risk_per_trade / 2)
        
        return round(kelly_percent, 2)
    
    def _empty_result(self) -> dict:
        return {
            "position_size": 0,
            "quantity": 0,
            "required_margin": 0,
            "risk_amount": 0,
            "risk_percent": 0,
            "sl_distance_percent": 0,
            "leverage": 1,
            "entry_price": 0,
            "stop_loss": 0,
        }


class PortfolioHeatTracker:
    """
    Трекер общего риска портфеля (Portfolio Heat).
    
    Portfolio Heat = сумма рисков всех открытых позиций
    
    Использование:
        tracker = PortfolioHeatTracker(balance=10000, max_heat=8.0)
        
        # Добавляем позицию
        tracker.add_position(position_risk)
        
        # Проверяем можно ли открыть ещё
        can_add = tracker.can_add_risk(2.0)
        
        # Получаем метрики
        metrics = tracker.get_metrics()
    """
    
    def __init__(
        self,
        balance: float,
        max_heat: float = 8.0,  # Максимальный portfolio heat в %
        max_positions: int = 5,
    ):
        """
        Args:
            balance: Общий баланс в USDT
            max_heat: Максимальный суммарный риск в %
            max_positions: Максимум одновременных позиций
        """
        self.balance = balance
        self.max_heat = max_heat
        self.max_positions = max_positions
        
        self._positions: Dict[str, PositionRisk] = {}
        self._peak_balance: float = balance
        self._max_drawdown: float = 0.0
    
    def update_balance(self, balance: float) -> None:
        """Обновить баланс."""
        self.balance = balance
        
        # Обновляем peak для drawdown
        if balance > self._peak_balance:
            self._peak_balance = balance
    
    def add_position(self, position: PositionRisk) -> bool:
        """
        Добавить позицию в трекинг.
        
        Returns:
            True если позиция добавлена
        """
        if len(self._positions) >= self.max_positions:
            return False
        
        if not self.can_add_risk(position.risk_amount / self.balance * 100):
            return False
        
        self._positions[position.symbol] = position
        return True
    
    def update_position(self, position: PositionRisk) -> None:
        """Обновить позицию."""
        self._positions[position.symbol] = position
    
    def remove_position(self, symbol: str) -> Optional[PositionRisk]:
        """Удалить позицию из трекинга."""
        return self._positions.pop(symbol, None)
    
    def get_position(self, symbol: str) -> Optional[PositionRisk]:
        """Получить позицию."""
        return self._positions.get(symbol)
    
    def clear_positions(self) -> None:
        """Очистить все позиции."""
        self._positions.clear()
    
    @property
    def position_count(self) -> int:
        """Количество открытых позиций."""
        return len(self._positions)
    
    @property
    def current_heat(self) -> float:
        """Текущий portfolio heat в %."""
        if self.balance <= 0:
            return 0.0
        
        total_risk = sum(p.risk_amount for p in self._positions.values())
        return total_risk / self.balance * 100
    
    @property
    def available_heat(self) -> float:
        """Доступный heat для новых позиций в %."""
        return max(0, self.max_heat - self.current_heat)
    
    @property
    def total_unrealized_pnl(self) -> float:
        """Общий нереализованный PnL."""
        return sum(p.unrealized_pnl_amount for p in self._positions.values())
    
    @property
    def current_drawdown(self) -> float:
        """Текущая просадка от пика в %."""
        if self._peak_balance <= 0:
            return 0.0
        
        current = self.balance + self.total_unrealized_pnl
        drawdown = (self._peak_balance - current) / self._peak_balance * 100
        
        if drawdown > self._max_drawdown:
            self._max_drawdown = drawdown
        
        return max(0, drawdown)
    
    def can_add_risk(self, risk_percent: float) -> bool:
        """Проверить можно ли добавить риск."""
        return self.current_heat + risk_percent <= self.max_heat
    
    def can_open_position(self) -> Tuple[bool, str]:
        """
        Проверить можно ли открыть новую позицию.
        
        Returns:
            (can_open, reason)
        """
        if self.position_count >= self.max_positions:
            return False, f"Max positions reached ({self.max_positions})"
        
        if self.current_heat >= self.max_heat:
            return False, f"Portfolio heat at limit ({self.max_heat}%)"
        
        return True, "OK"
    
    def get_risk_level(self) -> RiskLevel:
        """Определить уровень риска."""
        heat = self.current_heat
        
        if heat <= 3:
            return RiskLevel.LOW
        elif heat <= 5:
            return RiskLevel.NORMAL
        elif heat <= 8:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def get_metrics(self) -> PortfolioRiskMetrics:
        """Получить метрики риска портфеля."""
        used_margin = sum(p.notional_value for p in self._positions.values())
        
        return PortfolioRiskMetrics(
            total_balance=self.balance,
            used_margin=used_margin,
            free_margin=self.balance - used_margin,
            portfolio_heat=self.current_heat,
            max_portfolio_heat=self.max_heat,
            total_unrealized_pnl=self.total_unrealized_pnl,
            position_count=self.position_count,
            drawdown_current=self.current_drawdown,
            drawdown_max=self._max_drawdown,
            risk_level=self.get_risk_level(),
        )
    
    def get_position_list(self) -> List[PositionRisk]:
        """Получить список всех позиций."""
        return list(self._positions.values())
    
    def get_positions_by_risk(self) -> List[PositionRisk]:
        """Получить позиции, отсортированные по риску (от большего)."""
        return sorted(
            self._positions.values(),
            key=lambda x: x.risk_amount,
            reverse=True,
        )


@dataclass
class RiskLimits:
    """Конфигурация лимитов риска."""
    
    max_positions: int = 5
    max_portfolio_heat: float = 8.0  # %
    risk_per_trade: float = 2.0  # %
    max_position_size: float = 20.0  # % от баланса
    max_per_sector: int = 2
    correlation_threshold: float = 0.7
    max_drawdown: float = 15.0  # %
    
    def to_dict(self) -> dict:
        return {
            "max_positions": self.max_positions,
            "max_portfolio_heat": self.max_portfolio_heat,
            "risk_per_trade": self.risk_per_trade,
            "max_position_size": self.max_position_size,
            "max_per_sector": self.max_per_sector,
            "correlation_threshold": self.correlation_threshold,
            "max_drawdown": self.max_drawdown,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "RiskLimits":
        return cls(
            max_positions=data.get("max_positions", 5),
            max_portfolio_heat=data.get("max_portfolio_heat", 8.0),
            risk_per_trade=data.get("risk_per_trade", 2.0),
            max_position_size=data.get("max_position_size", 20.0),
            max_per_sector=data.get("max_per_sector", 2),
            correlation_threshold=data.get("correlation_threshold", 0.7),
            max_drawdown=data.get("max_drawdown", 15.0),
        )
