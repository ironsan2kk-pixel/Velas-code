"""
VELAS TP/SL Manager - управление тейк-профитами и стоп-лоссами.

Особенности:
- 6 уровней TP с распределением позиции
- Каскадный стоп (TP1→Entry, TP2→TP1, ...)
- Перевод в БУ после достижения указанного TP
- Адаптивные TP/SL (на основе ATR или волатильности)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple, Dict
import numpy as np

from .signals import Signal, SignalType


class StopManagement(Enum):
    """Режим управления стоп-лоссом."""
    NONE = "none"           # Стоп не двигается
    BREAKEVEN = "breakeven" # Стоп в БУ после указанного TP
    CASCADE = "cascade"     # Каскадный: TP1→Entry, TP2→TP1, ...


class AdaptiveMode(Enum):
    """Режим адаптивных TP/SL."""
    OFF = "off"           # Фиксированные проценты
    VOLATILITY = "volatility"  # На основе волатильности (стандартное отклонение)
    ATR = "atr"           # На основе ATR


@dataclass
class TPSLConfig:
    """Конфигурация TP/SL уровней."""
    
    # Проценты от входа (по умолчанию как в Pine Script)
    tp1_percent: float = 1.0
    tp2_percent: float = 2.0
    tp3_percent: float = 3.0
    tp4_percent: float = 4.0
    tp5_percent: float = 7.5
    tp6_percent: float = 14.0
    sl_percent: float = 8.5
    
    # Распределение позиции по TP (в процентах, сумма = 100%)
    tp1_position: float = 17.0
    tp2_position: float = 17.0
    tp3_position: float = 17.0
    tp4_position: float = 17.0
    tp5_position: float = 16.0
    tp6_position: float = 16.0
    
    # Управление стопом
    stop_management: StopManagement = StopManagement.CASCADE
    be_after_tp: int = 4  # После какого TP переводить в БУ (если BREAKEVEN)
    
    # Адаптивные уровни
    adaptive_mode: AdaptiveMode = AdaptiveMode.OFF
    atr_multiplier: float = 1.0  # Множитель для ATR-режима
    
    def __post_init__(self):
        self._normalize_positions()
    
    def _normalize_positions(self):
        """Нормализовать распределение позиции до 100%."""
        total = sum([
            self.tp1_position, self.tp2_position, self.tp3_position,
            self.tp4_position, self.tp5_position, self.tp6_position
        ])
        if total > 0 and abs(total - 100) > 0.01:
            factor = 100 / total
            self.tp1_position *= factor
            self.tp2_position *= factor
            self.tp3_position *= factor
            self.tp4_position *= factor
            self.tp5_position *= factor
            self.tp6_position *= factor
    
    @property
    def tp_percents(self) -> List[float]:
        """Список процентов TP."""
        return [
            self.tp1_percent, self.tp2_percent, self.tp3_percent,
            self.tp4_percent, self.tp5_percent, self.tp6_percent
        ]
    
    @property
    def tp_positions(self) -> List[float]:
        """Список распределения позиции."""
        return [
            self.tp1_position, self.tp2_position, self.tp3_position,
            self.tp4_position, self.tp5_position, self.tp6_position
        ]
    
    def to_dict(self) -> dict:
        return {
            "tp_percents": self.tp_percents,
            "tp_positions": self.tp_positions,
            "sl_percent": self.sl_percent,
            "stop_management": self.stop_management.value,
            "be_after_tp": self.be_after_tp,
            "adaptive_mode": self.adaptive_mode.value,
            "atr_multiplier": self.atr_multiplier,
        }


@dataclass
class TPLevel:
    """Уровень тейк-профита."""
    
    index: int           # 1-6
    price: float         # Цена уровня
    percent: float       # Процент от входа
    position_percent: float  # Доля позиции для закрытия
    hit: bool = False    # Достигнут ли уровень
    hit_price: float = 0.0  # Цена при достижении
    
    @property
    def name(self) -> str:
        return f"TP{self.index}"


@dataclass 
class TPSLLevels:
    """Полный набор TP/SL уровней для сделки."""
    
    entry_price: float
    is_long: bool
    tp_levels: List[TPLevel] = field(default_factory=list)
    sl_price: float = 0.0
    current_sl: float = 0.0  # Текущий SL (может быть сдвинут)
    
    def __post_init__(self):
        if self.current_sl == 0:
            self.current_sl = self.sl_price
    
    @property
    def tp_prices(self) -> List[float]:
        """Список цен TP."""
        return [tp.price for tp in self.tp_levels]
    
    @property
    def hit_count(self) -> int:
        """Количество достигнутых TP."""
        return sum(1 for tp in self.tp_levels if tp.hit)
    
    @property
    def remaining_position(self) -> float:
        """Оставшаяся позиция после частичных закрытий."""
        closed = sum(tp.position_percent for tp in self.tp_levels if tp.hit)
        return max(0, 100 - closed)
    
    def to_dict(self) -> dict:
        return {
            "entry_price": self.entry_price,
            "is_long": self.is_long,
            "tp_levels": [
                {
                    "index": tp.index,
                    "price": tp.price,
                    "percent": tp.percent,
                    "position_percent": tp.position_percent,
                    "hit": tp.hit,
                }
                for tp in self.tp_levels
            ],
            "sl_price": self.sl_price,
            "current_sl": self.current_sl,
            "hit_count": self.hit_count,
            "remaining_position": self.remaining_position,
        }


class TPSLManager:
    """
    Менеджер TP/SL уровней.
    
    Использование:
        manager = TPSLManager(config)
        levels = manager.calculate_levels(signal)
        
        # Проверка на каждом баре
        hit_tps, hit_sl = manager.check_levels(levels, high, low, close)
    """
    
    def __init__(self, config: TPSLConfig = None):
        self.config = config or TPSLConfig()
    
    def calculate_adaptive_percents(
        self,
        atr: float,
        close: float,
        volatility: float = None,
    ) -> Tuple[List[float], float]:
        """
        Рассчитать адаптивные проценты TP/SL.
        
        Args:
            atr: Текущий ATR
            close: Текущая цена закрытия
            volatility: Волатильность (для режима VOLATILITY)
            
        Returns:
            (tp_percents, sl_percent) - адаптированные проценты
        """
        if self.config.adaptive_mode == AdaptiveMode.OFF:
            return self.config.tp_percents, self.config.sl_percent
        
        base_tp = self.config.tp_percents
        base_sl = self.config.sl_percent
        
        if close == 0:
            return base_tp, base_sl
        
        if self.config.adaptive_mode == AdaptiveMode.ATR:
            # TP/SL на основе ATR
            atr_ratio = atr / close
            multiplier = self.config.atr_multiplier
            
            tp_percents = [p * atr_ratio * multiplier * 100 for p in base_tp]
            sl_percent = base_sl * atr_ratio * multiplier * 100
            
        elif self.config.adaptive_mode == AdaptiveMode.VOLATILITY:
            # TP/SL на основе волатильности
            if volatility is None or volatility == 0:
                return base_tp, base_sl
            
            vol_ratio = volatility / close
            
            tp_percents = [p * vol_ratio * 100 for p in base_tp]
            sl_percent = base_sl * vol_ratio * 100
        else:
            tp_percents = base_tp
            sl_percent = base_sl
        
        return tp_percents, sl_percent
    
    def calculate_levels(
        self,
        signal: Signal,
        atr: float = None,
        volatility: float = None,
    ) -> TPSLLevels:
        """
        Рассчитать уровни TP/SL для сигнала.
        
        Args:
            signal: Торговый сигнал
            atr: ATR (для адаптивных уровней)
            volatility: Волатильность (для адаптивных уровней)
            
        Returns:
            TPSLLevels с рассчитанными уровнями
        """
        entry = signal.entry_price
        is_long = signal.is_long
        
        # Получаем проценты (адаптивные или фиксированные)
        if self.config.adaptive_mode != AdaptiveMode.OFF and atr is not None:
            tp_percents, sl_percent = self.calculate_adaptive_percents(atr, entry, volatility)
        else:
            tp_percents = self.config.tp_percents
            sl_percent = self.config.sl_percent
        
        tp_positions = self.config.tp_positions
        
        # Рассчитываем цены TP
        tp_levels = []
        for i, (tp_pct, pos_pct) in enumerate(zip(tp_percents, tp_positions), 1):
            if is_long:
                price = entry * (1 + tp_pct / 100)
            else:
                price = entry * (1 - tp_pct / 100)
            
            tp_levels.append(TPLevel(
                index=i,
                price=round(price, 8),
                percent=tp_pct,
                position_percent=pos_pct,
            ))
        
        # Рассчитываем SL
        if is_long:
            sl_price = entry * (1 - sl_percent / 100)
        else:
            sl_price = entry * (1 + sl_percent / 100)
        
        return TPSLLevels(
            entry_price=entry,
            is_long=is_long,
            tp_levels=tp_levels,
            sl_price=round(sl_price, 8),
            current_sl=round(sl_price, 8),
        )
    
    def check_levels(
        self,
        levels: TPSLLevels,
        high: float,
        low: float,
        close: float,
    ) -> Tuple[List[TPLevel], bool]:
        """
        Проверить достижение уровней на текущем баре.
        
        Args:
            levels: Уровни TP/SL
            high: Максимум бара
            low: Минимум бара
            close: Закрытие бара
            
        Returns:
            (список достигнутых TP, достигнут ли SL)
        """
        hit_tps = []
        hit_sl = False
        
        is_long = levels.is_long
        
        # Проверяем TP уровни
        for tp in levels.tp_levels:
            if tp.hit:
                continue
            
            if is_long and high >= tp.price:
                tp.hit = True
                tp.hit_price = tp.price
                hit_tps.append(tp)
            elif not is_long and low <= tp.price:
                tp.hit = True
                tp.hit_price = tp.price
                hit_tps.append(tp)
        
        # Обновляем SL по каскадной логике
        if hit_tps and self.config.stop_management == StopManagement.CASCADE:
            levels.current_sl = self._calculate_cascade_sl(levels)
        elif hit_tps and self.config.stop_management == StopManagement.BREAKEVEN:
            levels.current_sl = self._calculate_breakeven_sl(levels)
        
        # Проверяем SL
        if is_long and low <= levels.current_sl:
            hit_sl = True
        elif not is_long and high >= levels.current_sl:
            hit_sl = True
        
        return hit_tps, hit_sl
    
    def _calculate_cascade_sl(self, levels: TPSLLevels) -> float:
        """
        Рассчитать каскадный SL.
        
        Логика:
        - После TP1 → SL = Entry
        - После TP2 → SL = TP1
        - После TP3 → SL = TP2
        - и т.д.
        """
        hit_count = levels.hit_count
        is_long = levels.is_long
        
        if hit_count == 0:
            return levels.sl_price
        
        # После TP1 → SL = Entry
        if hit_count == 1:
            new_sl = levels.entry_price
        else:
            # После TPn → SL = TP(n-1)
            prev_tp_idx = hit_count - 1  # 0-indexed
            if prev_tp_idx < len(levels.tp_levels):
                new_sl = levels.tp_levels[prev_tp_idx - 1].price if prev_tp_idx > 0 else levels.entry_price
            else:
                new_sl = levels.entry_price
        
        # Стоп может только улучшаться
        if is_long:
            return max(levels.current_sl, new_sl)
        else:
            return min(levels.current_sl, new_sl)
    
    def _calculate_breakeven_sl(self, levels: TPSLLevels) -> float:
        """
        Рассчитать SL для режима Breakeven.
        
        После достижения be_after_tp стоп переводится на вход.
        """
        hit_count = levels.hit_count
        is_long = levels.is_long
        
        if hit_count >= self.config.be_after_tp:
            new_sl = levels.entry_price
            
            if is_long:
                return max(levels.current_sl, new_sl)
            else:
                return min(levels.current_sl, new_sl)
        
        return levels.current_sl
    
    def calculate_trade_pnl(
        self,
        levels: TPSLLevels,
        exit_price: float,
        was_sl: bool = False,
    ) -> Tuple[float, Dict[str, float]]:
        """
        Рассчитать PnL сделки.
        
        Args:
            levels: Уровни TP/SL с информацией о достигнутых TP
            exit_price: Цена выхода
            was_sl: Была ли сделка закрыта по SL
            
        Returns:
            (total_pnl_percent, dict с детализацией по TP)
        """
        entry = levels.entry_price
        is_long = levels.is_long
        
        pnl_details = {}
        total_pnl = 0.0
        position_closed = 0.0
        
        # PnL от каждого достигнутого TP
        for tp in levels.tp_levels:
            if tp.hit:
                if is_long:
                    tp_pnl = (tp.hit_price - entry) / entry * 100
                else:
                    tp_pnl = (entry - tp.hit_price) / entry * 100
                
                weighted_pnl = tp_pnl * (tp.position_percent / 100)
                pnl_details[tp.name] = {
                    "price": tp.hit_price,
                    "pnl_percent": tp_pnl,
                    "position_percent": tp.position_percent,
                    "weighted_pnl": weighted_pnl,
                }
                total_pnl += weighted_pnl
                position_closed += tp.position_percent
        
        # PnL от оставшейся позиции (SL или закрытие)
        remaining = 100 - position_closed
        if remaining > 0:
            if is_long:
                exit_pnl = (exit_price - entry) / entry * 100
            else:
                exit_pnl = (entry - exit_price) / entry * 100
            
            weighted_pnl = exit_pnl * (remaining / 100)
            key = "SL" if was_sl else "EXIT"
            pnl_details[key] = {
                "price": exit_price,
                "pnl_percent": exit_pnl,
                "position_percent": remaining,
                "weighted_pnl": weighted_pnl,
            }
            total_pnl += weighted_pnl
        
        return total_pnl, pnl_details


# Готовые конфигурации для разных режимов волатильности
TPSL_CONFIG_LOW = TPSLConfig(
    tp1_percent=0.8, tp2_percent=1.6, tp3_percent=2.4,
    tp4_percent=3.2, tp5_percent=6.0, tp6_percent=11.2,
    sl_percent=6.8,
    stop_management=StopManagement.CASCADE,
)

TPSL_CONFIG_NORMAL = TPSLConfig(
    tp1_percent=1.0, tp2_percent=2.0, tp3_percent=3.0,
    tp4_percent=4.0, tp5_percent=7.5, tp6_percent=14.0,
    sl_percent=8.5,
    stop_management=StopManagement.CASCADE,
)

TPSL_CONFIG_HIGH = TPSLConfig(
    tp1_percent=1.3, tp2_percent=2.6, tp3_percent=3.9,
    tp4_percent=5.2, tp5_percent=9.75, tp6_percent=18.2,
    sl_percent=10.2,
    stop_management=StopManagement.CASCADE,
)


def get_tpsl_config_for_volatility(volatility_regime: str) -> TPSLConfig:
    """
    Получить конфигурацию TP/SL для режима волатильности.
    
    Args:
        volatility_regime: "low", "normal" или "high"
    """
    configs = {
        "low": TPSL_CONFIG_LOW,
        "normal": TPSL_CONFIG_NORMAL,
        "high": TPSL_CONFIG_HIGH,
    }
    return configs.get(volatility_regime.lower(), TPSL_CONFIG_NORMAL)
