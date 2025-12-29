"""
VELAS Correlation - расчёт корреляций между торговыми парами.

Используется для:
- Фильтрации сигналов на высококоррелированных парах
- Ограничения одновременных позиций в одном секторе
- Диверсификации портфеля
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
import pandas as pd
import numpy as np
from enum import Enum


class CorrelationMethod(Enum):
    """Метод расчёта корреляции."""
    PEARSON = "pearson"
    SPEARMAN = "spearman"
    KENDALL = "kendall"


@dataclass
class CorrelationResult:
    """Результат расчёта корреляции между двумя парами."""
    
    symbol1: str
    symbol2: str
    correlation: float
    method: CorrelationMethod
    period_days: int
    calculated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def is_high(self) -> bool:
        """Высокая корреляция (> 0.7)."""
        return abs(self.correlation) > 0.7
    
    @property
    def is_medium(self) -> bool:
        """Средняя корреляция (0.4 - 0.7)."""
        return 0.4 <= abs(self.correlation) <= 0.7
    
    @property
    def is_low(self) -> bool:
        """Низкая корреляция (< 0.4)."""
        return abs(self.correlation) < 0.4
    
    def to_dict(self) -> dict:
        return {
            "symbol1": self.symbol1,
            "symbol2": self.symbol2,
            "correlation": round(self.correlation, 4),
            "method": self.method.value,
            "period_days": self.period_days,
            "is_high": self.is_high,
            "calculated_at": self.calculated_at.isoformat(),
        }


@dataclass
class CorrelationMatrix:
    """Матрица корреляций для всех пар."""
    
    symbols: List[str]
    matrix: pd.DataFrame  # DataFrame с символами в индексах и колонках
    method: CorrelationMethod
    period_days: int
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def get_correlation(self, symbol1: str, symbol2: str) -> float:
        """Получить корреляцию между двумя парами."""
        if symbol1 == symbol2:
            return 1.0
        
        if symbol1 not in self.symbols or symbol2 not in self.symbols:
            return 0.0
        
        return self.matrix.loc[symbol1, symbol2]
    
    def get_high_correlations(self, threshold: float = 0.7) -> List[CorrelationResult]:
        """Получить все пары с высокой корреляцией."""
        results = []
        
        for i, sym1 in enumerate(self.symbols):
            for sym2 in self.symbols[i+1:]:
                corr = self.matrix.loc[sym1, sym2]
                if abs(corr) >= threshold:
                    results.append(CorrelationResult(
                        symbol1=sym1,
                        symbol2=sym2,
                        correlation=corr,
                        method=self.method,
                        period_days=self.period_days,
                        calculated_at=self.calculated_at,
                    ))
        
        return sorted(results, key=lambda x: abs(x.correlation), reverse=True)
    
    def get_correlated_symbols(self, symbol: str, threshold: float = 0.7) -> List[str]:
        """Получить список символов, коррелирующих с данным."""
        if symbol not in self.symbols:
            return []
        
        correlated = []
        for other in self.symbols:
            if other != symbol:
                corr = abs(self.matrix.loc[symbol, other])
                if corr >= threshold:
                    correlated.append(other)
        
        return correlated
    
    def to_dict(self) -> dict:
        return {
            "symbols": self.symbols,
            "matrix": self.matrix.to_dict(),
            "method": self.method.value,
            "period_days": self.period_days,
            "calculated_at": self.calculated_at.isoformat(),
        }


class CorrelationCalculator:
    """
    Калькулятор корреляций между торговыми парами.
    
    Использование:
        calculator = CorrelationCalculator()
        
        # Добавляем данные
        calculator.add_price_data("BTCUSDT", btc_df)
        calculator.add_price_data("ETHUSDT", eth_df)
        
        # Считаем матрицу
        matrix = calculator.calculate_matrix()
        
        # Проверяем корреляцию
        corr = matrix.get_correlation("BTCUSDT", "ETHUSDT")
    """
    
    def __init__(
        self,
        method: CorrelationMethod = CorrelationMethod.PEARSON,
        period_days: int = 30,
        use_returns: bool = True,
    ):
        """
        Args:
            method: Метод расчёта корреляции
            period_days: Период для расчёта (дней)
            use_returns: Использовать returns вместо цен (рекомендуется)
        """
        self.method = method
        self.period_days = period_days
        self.use_returns = use_returns
        
        self._price_data: Dict[str, pd.DataFrame] = {}
        self._cache: Optional[CorrelationMatrix] = None
        self._cache_time: Optional[datetime] = None
        self._cache_ttl = timedelta(hours=1)  # Кэш на 1 час
    
    def add_price_data(
        self,
        symbol: str,
        df: pd.DataFrame,
        price_column: str = "close",
    ) -> None:
        """
        Добавить ценовые данные для символа.
        
        Args:
            symbol: Символ пары (например, "BTCUSDT")
            df: DataFrame с ценами (должен иметь timestamp в индексе или колонке)
            price_column: Колонка с ценами
        """
        if df is None or len(df) == 0:
            return
        
        # Нормализуем DataFrame
        if "timestamp" in df.columns:
            df = df.set_index("timestamp")
        
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Берём только нужную колонку
        if price_column not in df.columns:
            raise ValueError(f"Column '{price_column}' not found in DataFrame")
        
        self._price_data[symbol] = df[[price_column]].copy()
        self._price_data[symbol].columns = [symbol]
        
        # Сбрасываем кэш
        self._cache = None
    
    def add_prices_batch(
        self,
        prices: Dict[str, pd.DataFrame],
        price_column: str = "close",
    ) -> None:
        """Добавить данные для нескольких символов."""
        for symbol, df in prices.items():
            self.add_price_data(symbol, df, price_column)
    
    def calculate_pair_correlation(
        self,
        symbol1: str,
        symbol2: str,
    ) -> Optional[CorrelationResult]:
        """Рассчитать корреляцию между двумя парами."""
        if symbol1 not in self._price_data or symbol2 not in self._price_data:
            return None
        
        df1 = self._price_data[symbol1]
        df2 = self._price_data[symbol2]
        
        # Объединяем по индексу
        merged = pd.concat([df1, df2], axis=1).dropna()
        
        if len(merged) < 20:  # Минимум 20 точек
            return None
        
        # Берём последние N дней
        if self.period_days > 0:
            cutoff = merged.index.max() - timedelta(days=self.period_days)
            merged = merged[merged.index >= cutoff]
        
        if len(merged) < 20:
            return None
        
        # Считаем returns если нужно
        if self.use_returns:
            data1 = merged[symbol1].pct_change().dropna()
            data2 = merged[symbol2].pct_change().dropna()
        else:
            data1 = merged[symbol1]
            data2 = merged[symbol2]
        
        # Считаем корреляцию
        if self.method == CorrelationMethod.PEARSON:
            corr = data1.corr(data2, method="pearson")
        elif self.method == CorrelationMethod.SPEARMAN:
            corr = data1.corr(data2, method="spearman")
        else:
            corr = data1.corr(data2, method="kendall")
        
        if pd.isna(corr):
            return None
        
        return CorrelationResult(
            symbol1=symbol1,
            symbol2=symbol2,
            correlation=corr,
            method=self.method,
            period_days=self.period_days,
        )
    
    def calculate_matrix(self, force: bool = False) -> Optional[CorrelationMatrix]:
        """
        Рассчитать матрицу корреляций для всех пар.
        
        Args:
            force: Пересчитать даже если есть кэш
            
        Returns:
            CorrelationMatrix или None если недостаточно данных
        """
        # Проверяем кэш
        if not force and self._cache is not None:
            if self._cache_time and datetime.now() - self._cache_time < self._cache_ttl:
                return self._cache
        
        symbols = list(self._price_data.keys())
        
        if len(symbols) < 2:
            return None
        
        # Собираем все данные в один DataFrame
        all_data = []
        for symbol in symbols:
            all_data.append(self._price_data[symbol])
        
        merged = pd.concat(all_data, axis=1).dropna()
        
        if len(merged) < 20:
            return None
        
        # Берём последние N дней
        if self.period_days > 0:
            cutoff = merged.index.max() - timedelta(days=self.period_days)
            merged = merged[merged.index >= cutoff]
        
        if len(merged) < 20:
            return None
        
        # Считаем returns если нужно
        if self.use_returns:
            merged = merged.pct_change().dropna()
        
        # Считаем корреляционную матрицу
        if self.method == CorrelationMethod.PEARSON:
            corr_matrix = merged.corr(method="pearson")
        elif self.method == CorrelationMethod.SPEARMAN:
            corr_matrix = merged.corr(method="spearman")
        else:
            corr_matrix = merged.corr(method="kendall")
        
        self._cache = CorrelationMatrix(
            symbols=symbols,
            matrix=corr_matrix,
            method=self.method,
            period_days=self.period_days,
        )
        self._cache_time = datetime.now()
        
        return self._cache
    
    def clear_cache(self) -> None:
        """Очистить кэш корреляций."""
        self._cache = None
        self._cache_time = None
    
    def clear_data(self) -> None:
        """Очистить все данные."""
        self._price_data.clear()
        self.clear_cache()


# === Секторы для диверсификации ===

SECTORS: Dict[str, List[str]] = {
    "BTC": ["BTCUSDT"],
    "ETH": ["ETHUSDT"],
    "L1": ["SOLUSDT", "AVAXUSDT", "ATOMUSDT", "NEARUSDT", "APTUSDT"],
    "L2": ["MATICUSDT", "ARBUSDT", "OPUSDT"],
    "DEFI": ["LINKUSDT", "UNIUSDT", "INJUSDT"],
    "OLD": ["XRPUSDT", "ADAUSDT", "DOTUSDT", "LTCUSDT", "ETCUSDT"],
    "MEME": ["DOGEUSDT"],
    "CEX": ["BNBUSDT"],
}


def get_symbol_sector(symbol: str) -> str:
    """Получить сектор для символа."""
    for sector, symbols in SECTORS.items():
        if symbol in symbols:
            return sector
    return "OTHER"


def get_sector_symbols(sector: str) -> List[str]:
    """Получить все символы сектора."""
    return SECTORS.get(sector, [])


def are_same_sector(symbol1: str, symbol2: str) -> bool:
    """Проверить, принадлежат ли символы одному сектору."""
    return get_symbol_sector(symbol1) == get_symbol_sector(symbol2)


class SectorFilter:
    """
    Фильтр по секторам для диверсификации портфеля.
    
    Использование:
        filter = SectorFilter(max_per_sector=2)
        
        # Проверяем можно ли открыть позицию
        open_positions = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        can_open = filter.can_open_position("AVAXUSDT", open_positions)
    """
    
    def __init__(self, max_per_sector: int = 2):
        """
        Args:
            max_per_sector: Максимум позиций на сектор
        """
        self.max_per_sector = max_per_sector
    
    def count_sector_positions(
        self,
        sector: str,
        open_positions: List[str],
    ) -> int:
        """Посчитать количество открытых позиций в секторе."""
        return sum(1 for pos in open_positions if get_symbol_sector(pos) == sector)
    
    def can_open_position(
        self,
        symbol: str,
        open_positions: List[str],
    ) -> bool:
        """
        Проверить, можно ли открыть позицию по символу.
        
        Args:
            symbol: Символ для новой позиции
            open_positions: Список открытых позиций
            
        Returns:
            True если можно открыть
        """
        sector = get_symbol_sector(symbol)
        current_count = self.count_sector_positions(sector, open_positions)
        return current_count < self.max_per_sector
    
    def get_available_sectors(
        self,
        open_positions: List[str],
    ) -> List[str]:
        """Получить секторы, где ещё можно открыть позиции."""
        available = []
        
        for sector in SECTORS:
            count = self.count_sector_positions(sector, open_positions)
            if count < self.max_per_sector:
                available.append(sector)
        
        return available
    
    def get_sector_stats(
        self,
        open_positions: List[str],
    ) -> Dict[str, dict]:
        """Получить статистику по секторам."""
        stats = {}
        
        for sector in SECTORS:
            count = self.count_sector_positions(sector, open_positions)
            stats[sector] = {
                "count": count,
                "max": self.max_per_sector,
                "available": self.max_per_sector - count,
                "symbols": get_sector_symbols(sector),
            }
        
        return stats


class CorrelationFilter:
    """
    Фильтр по корреляции для диверсификации.
    
    Использование:
        filter = CorrelationFilter(calculator, threshold=0.7)
        
        # Проверяем можно ли открыть позицию
        can_open = filter.can_open_position("ETHUSDT", ["BTCUSDT"])
    """
    
    def __init__(
        self,
        calculator: CorrelationCalculator,
        threshold: float = 0.7,
    ):
        """
        Args:
            calculator: Калькулятор корреляций
            threshold: Порог корреляции (позиции не открываются при |corr| > threshold)
        """
        self.calculator = calculator
        self.threshold = threshold
    
    def can_open_position(
        self,
        symbol: str,
        open_positions: List[str],
    ) -> Tuple[bool, Optional[str]]:
        """
        Проверить, можно ли открыть позицию по символу.
        
        Args:
            symbol: Символ для новой позиции
            open_positions: Список открытых позиций
            
        Returns:
            (can_open, blocking_symbol) - можно ли открыть и что блокирует
        """
        matrix = self.calculator.calculate_matrix()
        
        if matrix is None:
            # Нет данных - разрешаем
            return True, None
        
        for open_pos in open_positions:
            corr = matrix.get_correlation(symbol, open_pos)
            if abs(corr) > self.threshold:
                return False, open_pos
        
        return True, None
    
    def get_blocking_positions(
        self,
        symbol: str,
        open_positions: List[str],
    ) -> List[Tuple[str, float]]:
        """
        Получить список позиций, блокирующих открытие.
        
        Returns:
            Список (symbol, correlation)
        """
        blocking = []
        matrix = self.calculator.calculate_matrix()
        
        if matrix is None:
            return blocking
        
        for open_pos in open_positions:
            corr = matrix.get_correlation(symbol, open_pos)
            if abs(corr) > self.threshold:
                blocking.append((open_pos, corr))
        
        return sorted(blocking, key=lambda x: abs(x[1]), reverse=True)
