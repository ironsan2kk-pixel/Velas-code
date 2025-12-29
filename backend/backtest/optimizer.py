"""
VELAS Optimizer - Grid search по пресетам индикатора.

Функционал:
- Grid search по 60 пресетам i1-i5
- Параллельное выполнение бэктестов
- Сортировка по composite score
- Фильтрация по минимальным требованиям

Использование:
    optimizer = VelasOptimizer(df, config)
    results = optimizer.run_grid_search()
    best = optimizer.get_best_preset()
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import pandas as pd
import numpy as np
import logging
import time

from ..core.velas_indicator import VelasPreset, VELAS_PRESETS_60
from ..core.tpsl import TPSLConfig
from ..core.signals import FilterConfig
from .engine import BacktestEngine, BacktestConfig, BacktestResult
from .metrics import BacktestMetrics


logger = logging.getLogger(__name__)


@dataclass
class OptimizationConfig:
    """Конфигурация оптимизации."""
    
    # Целевые метрики
    min_trades: int = 20              # Минимум сделок для валидности
    min_win_rate_tp1: float = 65.0    # Минимальный WinRate TP1 (%)
    min_sharpe: float = 1.2           # Минимальный Sharpe Ratio
    max_sharpe: float = 2.5           # Максимальный Sharpe (защита от переобучения)
    min_profit_factor: float = 1.4    # Минимальный Profit Factor
    max_drawdown: float = 15.0        # Максимальная просадка (%)
    
    # Веса для composite score
    weight_sharpe: float = 0.30
    weight_profit_factor: float = 0.25
    weight_win_rate_tp1: float = 0.25
    weight_drawdown: float = 0.20
    
    # Параллелизация
    max_workers: int = None  # None = cpu_count()
    
    # Пресеты для оптимизации
    preset_indices: List[int] = None  # None = все 60
    
    def __post_init__(self):
        if self.max_workers is None:
            self.max_workers = max(1, multiprocessing.cpu_count() - 1)
        
        if self.preset_indices is None:
            self.preset_indices = list(range(60))


@dataclass
class OptimizationResult:
    """Результат оптимизации одного пресета."""
    
    preset: VelasPreset
    backtest_result: BacktestResult
    metrics: BacktestMetrics
    
    # Расчётные поля
    is_valid: bool = False           # Прошёл ли минимальные требования
    composite_score: float = 0.0     # Общий скор (0-100)
    
    # Причина невалидности
    invalid_reasons: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Конвертация в словарь."""
        return {
            "preset_index": self.preset.index,
            "preset_name": self.preset.name,
            "i1": self.preset.i1,
            "i2": self.preset.i2,
            "i3": self.preset.i3,
            "i4": self.preset.i4,
            "i5": self.preset.i5,
            "total_trades": self.metrics.total_trades,
            "win_rate": round(self.metrics.win_rate, 2),
            "win_rate_tp1": round(self.metrics.win_rate_tp1, 2),
            "sharpe_ratio": round(self.metrics.sharpe_ratio, 2),
            "profit_factor": round(self.metrics.profit_factor, 2),
            "max_drawdown": round(self.metrics.max_drawdown_percent, 2),
            "total_pnl": round(self.metrics.total_pnl_percent, 2),
            "is_valid": self.is_valid,
            "composite_score": round(self.composite_score, 2),
            "invalid_reasons": self.invalid_reasons,
        }


@dataclass
class GridSearchResult:
    """Полный результат grid search."""
    
    # Параметры
    symbol: str
    timeframe: str
    start_date: datetime
    end_date: datetime
    total_bars: int
    
    # Результаты
    all_results: List[OptimizationResult] = field(default_factory=list)
    valid_results: List[OptimizationResult] = field(default_factory=list)
    
    # Лучший
    best_result: OptimizationResult = None
    
    # Статистика
    total_presets_tested: int = 0
    valid_presets_count: int = 0
    execution_time_sec: float = 0.0
    
    def to_dataframe(self) -> pd.DataFrame:
        """Результаты в DataFrame для анализа."""
        rows = [r.to_dict() for r in self.all_results]
        df = pd.DataFrame(rows)
        return df.sort_values("composite_score", ascending=False)
    
    def get_top_n(self, n: int = 5) -> List[OptimizationResult]:
        """Топ N результатов по composite_score."""
        sorted_results = sorted(
            self.valid_results, 
            key=lambda x: x.composite_score, 
            reverse=True
        )
        return sorted_results[:n]


class VelasOptimizer:
    """
    Оптимизатор параметров индикатора Velas.
    
    Выполняет grid search по 60 пресетам i1-i5,
    оценивает результаты и выбирает лучший.
    """
    
    def __init__(
        self,
        df: pd.DataFrame,
        symbol: str = "BTCUSDT",
        timeframe: str = "1h",
        opt_config: OptimizationConfig = None,
        tpsl_config: TPSLConfig = None,
        filter_config: FilterConfig = None,
        initial_capital: float = 10000.0,
    ):
        """
        Args:
            df: DataFrame с OHLCV данными
            symbol: Торговая пара
            timeframe: Таймфрейм
            opt_config: Конфигурация оптимизации
            tpsl_config: Конфигурация TP/SL
            filter_config: Конфигурация фильтров
            initial_capital: Начальный капитал
        """
        self.df = df.copy()
        self.symbol = symbol
        self.timeframe = timeframe
        self.opt_config = opt_config or OptimizationConfig()
        self.tpsl_config = tpsl_config or TPSLConfig()
        self.filter_config = filter_config or FilterConfig()
        self.initial_capital = initial_capital
        
        # Валидация данных
        self._validate_data()
        
        logger.info(
            f"VelasOptimizer initialized: {symbol} {timeframe}, "
            f"{len(df)} bars, {len(self.opt_config.preset_indices)} presets to test"
        )
    
    def _validate_data(self):
        """Валидация входных данных."""
        required_cols = ["open", "high", "low", "close", "volume"]
        missing = [c for c in required_cols if c not in self.df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")
        
        if len(self.df) < 100:
            raise ValueError(f"Not enough data: {len(self.df)} bars, need at least 100")
    
    def _run_single_backtest(self, preset_index: int) -> OptimizationResult:
        """
        Запуск бэктеста для одного пресета.
        
        Args:
            preset_index: Индекс пресета (0-59)
            
        Returns:
            OptimizationResult
        """
        preset = VELAS_PRESETS_60[preset_index]
        
        try:
            # Конфигурация бэктеста
            config = BacktestConfig(
                symbol=self.symbol,
                timeframe=self.timeframe,
                preset=preset,
                tpsl_config=self.tpsl_config,
                filter_config=self.filter_config,
                initial_capital=self.initial_capital,
                cascade_stop=True,
                close_on_opposite_signal=True,
            )
            
            # Запуск бэктеста
            engine = BacktestEngine(config)
            result = engine.run(self.df)
            
            # Создаём результат
            opt_result = OptimizationResult(
                preset=preset,
                backtest_result=result,
                metrics=result.metrics,
            )
            
            # Валидация и скоринг
            self._validate_result(opt_result)
            if opt_result.is_valid:
                self._calculate_score(opt_result)
            
            return opt_result
            
        except Exception as e:
            logger.error(f"Backtest failed for preset {preset_index}: {e}")
            # Возвращаем невалидный результат
            return OptimizationResult(
                preset=preset,
                backtest_result=None,
                metrics=BacktestMetrics(),
                is_valid=False,
                invalid_reasons=[f"Backtest error: {str(e)}"],
            )
    
    def _validate_result(self, result: OptimizationResult):
        """
        Проверка результата на соответствие минимальным требованиям.
        
        Args:
            result: Результат для валидации
        """
        cfg = self.opt_config
        metrics = result.metrics
        reasons = []
        
        # Минимум сделок
        if metrics.total_trades < cfg.min_trades:
            reasons.append(f"trades={metrics.total_trades} < {cfg.min_trades}")
        
        # Win Rate TP1
        if metrics.win_rate_tp1 < cfg.min_win_rate_tp1:
            reasons.append(f"TP1_WR={metrics.win_rate_tp1:.1f}% < {cfg.min_win_rate_tp1}%")
        
        # Sharpe Ratio (не слишком низкий, не слишком высокий)
        if metrics.sharpe_ratio < cfg.min_sharpe:
            reasons.append(f"Sharpe={metrics.sharpe_ratio:.2f} < {cfg.min_sharpe}")
        if metrics.sharpe_ratio > cfg.max_sharpe:
            reasons.append(f"Sharpe={metrics.sharpe_ratio:.2f} > {cfg.max_sharpe} (overfitting?)")
        
        # Profit Factor
        if metrics.profit_factor < cfg.min_profit_factor:
            reasons.append(f"PF={metrics.profit_factor:.2f} < {cfg.min_profit_factor}")
        
        # Max Drawdown
        if metrics.max_drawdown_percent > cfg.max_drawdown:
            reasons.append(f"DD={metrics.max_drawdown_percent:.1f}% > {cfg.max_drawdown}%")
        
        result.invalid_reasons = reasons
        result.is_valid = len(reasons) == 0
    
    def _calculate_score(self, result: OptimizationResult):
        """
        Расчёт composite score для валидного результата.
        
        Score = weighted average of normalized metrics.
        
        Args:
            result: Результат для скоринга
        """
        cfg = self.opt_config
        m = result.metrics
        
        # Нормализация метрик в диапазон 0-100
        
        # Sharpe: 1.0-3.0 → 0-100
        sharpe_norm = min(100, max(0, (m.sharpe_ratio - 1.0) / 2.0 * 100))
        
        # Profit Factor: 1.0-3.0 → 0-100
        pf_norm = min(100, max(0, (m.profit_factor - 1.0) / 2.0 * 100))
        
        # Win Rate TP1: 50-90% → 0-100
        wr_norm = min(100, max(0, (m.win_rate_tp1 - 50) / 40 * 100))
        
        # Drawdown: 0-20% → 100-0 (меньше = лучше)
        dd_norm = min(100, max(0, (20 - m.max_drawdown_percent) / 20 * 100))
        
        # Взвешенная сумма
        score = (
            cfg.weight_sharpe * sharpe_norm +
            cfg.weight_profit_factor * pf_norm +
            cfg.weight_win_rate_tp1 * wr_norm +
            cfg.weight_drawdown * dd_norm
        )
        
        result.composite_score = score
    
    def run_grid_search(self, parallel: bool = True) -> GridSearchResult:
        """
        Запуск grid search по всем пресетам.
        
        Args:
            parallel: Использовать многопоточность
            
        Returns:
            GridSearchResult
        """
        start_time = time.time()
        preset_indices = self.opt_config.preset_indices
        
        logger.info(f"Starting grid search: {len(preset_indices)} presets")
        
        # Инициализация результата
        result = GridSearchResult(
            symbol=self.symbol,
            timeframe=self.timeframe,
            start_date=self.df.index[0] if isinstance(self.df.index[0], datetime) 
                       else pd.Timestamp(self.df.index[0]),
            end_date=self.df.index[-1] if isinstance(self.df.index[-1], datetime)
                     else pd.Timestamp(self.df.index[-1]),
            total_bars=len(self.df),
            total_presets_tested=len(preset_indices),
        )
        
        # Выполнение бэктестов
        if parallel and len(preset_indices) > 1:
            all_results = self._run_parallel(preset_indices)
        else:
            all_results = self._run_sequential(preset_indices)
        
        # Сортировка и фильтрация
        result.all_results = all_results
        result.valid_results = [r for r in all_results if r.is_valid]
        result.valid_presets_count = len(result.valid_results)
        
        # Лучший результат
        if result.valid_results:
            result.best_result = max(
                result.valid_results, 
                key=lambda x: x.composite_score
            )
        
        result.execution_time_sec = time.time() - start_time
        
        logger.info(
            f"Grid search complete: {result.valid_presets_count}/{result.total_presets_tested} valid, "
            f"best score={result.best_result.composite_score:.2f if result.best_result else 0:.2f}, "
            f"time={result.execution_time_sec:.1f}s"
        )
        
        return result
    
    def _run_sequential(self, preset_indices: List[int]) -> List[OptimizationResult]:
        """Последовательное выполнение бэктестов."""
        results = []
        for i, idx in enumerate(preset_indices):
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i + 1}/{len(preset_indices)}")
            results.append(self._run_single_backtest(idx))
        return results
    
    def _run_parallel(self, preset_indices: List[int]) -> List[OptimizationResult]:
        """
        Параллельное выполнение бэктестов.
        
        Note: Для полной параллелизации нужно использовать ProcessPoolExecutor,
        но для простоты используем последовательное выполнение с ThreadPoolExecutor.
        """
        # Временно используем последовательное выполнение
        # TODO: Implement proper multiprocessing
        logger.warning("Parallel execution not implemented, falling back to sequential")
        return self._run_sequential(preset_indices)
    
    def get_best_preset(self, n: int = 1) -> List[OptimizationResult]:
        """
        Получить лучшие пресеты после grid search.
        
        Args:
            n: Количество лучших пресетов
            
        Returns:
            Список лучших OptimizationResult
        """
        # Нужно сначала запустить grid_search
        raise NotImplementedError("Call run_grid_search() first, then use result.get_top_n()")


def optimize_preset(
    df: pd.DataFrame,
    symbol: str = "BTCUSDT",
    timeframe: str = "1h",
    opt_config: OptimizationConfig = None,
    tpsl_config: TPSLConfig = None,
) -> GridSearchResult:
    """
    Удобная функция для оптимизации пресета.
    
    Args:
        df: OHLCV данные
        symbol: Торговая пара
        timeframe: Таймфрейм
        opt_config: Конфигурация оптимизации
        tpsl_config: Конфигурация TP/SL
        
    Returns:
        GridSearchResult
    """
    optimizer = VelasOptimizer(
        df=df,
        symbol=symbol,
        timeframe=timeframe,
        opt_config=opt_config,
        tpsl_config=tpsl_config,
    )
    return optimizer.run_grid_search()
