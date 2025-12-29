"""
VELAS Indicator - перевод Pine Script индикатора в Python.

Оригинал: "Велас" v6 by anyoffeye
Логика:
1. Расчёт канала (highest/lowest за i1 периодов)
2. Середина канала (fib 0.5)
3. Триггеры входа = середина ± (ATR*i4 + StdDev*i3) * (1 ± i5%)
4. LONG когда high > long_trigger
5. SHORT когда low < short_trigger
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple
import numpy as np
import pandas as pd


@dataclass
class VelasPreset:
    """Пресет параметров индикатора Velas (i1-i5)."""
    
    index: int  # 0-59
    i1: int     # Период канала (highest/lowest)
    i2: int     # Период StdDev
    i3: float   # Множитель StdDev
    i4: float   # Множитель ATR
    i5: float   # Процент смещения от середины
    
    def __post_init__(self):
        if not 0 <= self.index < 60:
            raise ValueError(f"index должен быть 0-59, получено: {self.index}")
        if self.i1 < 1:
            raise ValueError(f"i1 должен быть >= 1, получено: {self.i1}")
        if self.i2 < 1:
            raise ValueError(f"i2 должен быть >= 1, получено: {self.i2}")
    
    @property
    def name(self) -> str:
        return f"Вариант {self.index + 1}"
    
    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "i1": self.i1,
            "i2": self.i2,
            "i3": self.i3,
            "i4": self.i4,
            "i5": self.i5,
        }


# 60 комбинаций параметров из оригинального Pine Script
# Первые 26 = базовый набор, 27-60 = расширение
_VELAS_I1 = [40, 50, 55, 60, 65, 70, 80, 90, 60, 55, 50, 45, 40, 35, 30, 150, 150, 200, 40, 200, 200, 200, 30, 20, 40, 15, 100, 110, 120, 130, 140, 160, 180, 100, 80, 75, 65, 55, 25, 18, 10, 12, 15, 20, 25, 30, 35, 75, 95, 180, 220, 250, 300, 320, 350, 400, 450, 500, 260, 280]
_VELAS_I2 = [10, 11, 12, 14, 14, 14, 14, 15, 16, 16, 15, 16, 15, 15, 14, 14, 14, 14, 13, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 16, 12, 13, 12, 13, 13, 12, 8, 9, 10, 12, 14, 16, 18, 20, 21, 22, 18, 20, 14, 16, 12, 8, 18, 20, 10, 14]
_VELAS_I3 = [0.3, 0.4, 0.5, 0.6, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.6, 1.7, 1.8, 2.0, 2.1, 1.1, 1.2, 1.4, 1.6, 2.3, 2.5, 2.7, 3.0, 1.05, 1.15, 1.25, 1.35, 1.45, 1.55, 1.65, 1.35, 0.65, 0.75, 0.55, 1.0, 2.0, 2.7, 0.2, 0.25, 0.35, 0.45, 0.6, 0.7, 0.85, 1.1, 1.3, 1.6, 1.9, 2.2, 2.6, 2.9, 3.2, 3.5, 4.0, 1.05, 0.55, 2.4]
_VELAS_I4 = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.5, 1.6, 1.7, 1.8, 1.8, 1.9, 2.0, 2.2, 2.4, 2.6, 1.0, 1.6, 1.8, 2.0, 2.6, 3.0, 3.2, 3.5, 1.75, 1.85, 1.95, 2.05, 2.15, 2.25, 2.35, 1.9, 1.4, 1.5, 1.35, 1.55, 2.4, 3.1, 0.9, 1.0, 1.15, 1.25, 1.4, 1.55, 1.7, 1.85, 2.0, 2.2, 2.4, 2.6, 2.9, 3.1, 3.3, 3.5, 4.0, 1.35, 1.6, 2.8]
_VELAS_I5 = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.5, 1.6, 1.7, 1.8, 1.8, 1.9, 1.5, 1.3, 1.5, 1.8, 1.0, 2.1, 2.4, 2.0, 2.6, 3.0, 3.2, 3.5, 1.75, 1.85, 1.75, 1.65, 1.55, 1.45, 1.55, 1.9, 1.25, 1.35, 1.15, 1.55, 2.2, 3.0, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.2, 3.5, 3.8, 4.0, 4.2, 1.5, 2.1, 3.6]

# Готовый список всех 60 пресетов
VELAS_PRESETS_60: List[VelasPreset] = [
    VelasPreset(
        index=i,
        i1=_VELAS_I1[i],
        i2=_VELAS_I2[i],
        i3=_VELAS_I3[i],
        i4=_VELAS_I4[i],
        i5=_VELAS_I5[i],
    )
    for i in range(60)
]


@dataclass
class VelasResult:
    """Результат расчёта индикатора Velas для одного бара."""
    
    timestamp: pd.Timestamp
    high_channel: float      # Верхняя граница канала
    low_channel: float       # Нижняя граница канала
    mid_channel: float       # Середина (fib 0.5)
    long_trigger: float      # Триггер для LONG
    short_trigger: float     # Триггер для SHORT
    atr: float               # ATR(14)
    stdev: float             # StdDev(close, i2)
    
    @property
    def channel_width(self) -> float:
        return self.high_channel - self.low_channel
    
    @property
    def channel_width_percent(self) -> float:
        if self.mid_channel == 0:
            return 0.0
        return (self.channel_width / self.mid_channel) * 100


class VelasIndicator:
    """
    Индикатор Velas - Python-версия Pine Script индикатора.
    
    Логика расчёта:
    1. high_channel = highest(high, i1)
    2. low_channel = lowest(low, i1)
    3. mid_channel = high_channel - (high_channel - low_channel) * 0.5
    4. stdev_value = stdev(close, i2) * i3
    5. atr_value = atr(14) * i4
    6. long_trigger = mid_channel * (1 + i5/100) + atr_value + stdev_value
    7. short_trigger = mid_channel * (1 - i5/100) - atr_value - stdev_value
    """
    
    ATR_PERIOD = 14  # Фиксированный период ATR как в оригинале
    
    def __init__(self, preset: VelasPreset):
        self.preset = preset
        self._cache: dict = {}
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Расчёт ATR (Average True Range).
        
        ATR = RMA(TR, period)
        где TR = max(high - low, abs(high - prev_close), abs(low - prev_close))
        """
        high = df["high"]
        low = df["low"]
        close = df["close"]
        prev_close = close.shift(1)
        
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # RMA (Wilder's smoothing) = EMA с alpha = 1/period
        atr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        
        return atr
    
    @staticmethod
    def calculate_stdev(series: pd.Series, period: int) -> pd.Series:
        """Расчёт стандартного отклонения."""
        return series.rolling(window=period, min_periods=period).std()
    
    @staticmethod
    def calculate_highest(series: pd.Series, period: int) -> pd.Series:
        """Расчёт максимума за period баров."""
        return series.rolling(window=period, min_periods=period).max()
    
    @staticmethod
    def calculate_lowest(series: pd.Series, period: int) -> pd.Series:
        """Расчёт минимума за period баров."""
        return series.rolling(window=period, min_periods=period).min()
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Рассчитать индикатор Velas для всего DataFrame.
        
        Args:
            df: DataFrame с колонками [timestamp, open, high, low, close, volume]
            
        Returns:
            DataFrame с добавленными колонками индикатора
        """
        if len(df) < max(self.preset.i1, self.preset.i2, self.ATR_PERIOD):
            raise ValueError(
                f"Недостаточно данных: нужно минимум {max(self.preset.i1, self.preset.i2, self.ATR_PERIOD)} баров"
            )
        
        result = df.copy()
        
        # 1. Канал
        result["high_channel"] = self.calculate_highest(df["high"], self.preset.i1)
        result["low_channel"] = self.calculate_lowest(df["low"], self.preset.i1)
        result["channel_range"] = result["high_channel"] - result["low_channel"]
        result["mid_channel"] = result["high_channel"] - result["channel_range"] * 0.5
        
        # 2. ATR и StdDev
        result["atr"] = self.calculate_atr(df, self.ATR_PERIOD)
        result["stdev"] = self.calculate_stdev(df["close"], self.preset.i2)
        
        # 3. Компоненты триггера
        result["atr_component"] = result["atr"] * self.preset.i4
        result["stdev_component"] = result["stdev"] * self.preset.i3
        
        # 4. Триггеры входа
        result["long_trigger"] = (
            result["mid_channel"] * (1 + self.preset.i5 / 100) 
            + result["atr_component"] 
            + result["stdev_component"]
        )
        result["short_trigger"] = (
            result["mid_channel"] * (1 - self.preset.i5 / 100) 
            - result["atr_component"] 
            - result["stdev_component"]
        )
        
        return result
    
    def get_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Получить сигналы LONG/SHORT.
        
        Условия:
        - LONG: high > long_trigger (и НЕ в LONG позиции)
        - SHORT: low < short_trigger (и НЕ в SHORT позиции)
        
        Returns:
            DataFrame с колонками:
            - long_signal: bool
            - short_signal: bool
            - entry_price: float (close при сигнале)
        """
        result = self.calculate(df).copy()
        
        # Базовые условия пробоя
        result["raw_long"] = result["high"] > result["long_trigger"]
        result["raw_short"] = result["low"] < result["short_trigger"]
        
        # Отслеживание позиции (нельзя открыть новый LONG пока в LONG)
        # Это упрощённая логика - в live engine будет полноценный state machine
        in_position = 0  # 0 = нет, 1 = long, -1 = short
        long_signals = []
        short_signals = []
        
        for idx in range(len(result)):
            raw_long = result["raw_long"].iloc[idx]
            raw_short = result["raw_short"].iloc[idx]
            
            long_signal = False
            short_signal = False
            
            if raw_long and in_position != 1:
                long_signal = True
                in_position = 1
            elif raw_short and in_position != -1:
                short_signal = True
                in_position = -1
            
            # Противоположный сигнал закрывает позицию
            if raw_short and in_position == 1:
                in_position = -1
                short_signal = True
            elif raw_long and in_position == -1:
                in_position = 1
                long_signal = True
            
            long_signals.append(long_signal)
            short_signals.append(short_signal)
        
        result["long_signal"] = long_signals
        result["short_signal"] = short_signals
        result["entry_price"] = result["close"]
        
        return result
    
    def calculate_single(self, df: pd.DataFrame, idx: int = -1) -> Optional[VelasResult]:
        """
        Рассчитать индикатор для одного бара.
        
        Args:
            df: DataFrame с OHLCV данными
            idx: Индекс бара (-1 = последний)
            
        Returns:
            VelasResult или None если недостаточно данных
        """
        calc_df = self.calculate(df)
        
        if idx < 0:
            idx = len(calc_df) + idx
        
        if idx < 0 or idx >= len(calc_df):
            return None
        
        row = calc_df.iloc[idx]
        
        if pd.isna(row["long_trigger"]) or pd.isna(row["short_trigger"]):
            return None
        
        return VelasResult(
            timestamp=row.name if isinstance(row.name, pd.Timestamp) else pd.Timestamp(row.get("timestamp", row.name)),
            high_channel=row["high_channel"],
            low_channel=row["low_channel"],
            mid_channel=row["mid_channel"],
            long_trigger=row["long_trigger"],
            short_trigger=row["short_trigger"],
            atr=row["atr"],
            stdev=row["stdev"],
        )


def find_best_preset(
    df: pd.DataFrame,
    presets: List[VelasPreset] = None,
    metric_func: callable = None,
) -> Tuple[VelasPreset, float]:
    """
    Найти лучший пресет по заданной метрике.
    
    Args:
        df: DataFrame с OHLCV данными
        presets: Список пресетов (по умолчанию все 60)
        metric_func: Функция расчёта метрики (preset, signals_df) -> float
        
    Returns:
        (лучший пресет, значение метрики)
    """
    if presets is None:
        presets = VELAS_PRESETS_60
    
    if metric_func is None:
        # По умолчанию - количество сигналов с положительным исходом
        def default_metric(preset: VelasPreset, signals_df: pd.DataFrame) -> float:
            total_signals = signals_df["long_signal"].sum() + signals_df["short_signal"].sum()
            return float(total_signals)
        metric_func = default_metric
    
    best_preset = presets[0]
    best_metric = float("-inf")
    
    for preset in presets:
        try:
            indicator = VelasIndicator(preset)
            signals_df = indicator.get_signals(df)
            metric = metric_func(preset, signals_df)
            
            if metric > best_metric:
                best_metric = metric
                best_preset = preset
        except Exception:
            continue
    
    return best_preset, best_metric


# Вспомогательные функции для совместимости с Pine Script
def ta_highest(series: pd.Series, period: int) -> pd.Series:
    """Аналог ta.highest() из Pine Script."""
    return VelasIndicator.calculate_highest(series, period)


def ta_lowest(series: pd.Series, period: int) -> pd.Series:
    """Аналог ta.lowest() из Pine Script."""
    return VelasIndicator.calculate_lowest(series, period)


def ta_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Аналог ta.atr() из Pine Script."""
    return VelasIndicator.calculate_atr(df, period)


def ta_stdev(series: pd.Series, period: int) -> pd.Series:
    """Аналог ta.stdev() из Pine Script."""
    return VelasIndicator.calculate_stdev(series, period)
