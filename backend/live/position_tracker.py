"""
VELAS Position Tracker - отслеживание позиций в реальном времени.

Ответственность:
- Мониторинг открытых позиций
- Проверка достижения TP/SL
- Обновление стопов (каскад, БУ)
- Генерация уведомлений
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Callable, Tuple, Any
from enum import Enum

# Core imports
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])

from backend.portfolio import Position, PositionStatus, PortfolioManager


logger = logging.getLogger(__name__)


class PositionEvent(Enum):
    """Тип события позиции."""
    OPENED = "opened"
    TP_HIT = "tp_hit"
    SL_MOVED = "sl_moved"
    BREAKEVEN = "breakeven"
    CLOSED_TP = "closed_tp"
    CLOSED_SL = "closed_sl"
    CLOSED_SIGNAL = "closed_signal"
    CLOSED_MANUAL = "closed_manual"
    PRICE_UPDATE = "price_update"


@dataclass
class TrackingEvent:
    """Событие трекинга позиции."""
    
    event_type: PositionEvent
    position: Position
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Детали события
    tp_index: int = 0           # Для TP_HIT
    tp_price: float = 0.0
    old_sl: float = 0.0         # Для SL_MOVED
    new_sl: float = 0.0
    close_price: float = 0.0    # Для CLOSED_*
    pnl_amount: float = 0.0
    pnl_percent: float = 0.0
    message: str = ""
    
    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type.value,
            "symbol": self.position.symbol,
            "direction": self.position.direction,
            "timestamp": self.timestamp.isoformat(),
            "tp_index": self.tp_index,
            "tp_price": self.tp_price,
            "old_sl": self.old_sl,
            "new_sl": self.new_sl,
            "close_price": self.close_price,
            "pnl_amount": round(self.pnl_amount, 2),
            "pnl_percent": round(self.pnl_percent, 2),
            "message": self.message,
            "signal_id": self.position.signal_id,
        }


class PositionTracker:
    """
    Трекер позиций в реальном времени.
    
    Использование:
        tracker = PositionTracker(portfolio_manager)
        
        # Подписываемся на события
        tracker.on_event = lambda event: print(f"Event: {event}")
        
        # Обновляем цену
        events = tracker.update_price("BTCUSDT", 42500)
        
        # Проверяем все позиции
        all_events = tracker.check_all_positions(prices)
    """
    
    # Распределение позиции по TP (из Pine Script)
    DEFAULT_TP_DISTRIBUTION = [17, 17, 17, 17, 16, 16]  # 100%
    
    def __init__(
        self,
        portfolio_manager: PortfolioManager,
        cascade_stop: bool = True,
        breakeven_after_tp: int = 1,
    ):
        """
        Args:
            portfolio_manager: Менеджер портфеля
            cascade_stop: Использовать каскадный стоп
            breakeven_after_tp: После какого TP переводить в БУ
        """
        self.portfolio = portfolio_manager
        self.cascade_stop = cascade_stop
        self.breakeven_after_tp = breakeven_after_tp
        
        # Callback для событий
        self.on_event: Optional[Callable[[TrackingEvent], None]] = None
        
        # История событий
        self._event_history: List[TrackingEvent] = []
        self._max_history = 1000
    
    def _emit_event(self, event: TrackingEvent) -> None:
        """Отправить событие."""
        self._event_history.append(event)
        
        # Ограничиваем историю
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # Вызываем callback
        if self.on_event:
            try:
                self.on_event(event)
            except Exception as e:
                logger.error(f"Error in on_event callback: {e}")
        
        logger.info(f"Position event: {event.event_type.value} - {event.position.symbol} - {event.message}")
    
    def update_price(
        self,
        symbol: str,
        price: float,
        high: float = None,
        low: float = None,
    ) -> List[TrackingEvent]:
        """
        Обновить цену для позиции и проверить TP/SL.
        
        Args:
            symbol: Символ пары
            price: Текущая цена (close)
            high: Максимум свечи (для проверки TP)
            low: Минимум свечи (для проверки SL)
            
        Returns:
            Список событий
        """
        position = self.portfolio.get_position(symbol)
        if position is None or not position.is_open:
            return []
        
        events = []
        
        # Если high/low не указаны, используем price
        if high is None:
            high = price
        if low is None:
            low = price
        
        # Обновляем текущую цену
        position.update_price(price)
        
        # Проверяем TP
        tp_events = self._check_tp_levels(position, high, low)
        events.extend(tp_events)
        
        # Проверяем SL (если позиция ещё открыта)
        if position.is_open:
            sl_event = self._check_sl(position, high, low)
            if sl_event:
                events.append(sl_event)
        
        return events
    
    def _check_tp_levels(
        self,
        position: Position,
        high: float,
        low: float,
    ) -> List[TrackingEvent]:
        """Проверить достижение TP уровней."""
        events = []
        
        for i, tp_price in enumerate(position.tp_prices):
            tp_index = i + 1
            
            # Пропускаем уже достигнутые
            if tp_index in position.tp_hits:
                continue
            
            # Проверяем достижение
            hit = False
            if position.is_long and high >= tp_price:
                hit = True
            elif not position.is_long and low <= tp_price:
                hit = True
            
            if hit:
                # Рассчитываем PnL для этой части
                if position.is_long:
                    pnl_percent = (tp_price - position.entry_price) / position.entry_price * 100
                else:
                    pnl_percent = (position.entry_price - tp_price) / position.entry_price * 100
                
                # Доля позиции для этого TP
                tp_position = self.DEFAULT_TP_DISTRIBUTION[i] if i < len(self.DEFAULT_TP_DISTRIBUTION) else 16
                pnl_amount = position.notional_value * tp_position / 100 * pnl_percent / 100
                
                # Записываем в портфель
                self.portfolio.record_tp_hit(
                    symbol=position.symbol,
                    tp_index=tp_index,
                    close_percent=tp_position,
                    realized_pnl=pnl_amount,
                )
                
                # Создаём событие
                event = TrackingEvent(
                    event_type=PositionEvent.TP_HIT,
                    position=position,
                    tp_index=tp_index,
                    tp_price=tp_price,
                    pnl_amount=pnl_amount,
                    pnl_percent=pnl_percent,
                    message=f"TP{tp_index} hit @ {tp_price} (+{pnl_percent:.2f}%)",
                )
                events.append(event)
                self._emit_event(event)
                
                # Обновляем стоп
                sl_event = self._update_stop_after_tp(position, tp_index)
                if sl_event:
                    events.append(sl_event)
                
                # Если достигнут последний TP - закрываем
                if tp_index == 6 or position.position_remaining <= 0:
                    close_event = self._close_position(
                        position=position,
                        close_price=tp_price,
                        event_type=PositionEvent.CLOSED_TP,
                        reason="All TP hit",
                    )
                    events.append(close_event)
                    break
        
        return events
    
    def _update_stop_after_tp(
        self,
        position: Position,
        tp_hit: int,
    ) -> Optional[TrackingEvent]:
        """Обновить стоп после достижения TP."""
        old_sl = position.current_sl
        new_sl = old_sl
        event_type = PositionEvent.SL_MOVED
        
        if not self.cascade_stop:
            return None
        
        # Каскадная логика
        if tp_hit == 1:
            # После TP1 → SL = Entry (Breakeven)
            new_sl = position.entry_price
            event_type = PositionEvent.BREAKEVEN
        else:
            # После TPn → SL = TP(n-1)
            prev_tp_idx = tp_hit - 2  # -1 для индекса, -1 для предыдущего
            if 0 <= prev_tp_idx < len(position.tp_prices):
                new_sl = position.tp_prices[prev_tp_idx]
        
        # Стоп может только улучшаться
        if position.is_long:
            new_sl = max(old_sl, new_sl)
        else:
            new_sl = min(old_sl, new_sl)
        
        # Если стоп изменился
        if new_sl != old_sl:
            self.portfolio.update_position_sl(position.symbol, new_sl)
            
            message = f"SL moved: {old_sl:.4f} → {new_sl:.4f}"
            if event_type == PositionEvent.BREAKEVEN:
                message = f"Breakeven: SL moved to entry {new_sl:.4f}"
            
            event = TrackingEvent(
                event_type=event_type,
                position=position,
                old_sl=old_sl,
                new_sl=new_sl,
                message=message,
            )
            self._emit_event(event)
            return event
        
        return None
    
    def _check_sl(
        self,
        position: Position,
        high: float,
        low: float,
    ) -> Optional[TrackingEvent]:
        """Проверить достижение Stop Loss."""
        sl_hit = False
        
        if position.is_long and low <= position.current_sl:
            sl_hit = True
        elif not position.is_long and high >= position.current_sl:
            sl_hit = True
        
        if sl_hit:
            return self._close_position(
                position=position,
                close_price=position.current_sl,
                event_type=PositionEvent.CLOSED_SL,
                reason="Stop Loss hit",
            )
        
        return None
    
    def _close_position(
        self,
        position: Position,
        close_price: float,
        event_type: PositionEvent,
        reason: str,
    ) -> TrackingEvent:
        """Закрыть позицию."""
        # Рассчитываем финальный PnL
        if position.is_long:
            pnl_percent = (close_price - position.entry_price) / position.entry_price * 100
        else:
            pnl_percent = (position.entry_price - close_price) / position.entry_price * 100
        
        remaining_notional = position.notional_value * position.position_remaining / 100
        pnl_amount = remaining_notional * pnl_percent / 100
        
        # Закрываем в портфеле
        closed_position = self.portfolio.close_position(
            symbol=position.symbol,
            close_price=close_price,
            reason=reason,
            realized_pnl=pnl_amount,
        )
        
        # Создаём событие
        total_pnl = position.realized_pnl + pnl_amount
        
        event = TrackingEvent(
            event_type=event_type,
            position=position,
            close_price=close_price,
            pnl_amount=total_pnl,
            pnl_percent=total_pnl / position.notional_value * 100 if position.notional_value > 0 else 0,
            message=f"{reason} @ {close_price} (Total PnL: {total_pnl:.2f})",
        )
        self._emit_event(event)
        
        return event
    
    def close_by_signal(
        self,
        symbol: str,
        close_price: float,
    ) -> Optional[TrackingEvent]:
        """Закрыть позицию противоположным сигналом."""
        position = self.portfolio.get_position(symbol)
        if position is None or not position.is_open:
            return None
        
        return self._close_position(
            position=position,
            close_price=close_price,
            event_type=PositionEvent.CLOSED_SIGNAL,
            reason="Opposite signal",
        )
    
    def close_manual(
        self,
        symbol: str,
        close_price: float,
    ) -> Optional[TrackingEvent]:
        """Закрыть позицию вручную."""
        position = self.portfolio.get_position(symbol)
        if position is None or not position.is_open:
            return None
        
        return self._close_position(
            position=position,
            close_price=close_price,
            event_type=PositionEvent.CLOSED_MANUAL,
            reason="Manual close",
        )
    
    def check_all_positions(
        self,
        prices: Dict[str, dict],
    ) -> List[TrackingEvent]:
        """
        Проверить все позиции.
        
        Args:
            prices: Словарь {symbol: {"price": x, "high": y, "low": z}}
            
        Returns:
            Список событий
        """
        all_events = []
        
        for position in self.portfolio.get_all_positions():
            if position.symbol in prices:
                p = prices[position.symbol]
                events = self.update_price(
                    symbol=position.symbol,
                    price=p.get("price", p.get("close", 0)),
                    high=p.get("high"),
                    low=p.get("low"),
                )
                all_events.extend(events)
        
        return all_events
    
    def get_event_history(
        self,
        symbol: str = None,
        event_type: PositionEvent = None,
        limit: int = 100,
    ) -> List[TrackingEvent]:
        """Получить историю событий."""
        events = self._event_history
        
        if symbol:
            events = [e for e in events if e.position.symbol == symbol]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events[-limit:]
    
    def get_open_positions_summary(self) -> List[dict]:
        """Получить сводку по открытым позициям."""
        summary = []
        
        for position in self.portfolio.get_all_positions():
            summary.append({
                "symbol": position.symbol,
                "direction": position.direction,
                "entry_price": position.entry_price,
                "current_price": position.current_price,
                "current_sl": position.current_sl,
                "tp_hits": len(position.tp_hits),
                "position_remaining": position.position_remaining,
                "unrealized_pnl_percent": round(position.unrealized_pnl_percent, 2),
                "unrealized_pnl_amount": round(position.unrealized_pnl_amount, 2),
                "signal_id": position.signal_id,
            })
        
        return summary
