"""
VELAS Trade - модель сделки для бэктестинга.

Trade отслеживает:
- Вход (цена, время, направление)
- Достижение TP уровней
- Изменение SL
- Выход (цена, время, причина)
- PnL
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
import uuid


class TradeStatus(Enum):
    """Статус сделки."""
    OPEN = "open"
    CLOSED_TP = "closed_tp"      # Закрыта по последнему TP
    CLOSED_SL = "closed_sl"      # Закрыта по SL
    CLOSED_SIGNAL = "closed_signal"  # Закрыта противоположным сигналом
    CLOSED_MANUAL = "closed_manual"  # Закрыта вручную


class TradeDirection(Enum):
    """Направление сделки."""
    LONG = "long"
    SHORT = "short"


@dataclass
class TPHit:
    """Информация о достижении TP."""
    
    index: int              # 1-6
    price: float            # Цена TP
    hit_price: float        # Фактическая цена достижения
    timestamp: datetime     # Время достижения
    position_closed: float  # Процент закрытой позиции
    pnl_percent: float      # PnL этой части
    
    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "price": self.price,
            "hit_price": self.hit_price,
            "timestamp": self.timestamp.isoformat(),
            "position_closed": self.position_closed,
            "pnl_percent": self.pnl_percent,
        }


@dataclass
class TradeResult:
    """Результат закрытой сделки."""
    
    status: TradeStatus
    exit_price: float
    exit_timestamp: datetime
    total_pnl_percent: float
    tp_hits: List[TPHit]
    max_profit_percent: float = 0.0  # Максимальная прибыль за время сделки
    max_drawdown_percent: float = 0.0  # Максимальная просадка за время сделки
    duration_bars: int = 0
    
    @property
    def is_profitable(self) -> bool:
        return self.total_pnl_percent > 0
    
    @property
    def reached_tp1(self) -> bool:
        return any(tp.index == 1 for tp in self.tp_hits)
    
    @property
    def reached_tp_count(self) -> int:
        return len(self.tp_hits)
    
    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "exit_price": self.exit_price,
            "exit_timestamp": self.exit_timestamp.isoformat(),
            "total_pnl_percent": self.total_pnl_percent,
            "tp_hits": [tp.to_dict() for tp in self.tp_hits],
            "max_profit_percent": self.max_profit_percent,
            "max_drawdown_percent": self.max_drawdown_percent,
            "duration_bars": self.duration_bars,
            "is_profitable": self.is_profitable,
            "reached_tp1": self.reached_tp1,
            "reached_tp_count": self.reached_tp_count,
        }


@dataclass
class Trade:
    """
    Торговая сделка.
    
    Жизненный цикл:
    1. Создание при сигнале (OPEN)
    2. Обновление на каждом баре (check_bar)
    3. Закрытие (close)
    """
    
    # Идентификация
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    symbol: str = ""
    timeframe: str = ""
    preset_index: int = 0
    
    # Вход
    direction: TradeDirection = TradeDirection.LONG
    entry_price: float = 0.0
    entry_timestamp: datetime = None
    
    # TP/SL уровни
    tp_prices: List[float] = field(default_factory=list)
    tp_positions: List[float] = field(default_factory=list)
    sl_price: float = 0.0
    current_sl: float = 0.0
    
    # Состояние
    status: TradeStatus = TradeStatus.OPEN
    position_remaining: float = 100.0  # Оставшаяся позиция в %
    tp_hits: List[TPHit] = field(default_factory=list)
    
    # Трекинг
    bar_count: int = 0
    max_price: float = 0.0
    min_price: float = float("inf")
    max_profit: float = 0.0
    max_drawdown: float = 0.0
    
    # Результат
    result: Optional[TradeResult] = None
    
    def __post_init__(self):
        if self.current_sl == 0 and self.sl_price > 0:
            self.current_sl = self.sl_price
        if self.entry_timestamp is None:
            self.entry_timestamp = datetime.now()
    
    @property
    def is_long(self) -> bool:
        return self.direction == TradeDirection.LONG
    
    @property
    def is_open(self) -> bool:
        return self.status == TradeStatus.OPEN
    
    @property
    def signal_id(self) -> str:
        """Уникальный ID сигнала в формате Cornix."""
        direction = "Long" if self.is_long else "Short"
        ts = self.entry_timestamp.strftime("%d_%m_%Y_%H_%M")
        return f"#{direction}_{self.symbol}_{ts}"
    
    def check_bar(
        self,
        timestamp: datetime,
        high: float,
        low: float,
        close: float,
        cascade_stop: bool = True,
    ) -> Optional[TradeResult]:
        """
        Проверить бар на достижение TP/SL.
        
        Args:
            timestamp: Время бара
            high: Максимум бара
            low: Минимум бара
            close: Закрытие бара
            cascade_stop: Использовать ли каскадный стоп
            
        Returns:
            TradeResult если сделка закрыта, иначе None
        """
        if not self.is_open:
            return None
        
        self.bar_count += 1
        
        # Обновляем экстремумы
        self.max_price = max(self.max_price, high)
        self.min_price = min(self.min_price, low)
        
        # Считаем текущий unrealized PnL
        if self.is_long:
            current_pnl = (close - self.entry_price) / self.entry_price * 100
            max_pnl = (self.max_price - self.entry_price) / self.entry_price * 100
            min_pnl = (self.min_price - self.entry_price) / self.entry_price * 100
        else:
            current_pnl = (self.entry_price - close) / self.entry_price * 100
            max_pnl = (self.entry_price - self.min_price) / self.entry_price * 100
            min_pnl = (self.entry_price - self.max_price) / self.entry_price * 100
        
        self.max_profit = max(self.max_profit, max_pnl)
        self.max_drawdown = min(self.max_drawdown, min_pnl)
        
        # Проверяем TP уровни
        hit_any_tp = False
        for i, (tp_price, tp_pos) in enumerate(zip(self.tp_prices, self.tp_positions)):
            tp_idx = i + 1
            
            # Пропускаем уже достигнутые
            if any(h.index == tp_idx for h in self.tp_hits):
                continue
            
            # Проверяем достижение
            hit = False
            if self.is_long and high >= tp_price:
                hit = True
            elif not self.is_long and low <= tp_price:
                hit = True
            
            if hit:
                hit_any_tp = True
                
                # Рассчитываем PnL этой части
                if self.is_long:
                    pnl = (tp_price - self.entry_price) / self.entry_price * 100
                else:
                    pnl = (self.entry_price - tp_price) / self.entry_price * 100
                
                # Реальная закрываемая часть (не больше оставшейся)
                actual_pos = min(tp_pos, self.position_remaining)
                
                self.tp_hits.append(TPHit(
                    index=tp_idx,
                    price=tp_price,
                    hit_price=tp_price,
                    timestamp=timestamp,
                    position_closed=actual_pos,
                    pnl_percent=pnl,
                ))
                
                self.position_remaining -= actual_pos
                
                # Все TP достигнуты
                if self.position_remaining <= 0 or tp_idx == 6:
                    return self._close(
                        status=TradeStatus.CLOSED_TP,
                        exit_price=tp_price,
                        timestamp=timestamp,
                    )
        
        # Обновляем SL по каскадной логике
        if hit_any_tp and cascade_stop:
            self._update_cascade_sl()
        
        # Проверяем SL
        sl_hit = False
        if self.is_long and low <= self.current_sl:
            sl_hit = True
        elif not self.is_long and high >= self.current_sl:
            sl_hit = True
        
        if sl_hit:
            return self._close(
                status=TradeStatus.CLOSED_SL,
                exit_price=self.current_sl,
                timestamp=timestamp,
            )
        
        return None
    
    def close_by_signal(self, timestamp: datetime, close_price: float) -> TradeResult:
        """Закрыть сделку противоположным сигналом."""
        return self._close(
            status=TradeStatus.CLOSED_SIGNAL,
            exit_price=close_price,
            timestamp=timestamp,
        )
    
    def close_manual(self, timestamp: datetime, close_price: float) -> TradeResult:
        """Закрыть сделку вручную."""
        return self._close(
            status=TradeStatus.CLOSED_MANUAL,
            exit_price=close_price,
            timestamp=timestamp,
        )
    
    def _update_cascade_sl(self):
        """Обновить SL по каскадной логике."""
        if not self.tp_hits:
            return
        
        hit_count = len(self.tp_hits)
        
        # После TP1 → SL = Entry
        if hit_count == 1:
            new_sl = self.entry_price
        else:
            # После TPn → SL = TP(n-1)
            prev_tp_idx = hit_count - 1
            if prev_tp_idx > 0 and prev_tp_idx <= len(self.tp_prices):
                new_sl = self.tp_prices[prev_tp_idx - 1]
            else:
                new_sl = self.entry_price
        
        # Стоп может только улучшаться
        if self.is_long:
            self.current_sl = max(self.current_sl, new_sl)
        else:
            self.current_sl = min(self.current_sl, new_sl)
    
    def _close(
        self,
        status: TradeStatus,
        exit_price: float,
        timestamp: datetime,
    ) -> TradeResult:
        """Закрыть сделку."""
        self.status = status
        
        # Считаем PnL от каждого TP
        total_pnl = 0.0
        for tp_hit in self.tp_hits:
            weighted_pnl = tp_hit.pnl_percent * (tp_hit.position_closed / 100)
            total_pnl += weighted_pnl
        
        # PnL от оставшейся позиции
        if self.position_remaining > 0:
            if self.is_long:
                exit_pnl = (exit_price - self.entry_price) / self.entry_price * 100
            else:
                exit_pnl = (self.entry_price - exit_price) / self.entry_price * 100
            
            weighted_exit_pnl = exit_pnl * (self.position_remaining / 100)
            total_pnl += weighted_exit_pnl
        
        self.result = TradeResult(
            status=status,
            exit_price=exit_price,
            exit_timestamp=timestamp,
            total_pnl_percent=round(total_pnl, 4),
            tp_hits=self.tp_hits.copy(),
            max_profit_percent=round(self.max_profit, 4),
            max_drawdown_percent=round(self.max_drawdown, 4),
            duration_bars=self.bar_count,
        )
        
        return self.result
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "preset_index": self.preset_index,
            "direction": self.direction.value,
            "entry_price": self.entry_price,
            "entry_timestamp": self.entry_timestamp.isoformat() if self.entry_timestamp else None,
            "tp_prices": self.tp_prices,
            "sl_price": self.sl_price,
            "current_sl": self.current_sl,
            "status": self.status.value,
            "position_remaining": self.position_remaining,
            "tp_hits": [h.to_dict() for h in self.tp_hits],
            "bar_count": self.bar_count,
            "max_profit": self.max_profit,
            "max_drawdown": self.max_drawdown,
            "result": self.result.to_dict() if self.result else None,
        }
    
    @classmethod
    def from_signal(
        cls,
        signal,  # Signal from core.signals
        tpsl_levels,  # TPSLLevels from core.tpsl
    ) -> "Trade":
        """Создать Trade из Signal и TPSLLevels."""
        return cls(
            symbol=signal.symbol,
            timeframe=signal.timeframe,
            preset_index=signal.preset_index,
            direction=TradeDirection.LONG if signal.is_long else TradeDirection.SHORT,
            entry_price=signal.entry_price,
            entry_timestamp=signal.timestamp,
            tp_prices=[tp.price for tp in tpsl_levels.tp_levels],
            tp_positions=[tp.position_percent for tp in tpsl_levels.tp_levels],
            sl_price=tpsl_levels.sl_price,
            current_sl=tpsl_levels.current_sl,
        )
