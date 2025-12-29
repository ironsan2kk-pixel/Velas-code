"""
VELAS Volatility Analyzer - определение режима волатильности.

Режимы волатильности:
- LOW: ATR Ratio < 0.7 (спокойный рынок)
- NORMAL: ATR Ratio 0.7 - 1.3 (обычный рынок)
- HIGH: ATR Ratio > 1.3 (волатильный рынок)

ATR Ratio = текущий ATR / средний ATR за длинный период

Использование:
    analyzer = VolatilityAnalyzer(df)
    regime = analyzer.get_regime()
    print(regime)  # VolatilityRegime.LOW

    # Или сразу с настройками
    result = analyzer.analyze()
    print(result.regime, result.atr_ratio, result.recommendation)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Tuple, Any
import pandas as pd
import numpy as np
import logging


logger = logging.getLogger(__name__)


class VolatilityRegime(Enum):
    """Режим волатильности рынка."""
    LOW = "low"         # Низкая волатильность (ATR Ratio < 0.7)
    NORMAL = "normal"   # Нормальная волатильность (0.7 - 1.3)
    HIGH = "high"       # Высокая волатильность (> 1.3)
    
    @classmethod
    def from_ratio(cls, ratio: float) -> 'VolatilityRegime':
        """Определить режим по ATR ratio."""
        if ratio < 0.7:
            return cls.LOW
        elif ratio > 1.3:
            return cls.HIGH
        return cls.NORMAL


@dataclass
class VolatilityConfig:
    """Конфигурация анализа волатильности."""
    
    # Период ATR
    atr_period: int = 14
    
    # Период для расчёта среднего ATR (базовая линия)
    baseline_period: int = 100
    
    # Границы режимов
    low_threshold: float = 0.7      # < 0.7 = LOW
    high_threshold: float = 1.3     # > 1.3 = HIGH
    
    # Множители TP/SL для режимов
    low_tp_multiplier: float = 0.8    # Меньше TP в тихом рынке
    low_sl_multiplier: float = 0.8    # Меньше SL в тихом рынке
    
    normal_tp_multiplier: float = 1.0
    normal_sl_multiplier: float = 1.0
    
    high_tp_multiplier: float = 1.3   # Больше TP в волатильном рынке
    high_sl_multiplier: float = 1.2   # Немного больше SL
    
    def get_multipliers(self, regime: VolatilityRegime) -> Tuple[float, float]:
        """Получить множители TP и SL для режима."""
        if regime == VolatilityRegime.LOW:
            return self.low_tp_multiplier, self.low_sl_multiplier
        elif regime == VolatilityRegime.HIGH:
            return self.high_tp_multiplier, self.high_sl_multiplier
        return self.normal_tp_multiplier, self.normal_sl_multiplier


@dataclass
class VolatilityResult:
    """Результат анализа волатильности."""
    
    # Основной результат
    regime: VolatilityRegime
    
    # ATR данные
    current_atr: float
    average_atr: float
    atr_ratio: float
    
    # Исторические данные
    atr_min: float = 0.0
    atr_max: float = 0.0
    atr_percentile: float = 0.0  # Текущий ATR как перцентиль (0-100)
    
    # Множители
    tp_multiplier: float = 1.0
    sl_multiplier: float = 1.0
    
    # Рекомендации
    recommendation: str = ""
    
    def to_dict(self) -> dict:
        return {
            "regime": self.regime.value,
            "current_atr": round(self.current_atr, 8),
            "average_atr": round(self.average_atr, 8),
            "atr_ratio": round(self.atr_ratio, 4),
            "atr_min": round(self.atr_min, 8),
            "atr_max": round(self.atr_max, 8),
            "atr_percentile": round(self.atr_percentile, 2),
            "tp_multiplier": self.tp_multiplier,
            "sl_multiplier": self.sl_multiplier,
            "recommendation": self.recommendation,
        }


class VolatilityAnalyzer:
    """
    Анализатор волатильности рынка.
    
    Использует ATR Ratio для определения текущего режима
    и подстройки параметров торговли.
    """
    
    def __init__(
        self,
        df: pd.DataFrame = None,
        config: VolatilityConfig = None,
    ):
        """
        Args:
            df: DataFrame с OHLCV данными (опционально)
            config: Конфигурация анализа
        """
        self.df = df.copy() if df is not None else None
        self.config = config or VolatilityConfig()
        self._atr_series: Optional[pd.Series] = None
    
    def set_data(self, df: pd.DataFrame):
        """Установить данные для анализа."""
        self.df = df.copy()
        self._atr_series = None  # Сбросить кеш
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Расчёт ATR (Average True Range).
        
        Args:
            df: DataFrame с колонками high, low, close
            period: Период ATR
            
        Returns:
            Series с ATR значениями
        """
        high = df["high"]
        low = df["low"]
        close = df["close"]
        prev_close = close.shift(1)
        
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # RMA (Wilder's smoothing)
        atr = tr.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        
        return atr
    
    def _ensure_atr(self):
        """Убедиться что ATR рассчитан."""
        if self._atr_series is None:
            if self.df is None:
                raise ValueError("Данные не установлены. Вызовите set_data() или передайте df в конструктор.")
            self._atr_series = self.calculate_atr(self.df, self.config.atr_period)
    
    def get_current_atr(self) -> float:
        """Получить текущее значение ATR."""
        self._ensure_atr()
        return self._atr_series.iloc[-1]
    
    def get_average_atr(self) -> float:
        """Получить среднее значение ATR за baseline период."""
        self._ensure_atr()
        return self._atr_series.rolling(self.config.baseline_period).mean().iloc[-1]
    
    def get_atr_ratio(self) -> float:
        """Получить ATR Ratio (текущий / средний)."""
        current = self.get_current_atr()
        average = self.get_average_atr()
        
        if average == 0 or pd.isna(average):
            return 1.0
        
        return current / average
    
    def get_regime(self) -> VolatilityRegime:
        """Определить текущий режим волатильности."""
        ratio = self.get_atr_ratio()
        return VolatilityRegime.from_ratio(ratio)
    
    def analyze(self) -> VolatilityResult:
        """
        Полный анализ волатильности.
        
        Returns:
            VolatilityResult с детальной информацией
        """
        self._ensure_atr()
        
        current_atr = self.get_current_atr()
        average_atr = self.get_average_atr()
        atr_ratio = current_atr / average_atr if average_atr > 0 else 1.0
        
        regime = VolatilityRegime.from_ratio(atr_ratio)
        tp_mult, sl_mult = self.config.get_multipliers(regime)
        
        # Статистика ATR
        atr_clean = self._atr_series.dropna()
        atr_min = atr_clean.min()
        atr_max = atr_clean.max()
        atr_percentile = (atr_clean < current_atr).mean() * 100
        
        # Рекомендация
        recommendation = self._generate_recommendation(regime, atr_ratio, atr_percentile)
        
        return VolatilityResult(
            regime=regime,
            current_atr=current_atr,
            average_atr=average_atr,
            atr_ratio=atr_ratio,
            atr_min=atr_min,
            atr_max=atr_max,
            atr_percentile=atr_percentile,
            tp_multiplier=tp_mult,
            sl_multiplier=sl_mult,
            recommendation=recommendation,
        )
    
    def _generate_recommendation(
        self, 
        regime: VolatilityRegime, 
        ratio: float,
        percentile: float,
    ) -> str:
        """Генерация текстовой рекомендации."""
        if regime == VolatilityRegime.LOW:
            return (
                f"Низкая волатильность (ATR ratio={ratio:.2f}, {percentile:.0f}%). "
                "Рекомендуется: уменьшить TP/SL уровни, ожидать меньшие движения."
            )
        elif regime == VolatilityRegime.HIGH:
            return (
                f"Высокая волатильность (ATR ratio={ratio:.2f}, {percentile:.0f}%). "
                "Рекомендуется: увеличить TP уровни, немного расширить SL."
            )
        return (
            f"Нормальная волатильность (ATR ratio={ratio:.2f}, {percentile:.0f}%). "
            "Стандартные параметры торговли."
        )
    
    def get_regime_for_candle(self, index: int) -> VolatilityRegime:
        """
        Определить режим волатильности для конкретной свечи.
        
        Args:
            index: Индекс свечи (позиция в DataFrame)
            
        Returns:
            VolatilityRegime
        """
        self._ensure_atr()
        
        if index < self.config.baseline_period:
            return VolatilityRegime.NORMAL  # Недостаточно данных
        
        current = self._atr_series.iloc[index]
        avg = self._atr_series.iloc[:index+1].tail(self.config.baseline_period).mean()
        
        if avg == 0 or pd.isna(avg):
            return VolatilityRegime.NORMAL
        
        ratio = current / avg
        return VolatilityRegime.from_ratio(ratio)
    
    def get_regime_series(self) -> pd.Series:
        """
        Получить серию режимов волатильности для всех баров.
        
        Returns:
            Series с VolatilityRegime значениями
        """
        self._ensure_atr()
        
        avg_atr = self._atr_series.rolling(self.config.baseline_period).mean()
        ratio = self._atr_series / avg_atr
        
        def to_regime(r):
            if pd.isna(r):
                return VolatilityRegime.NORMAL
            return VolatilityRegime.from_ratio(r)
        
        return ratio.apply(to_regime)


def get_volatility_regime(
    df: pd.DataFrame,
    atr_period: int = 14,
    baseline_period: int = 100,
) -> VolatilityRegime:
    """
    Быстрая функция для определения режима волатильности.
    
    Args:
        df: DataFrame с OHLCV
        atr_period: Период ATR
        baseline_period: Период базовой линии
        
    Returns:
        VolatilityRegime
    """
    config = VolatilityConfig(
        atr_period=atr_period,
        baseline_period=baseline_period,
    )
    analyzer = VolatilityAnalyzer(df, config)
    return analyzer.get_regime()


def analyze_volatility(df: pd.DataFrame) -> VolatilityResult:
    """
    Быстрая функция для полного анализа волатильности.
    
    Args:
        df: DataFrame с OHLCV
        
    Returns:
        VolatilityResult
    """
    analyzer = VolatilityAnalyzer(df)
    return analyzer.analyze()


@dataclass
class VolatilityStats:
    """Статистика волатильности для отчётов."""
    
    symbol: str
    timeframe: str
    
    # Текущее состояние
    current_regime: VolatilityRegime
    current_atr_ratio: float
    
    # Распределение режимов (% времени в каждом)
    low_percent: float = 0.0
    normal_percent: float = 0.0
    high_percent: float = 0.0
    
    # Переходы между режимами
    regime_changes_count: int = 0
    avg_regime_duration_bars: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "current_regime": self.current_regime.value,
            "current_atr_ratio": round(self.current_atr_ratio, 4),
            "low_percent": round(self.low_percent, 2),
            "normal_percent": round(self.normal_percent, 2),
            "high_percent": round(self.high_percent, 2),
            "regime_changes_count": self.regime_changes_count,
            "avg_regime_duration_bars": round(self.avg_regime_duration_bars, 1),
        }


def calculate_volatility_stats(
    df: pd.DataFrame,
    symbol: str = "UNKNOWN",
    timeframe: str = "1h",
) -> VolatilityStats:
    """
    Расчёт статистики волатильности для пары.
    
    Args:
        df: DataFrame с OHLCV
        symbol: Название пары
        timeframe: Таймфрейм
        
    Returns:
        VolatilityStats
    """
    analyzer = VolatilityAnalyzer(df)
    regime_series = analyzer.get_regime_series()
    
    # Текущее состояние
    current_analysis = analyzer.analyze()
    
    # Распределение режимов
    total = len(regime_series.dropna())
    if total > 0:
        low_pct = (regime_series == VolatilityRegime.LOW).sum() / total * 100
        normal_pct = (regime_series == VolatilityRegime.NORMAL).sum() / total * 100
        high_pct = (regime_series == VolatilityRegime.HIGH).sum() / total * 100
    else:
        low_pct = normal_pct = high_pct = 0.0
    
    # Переходы между режимами
    regime_changes = (regime_series != regime_series.shift(1)).sum()
    avg_duration = total / (regime_changes + 1) if regime_changes > 0 else total
    
    return VolatilityStats(
        symbol=symbol,
        timeframe=timeframe,
        current_regime=current_analysis.regime,
        current_atr_ratio=current_analysis.atr_ratio,
        low_percent=low_pct,
        normal_percent=normal_pct,
        high_percent=high_pct,
        regime_changes_count=regime_changes,
        avg_regime_duration_bars=avg_duration,
    )
