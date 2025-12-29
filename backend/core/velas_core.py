"""
VELAS Core - Расчёт индикатора Velas.

Реализация каналов и триггеров на основе Pine Script "Велас v6".
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class VelasParams:
    """Параметры индикатора Velas."""
    i1: int = 60       # Период 1 (основной)
    i2: int = 14       # Период 2 (RSI-like)
    i3: float = 1.2    # Множитель 1 (ширина канала)
    i4: float = 1.6    # Множитель 2 (внешний канал)
    i5: float = 1.0    # Дополнительный множитель


@dataclass
class VelasChannels:
    """Результат расчёта каналов."""
    upper1: float      # Верхний канал 1
    lower1: float      # Нижний канал 1
    upper2: float      # Верхний канал 2 (внешний)
    lower2: float      # Нижний канал 2 (внешний)
    middle: float      # Средняя линия
    atr: float         # ATR


@dataclass
class VelasSignal:
    """Торговый сигнал Velas."""
    direction: str     # "LONG", "SHORT", "NONE"
    strength: float    # Сила сигнала (0-1)
    entry_price: float
    sl_price: float
    tp_levels: list    # Список TP уровней


class VelasIndicator:
    """Расчёт индикатора Velas."""
    
    def __init__(self, params: Optional[VelasParams] = None):
        self.params = params or VelasParams()
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Расчёт ATR (Average True Range)."""
        high = df["high"]
        low = df["low"]
        close = df["close"]
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def calculate_channels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Расчёт каналов Velas."""
        p = self.params
        
        # Средняя линия (EMA)
        middle = df["close"].ewm(span=p.i1, adjust=False).mean()
        
        # ATR для ширины каналов
        atr = self.calculate_atr(df, p.i2)
        
        # Каналы
        upper1 = middle + atr * p.i3
        lower1 = middle - atr * p.i3
        upper2 = middle + atr * p.i4
        lower2 = middle - atr * p.i4
        
        result = df.copy()
        result["velas_middle"] = middle
        result["velas_upper1"] = upper1
        result["velas_lower1"] = lower1
        result["velas_upper2"] = upper2
        result["velas_lower2"] = lower2
        result["velas_atr"] = atr
        
        return result
    
    def detect_signal(self, df: pd.DataFrame) -> Optional[VelasSignal]:
        """Детекция сигнала на последнем баре."""
        if len(df) < self.params.i1 + 10:
            return None
        
        # Расчёт каналов
        df_calc = self.calculate_channels(df)
        
        # Последние значения
        last = df_calc.iloc[-1]
        prev = df_calc.iloc[-2]
        
        close = last["close"]
        upper1 = last["velas_upper1"]
        lower1 = last["velas_lower1"]
        upper2 = last["velas_upper2"]
        lower2 = last["velas_lower2"]
        middle = last["velas_middle"]
        atr = last["velas_atr"]
        
        prev_close = prev["close"]
        prev_upper1 = prev["velas_upper1"]
        prev_lower1 = prev["velas_lower1"]
        
        # LONG сигнал: цена пробила нижний канал снизу вверх
        long_trigger = (prev_close < prev_lower1) and (close > lower1)
        
        # SHORT сигнал: цена пробила верхний канал сверху вниз  
        short_trigger = (prev_close > prev_upper1) and (close < upper1)
        
        if long_trigger:
            return self._create_signal("LONG", close, atr)
        elif short_trigger:
            return self._create_signal("SHORT", close, atr)
        
        return None
    
    def _create_signal(self, direction: str, entry: float, atr: float) -> VelasSignal:
        """Создание сигнала с TP/SL."""
        
        # SL на основе ATR (2x ATR)
        sl_distance = atr * 2
        
        # TP уровни (в процентах от входа)
        tp_percents = [0.8, 1.5, 2.5, 4.0, 6.0, 10.0]
        
        if direction == "LONG":
            sl_price = entry - sl_distance
            tp_levels = [entry * (1 + p / 100) for p in tp_percents]
        else:
            sl_price = entry + sl_distance
            tp_levels = [entry * (1 - p / 100) for p in tp_percents]
        
        # Сила сигнала (упрощённо)
        strength = min(1.0, atr / entry * 100)
        
        return VelasSignal(
            direction=direction,
            strength=strength,
            entry_price=round(entry, 8),
            sl_price=round(sl_price, 8),
            tp_levels=[round(tp, 8) for tp in tp_levels],
        )
    
    def get_volatility_regime(self, df: pd.DataFrame, lookback: int = 30) -> str:
        """Определение режима волатильности."""
        atr = self.calculate_atr(df, 14)
        
        current_atr = atr.iloc[-1]
        avg_atr = atr.iloc[-lookback:].mean()
        
        ratio = current_atr / avg_atr if avg_atr > 0 else 1.0
        
        if ratio < 0.7:
            return "low"
        elif ratio > 1.3:
            return "high"
        return "normal"


# Тестовая функция
def test_velas():
    """Тест индикатора."""
    # Генерация тестовых данных
    np.random.seed(42)
    n = 200
    
    dates = pd.date_range(start="2024-01-01", periods=n, freq="1h")
    
    # Симуляция цены
    price = 100
    prices = [price]
    for _ in range(n - 1):
        price *= 1 + np.random.randn() * 0.01
        prices.append(price)
    
    df = pd.DataFrame({
        "timestamp": dates,
        "open": prices,
        "high": [p * 1.005 for p in prices],
        "low": [p * 0.995 for p in prices],
        "close": prices,
        "volume": np.random.randint(1000, 10000, n),
    })
    
    # Расчёт
    indicator = VelasIndicator()
    df_calc = indicator.calculate_channels(df)
    
    print("Последние 5 баров:")
    print(df_calc[["close", "velas_middle", "velas_upper1", "velas_lower1", "velas_atr"]].tail())
    
    # Детекция сигнала
    signal = indicator.detect_signal(df)
    if signal:
        print(f"\nСигнал: {signal}")
    else:
        print("\nНет сигнала")
    
    # Режим волатильности
    regime = indicator.get_volatility_regime(df)
    print(f"Режим волатильности: {regime}")


if __name__ == "__main__":
    test_velas()
