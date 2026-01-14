"""
VELAS - Генератор сигналов.

Обрабатывает индикаторы и создаёт торговые сигналы.
"""

from typing import Optional, Dict, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

import pandas as pd

from .velas_core import VelasIndicator, VelasSignal, VelasParams

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS & TYPES для тестов
# =============================================================================

class SignalType(str, Enum):
    """Тип сигнала."""
    LONG = "LONG"
    SHORT = "SHORT"


class SignalStrength(str, Enum):
    """Сила сигнала."""
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


@dataclass
class FilterConfig:
    """Конфигурация фильтров сигналов."""
    volume_enabled: bool = True
    volume_multiplier: float = 1.5
    rsi_enabled: bool = True
    rsi_period: int = 14
    rsi_long_level: int = 30
    rsi_short_level: int = 70
    adx_enabled: bool = True
    adx_period: int = 14
    adx_min_level: int = 20


@dataclass
class Signal:
    """Базовый сигнал для тестов и внутренней логики."""
    symbol: str
    signal_type: SignalType
    timeframe: str
    entry_price: float
    sl_price: float
    tp_prices: List[float] = field(default_factory=list)
    strength: SignalStrength = SignalStrength.MEDIUM
    confidence: float = 0.5
    volatility_regime: str = "normal"
    preset_id: str = "default"
    filters_passed: List[str] = field(default_factory=list)
    filters_failed: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def side(self) -> str:
        """Направление сделки."""
        return self.signal_type.value


@dataclass
class TradingSignal:
    """Торговый сигнал для отправки."""
    symbol: str
    side: str  # LONG / SHORT
    timeframe: str
    entry_price: float
    sl_price: float
    tp1_price: float
    tp2_price: float
    tp3_price: float
    tp4_price: float
    tp5_price: float
    tp6_price: float
    confidence: float
    volatility_regime: str
    preset_id: str
    created_at: datetime


class SignalGenerator:
    """Генератор торговых сигналов."""
    
    def __init__(
        self,
        min_confidence: float = 0.6,
        signal_expiry_minutes: int = 30,
    ):
        self.min_confidence = min_confidence
        self.signal_expiry_minutes = signal_expiry_minutes
        
        # Активные сигналы
        self.active_signals: Dict[str, TradingSignal] = {}
        
        # Индикаторы для каждой пары
        self.indicators: Dict[str, VelasIndicator] = {}
    
    def get_or_create_indicator(
        self, 
        symbol: str, 
        params: Optional[VelasParams] = None
    ) -> VelasIndicator:
        """Получить или создать индикатор для пары."""
        key = f"{symbol}"
        
        if key not in self.indicators:
            self.indicators[key] = VelasIndicator(params)
        
        return self.indicators[key]
    
    def check_signal(
        self,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame,
        params: Optional[VelasParams] = None,
        preset_id: str = "default",
    ) -> Optional[TradingSignal]:
        """Проверить наличие сигнала для пары."""
        
        if df is None or len(df) < 100:
            return None
        
        indicator = self.get_or_create_indicator(symbol, params)
        
        # Детекция сигнала
        velas_signal = indicator.detect_signal(df)
        
        if not velas_signal:
            return None
        
        # Проверка уверенности
        if velas_signal.strength < self.min_confidence:
            logger.debug(f"{symbol}: сигнал отклонён (низкая уверенность: {velas_signal.strength:.2f})")
            return None
        
        # Режим волатильности
        volatility = indicator.get_volatility_regime(df)
        
        # Создание сигнала
        signal = TradingSignal(
            symbol=symbol,
            side=velas_signal.direction,
            timeframe=timeframe,
            entry_price=velas_signal.entry_price,
            sl_price=velas_signal.sl_price,
            tp1_price=velas_signal.tp_levels[0],
            tp2_price=velas_signal.tp_levels[1],
            tp3_price=velas_signal.tp_levels[2],
            tp4_price=velas_signal.tp_levels[3],
            tp5_price=velas_signal.tp_levels[4],
            tp6_price=velas_signal.tp_levels[5],
            confidence=velas_signal.strength,
            volatility_regime=volatility,
            preset_id=preset_id,
            created_at=datetime.utcnow(),
        )
        
        # Проверка на дубликат
        signal_key = f"{symbol}_{timeframe}"
        if signal_key in self.active_signals:
            existing = self.active_signals[signal_key]
            age = (datetime.utcnow() - existing.created_at).total_seconds() / 60
            
            if age < self.signal_expiry_minutes:
                logger.debug(f"{symbol}: сигнал уже активен (возраст: {age:.1f} мин)")
                return None
        
        # Сохранение сигнала
        self.active_signals[signal_key] = signal
        
        logger.info(f"🔔 Новый сигнал: {symbol} {velas_signal.direction} @ {velas_signal.entry_price}")
        
        return signal
    
    def clear_expired_signals(self):
        """Очистка просроченных сигналов."""
        now = datetime.utcnow()
        expired = []
        
        for key, signal in self.active_signals.items():
            age = (now - signal.created_at).total_seconds() / 60
            if age > self.signal_expiry_minutes:
                expired.append(key)
        
        for key in expired:
            del self.active_signals[key]
            logger.debug(f"Сигнал удалён (истёк): {key}")
    
    def get_active_signals(self) -> List[TradingSignal]:
        """Получить список активных сигналов."""
        self.clear_expired_signals()
        return list(self.active_signals.values())


# Фильтры для сигналов
class SignalFilters:
    """Фильтры для отсеивания некачественных сигналов."""
    
    @staticmethod
    def volume_filter(df: pd.DataFrame, multiplier: float = 1.5) -> bool:
        """Фильтр по объёму: объём должен быть выше среднего."""
        if "volume" not in df.columns:
            return True
        
        avg_volume = df["volume"].rolling(20).mean().iloc[-1]
        current_volume = df["volume"].iloc[-1]
        
        return current_volume >= avg_volume * multiplier
    
    @staticmethod
    def rsi_filter(
        df: pd.DataFrame, 
        period: int = 14,
        long_level: int = 30,
        short_level: int = 70,
        direction: str = "LONG",
    ) -> bool:
        """Фильтр по RSI."""
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        if direction == "LONG":
            return current_rsi < long_level  # RSI должен быть низким для LONG
        else:
            return current_rsi > short_level  # RSI должен быть высоким для SHORT
    
    @staticmethod
    def adx_filter(df: pd.DataFrame, period: int = 14, min_level: int = 20) -> bool:
        """Фильтр по ADX: тренд должен быть достаточно сильным."""
        high = df["high"]
        low = df["low"]
        close = df["close"]
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        tr = pd.concat([
            high - low,
            abs(high - close.shift(1)),
            abs(low - close.shift(1))
        ], axis=1).max(axis=1)
        
        atr = tr.rolling(period).mean()
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return adx.iloc[-1] >= min_level
