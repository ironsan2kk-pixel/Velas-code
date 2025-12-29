"""
VELAS - Портфельный менеджер.

Управляет позициями, рисками и корреляциями.
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Открытая позиция."""
    id: int
    symbol: str
    side: str
    entry_price: float
    current_price: float
    sl_price: float
    current_sl: float
    quantity: float
    leverage: int = 10
    position_remaining: float = 100.0
    unrealized_pnl_percent: float = 0.0
    entry_time: datetime = field(default_factory=datetime.utcnow)


@dataclass 
class PortfolioStats:
    """Статистика портфеля."""
    total_balance: float
    available_balance: float
    used_margin: float
    unrealized_pnl: float
    portfolio_heat: float  # Суммарный риск всех позиций
    open_positions_count: int
    max_positions: int


class PortfolioManager:
    """Управление портфелем."""
    
    # Группы коррелированных пар
    CORRELATION_GROUPS = {
        "BTC_related": ["BTCUSDT"],
        "ETH_related": ["ETHUSDT"],
        "Layer1": ["SOLUSDT", "AVAXUSDT", "DOTUSDT", "NEARUSDT", "APTUSDT", "ATOMUSDT"],
        "DeFi": ["UNIUSDT", "LINKUSDT", "ARBUSDT", "OPUSDT"],
        "Meme": ["DOGEUSDT"],
        "Exchange": ["BNBUSDT"],
        "Legacy": ["LTCUSDT", "ETCUSDT"],
        "Other": ["XRPUSDT", "ADAUSDT", "MATICUSDT", "INJUSDT"],
    }
    
    def __init__(
        self,
        initial_balance: float = 10000.0,
        max_positions: int = 5,
        risk_percent: float = 2.0,
        portfolio_heat_limit: float = 15.0,
        correlation_limit: float = 0.7,
    ):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.max_positions = max_positions
        self.risk_percent = risk_percent
        self.portfolio_heat_limit = portfolio_heat_limit
        self.correlation_limit = correlation_limit
        
        # Открытые позиции
        self.positions: Dict[int, Position] = {}
        self._next_id = 1
    
    def can_open_position(self, symbol: str) -> Tuple[bool, str]:
        """Проверка возможности открытия позиции."""
        
        # Проверка лимита позиций
        if len(self.positions) >= self.max_positions:
            return False, f"Достигнут лимит позиций ({self.max_positions})"
        
        # Проверка дубликата
        for pos in self.positions.values():
            if pos.symbol == symbol:
                return False, f"Позиция по {symbol} уже открыта"
        
        # Проверка корреляции
        symbol_group = self._get_correlation_group(symbol)
        for pos in self.positions.values():
            pos_group = self._get_correlation_group(pos.symbol)
            if symbol_group == pos_group and symbol_group not in ["Other"]:
                return False, f"Коррелирующая позиция уже открыта ({pos.symbol})"
        
        # Проверка portfolio heat
        current_heat = self._calculate_portfolio_heat()
        new_heat = current_heat + self.risk_percent
        
        if new_heat > self.portfolio_heat_limit:
            return False, f"Превышен лимит portfolio heat ({new_heat:.1f}% > {self.portfolio_heat_limit}%)"
        
        return True, "OK"
    
    def _get_correlation_group(self, symbol: str) -> str:
        """Определить группу корреляции для пары."""
        for group, symbols in self.CORRELATION_GROUPS.items():
            if symbol in symbols:
                return group
        return "Other"
    
    def _calculate_portfolio_heat(self) -> float:
        """Расчёт текущего portfolio heat."""
        return len(self.positions) * self.risk_percent
    
    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        sl_price: float,
        leverage: int = 10,
    ) -> float:
        """Расчёт размера позиции на основе риска."""
        
        # Риск в USDT
        risk_amount = self.current_balance * (self.risk_percent / 100)
        
        # Расстояние до SL в процентах
        sl_distance_pct = abs(entry_price - sl_price) / entry_price
        
        if sl_distance_pct == 0:
            return 0
        
        # Размер позиции
        position_value = risk_amount / sl_distance_pct
        
        # С учётом плеча
        margin_required = position_value / leverage
        
        # Количество монет
        quantity = position_value / entry_price
        
        return round(quantity, 8)
    
    def open_position(
        self,
        symbol: str,
        side: str,
        entry_price: float,
        sl_price: float,
        leverage: int = 10,
    ) -> Optional[Position]:
        """Открыть новую позицию."""
        
        can_open, reason = self.can_open_position(symbol)
        if not can_open:
            logger.warning(f"Не удалось открыть позицию: {reason}")
            return None
        
        quantity = self.calculate_position_size(symbol, entry_price, sl_price, leverage)
        
        position = Position(
            id=self._next_id,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            current_price=entry_price,
            sl_price=sl_price,
            current_sl=sl_price,
            quantity=quantity,
            leverage=leverage,
        )
        
        self.positions[self._next_id] = position
        self._next_id += 1
        
        logger.info(f"Открыта позиция #{position.id}: {symbol} {side} @ {entry_price}")
        
        return position
    
    def close_position(self, position_id: int, exit_price: float) -> Optional[float]:
        """Закрыть позицию и вернуть PnL."""
        
        if position_id not in self.positions:
            return None
        
        position = self.positions[position_id]
        
        # Расчёт PnL
        if position.side == "LONG":
            pnl_pct = (exit_price - position.entry_price) / position.entry_price * 100
        else:
            pnl_pct = (position.entry_price - exit_price) / position.entry_price * 100
        
        # Обновление баланса
        position_value = position.quantity * position.entry_price
        pnl_usd = position_value * (pnl_pct / 100)
        self.current_balance += pnl_usd
        
        # Удаление позиции
        del self.positions[position_id]
        
        logger.info(f"Закрыта позиция #{position_id}: PnL {pnl_pct:.2f}% (${pnl_usd:.2f})")
        
        return pnl_pct
    
    def update_position_price(self, position_id: int, current_price: float):
        """Обновить текущую цену позиции."""
        if position_id not in self.positions:
            return
        
        position = self.positions[position_id]
        position.current_price = current_price
        
        if position.side == "LONG":
            pnl = (current_price - position.entry_price) / position.entry_price * 100
        else:
            pnl = (position.entry_price - current_price) / position.entry_price * 100
        
        position.unrealized_pnl_percent = round(pnl, 2)
    
    def get_stats(self) -> PortfolioStats:
        """Получить статистику портфеля."""
        
        # Нереализованный PnL
        unrealized_pnl = 0
        for pos in self.positions.values():
            pos_value = pos.quantity * pos.entry_price
            unrealized_pnl += pos_value * (pos.unrealized_pnl_percent / 100)
        
        # Использованная маржа
        used_margin = sum(
            pos.quantity * pos.entry_price / pos.leverage 
            for pos in self.positions.values()
        )
        
        return PortfolioStats(
            total_balance=self.current_balance + unrealized_pnl,
            available_balance=self.current_balance - used_margin,
            used_margin=used_margin,
            unrealized_pnl=unrealized_pnl,
            portfolio_heat=self._calculate_portfolio_heat(),
            open_positions_count=len(self.positions),
            max_positions=self.max_positions,
        )
    
    def get_open_positions(self) -> List[Position]:
        """Получить список открытых позиций."""
        return list(self.positions.values())
