"""
VELAS Walk-Forward Analysis - продвинутая оптимизация против переобучения.

Принцип:
1. Разделяем данные на периоды: Train (6 мес) + Test (2 мес)
2. Оптимизируем на Train, тестируем на Test (UNSEEN данные!)
3. Сдвигаем окно на 2 месяца, повторяем
4. Проверяем стабильность результатов между периодами

Схема:
    |---Train (6mo)---|---Test (2mo)---|
                      |---Train (6mo)---|---Test (2mo)---|
                                        |---Train (6mo)---|---Test (2mo)---|

Использование:
    wf = WalkForwardAnalyzer(df, symbol, timeframe)
    result = wf.run()
    print(result.aggregated_metrics)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import pandas as pd
import numpy as np
import logging

from ..core.velas_indicator import VelasPreset, VELAS_PRESETS_60
from ..core.tpsl import TPSLConfig
from ..core.signals import FilterConfig
from .engine import BacktestEngine, BacktestConfig, BacktestResult
from .metrics import BacktestMetrics
from .optimizer import VelasOptimizer, OptimizationConfig, GridSearchResult, OptimizationResult


logger = logging.getLogger(__name__)


@dataclass
class WalkForwardConfig:
    """Конфигурация Walk-Forward Analysis."""
    
    # Периоды (в месяцах)
    train_months: int = 6        # Период обучения
    test_months: int = 2         # Период тестирования (Out-of-Sample)
    step_months: int = 2         # Шаг сдвига окна
    
    # Минимальное количество периодов
    min_periods: int = 4
    
    # Конфигурация оптимизации
    opt_config: OptimizationConfig = None
    
    # TP/SL конфигурация
    tpsl_config: TPSLConfig = None
    
    # Фильтры
    filter_config: FilterConfig = None
    
    # Капитал
    initial_capital: float = 10000.0
    
    def __post_init__(self):
        if self.opt_config is None:
            self.opt_config = OptimizationConfig()
        if self.tpsl_config is None:
            self.tpsl_config = TPSLConfig()
        if self.filter_config is None:
            self.filter_config = FilterConfig()


@dataclass
class WalkForwardPeriod:
    """Результат одного периода Walk-Forward."""
    
    # Период
    period_index: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    
    # Количество данных
    train_bars: int = 0
    test_bars: int = 0
    
    # Результат оптимизации на Train
    train_result: GridSearchResult = None
    best_preset: VelasPreset = None
    
    # Результат бэктеста на Test (Out-of-Sample)
    test_result: BacktestResult = None
    test_metrics: BacktestMetrics = None
    
    # Comparison
    train_score: float = 0.0    # Score на train
    test_score: float = 0.0     # Score на test (OOS)
    efficiency: float = 0.0     # test_score / train_score (должен быть > 0.5)
    
    def to_dict(self) -> dict:
        """Конвертация в словарь."""
        return {
            "period": self.period_index,
            "train_start": self.train_start.strftime("%Y-%m-%d") if self.train_start else None,
            "train_end": self.train_end.strftime("%Y-%m-%d") if self.train_end else None,
            "test_start": self.test_start.strftime("%Y-%m-%d") if self.test_start else None,
            "test_end": self.test_end.strftime("%Y-%m-%d") if self.test_end else None,
            "train_bars": self.train_bars,
            "test_bars": self.test_bars,
            "best_preset_index": self.best_preset.index if self.best_preset else None,
            "best_preset_i1": self.best_preset.i1 if self.best_preset else None,
            "best_preset_i2": self.best_preset.i2 if self.best_preset else None,
            "best_preset_i3": self.best_preset.i3 if self.best_preset else None,
            "best_preset_i4": self.best_preset.i4 if self.best_preset else None,
            "best_preset_i5": self.best_preset.i5 if self.best_preset else None,
            "train_score": round(self.train_score, 2),
            "test_score": round(self.test_score, 2),
            "efficiency": round(self.efficiency, 2),
            "test_trades": self.test_metrics.total_trades if self.test_metrics else 0,
            "test_win_rate": round(self.test_metrics.win_rate, 2) if self.test_metrics else 0,
            "test_win_rate_tp1": round(self.test_metrics.win_rate_tp1, 2) if self.test_metrics else 0,
            "test_sharpe": round(self.test_metrics.sharpe_ratio, 2) if self.test_metrics else 0,
            "test_pf": round(self.test_metrics.profit_factor, 2) if self.test_metrics else 0,
            "test_max_dd": round(self.test_metrics.max_drawdown_percent, 2) if self.test_metrics else 0,
            "test_pnl": round(self.test_metrics.total_pnl_percent, 2) if self.test_metrics else 0,
        }


@dataclass
class WalkForwardResult:
    """Полный результат Walk-Forward Analysis."""
    
    # Параметры
    symbol: str
    timeframe: str
    config: WalkForwardConfig
    
    # Данные
    data_start: datetime = None
    data_end: datetime = None
    total_bars: int = 0
    
    # Периоды
    periods: List[WalkForwardPeriod] = field(default_factory=list)
    total_periods: int = 0
    successful_periods: int = 0
    
    # Агрегированные метрики (по Test периодам)
    aggregated_metrics: BacktestMetrics = None
    
    # Стабильность
    avg_efficiency: float = 0.0          # Средняя эффективность
    min_efficiency: float = 0.0          # Минимальная эффективность
    preset_stability: float = 0.0        # Насколько часто выбирается один пресет
    most_common_preset_index: int = -1   # Самый частый пресет
    
    # Статус
    is_robust: bool = False              # Прошёл ли WF проверку
    failure_reasons: List[str] = field(default_factory=list)
    
    # Время
    execution_time_sec: float = 0.0
    
    def to_dataframe(self) -> pd.DataFrame:
        """Результаты периодов в DataFrame."""
        rows = [p.to_dict() for p in self.periods]
        return pd.DataFrame(rows)
    
    def get_preset_frequency(self) -> Dict[int, int]:
        """Частота выбора каждого пресета."""
        freq = {}
        for p in self.periods:
            if p.best_preset:
                idx = p.best_preset.index
                freq[idx] = freq.get(idx, 0) + 1
        return dict(sorted(freq.items(), key=lambda x: -x[1]))


class WalkForwardAnalyzer:
    """
    Walk-Forward Analyzer для проверки устойчивости стратегии.
    
    Ключевые принципы:
    1. Оптимизация ТОЛЬКО на Train данных
    2. Тестирование на UNSEEN Test данных
    3. Проверка стабильности между периодами
    4. Отклонение нестабильных результатов
    """
    
    def __init__(
        self,
        df: pd.DataFrame,
        symbol: str = "BTCUSDT",
        timeframe: str = "1h",
        config: WalkForwardConfig = None,
    ):
        """
        Args:
            df: DataFrame с OHLCV данными (индекс = datetime)
            symbol: Торговая пара
            timeframe: Таймфрейм
            config: Конфигурация WF анализа
        """
        self.df = df.copy()
        self.symbol = symbol
        self.timeframe = timeframe
        self.config = config or WalkForwardConfig()
        
        # Убедимся что индекс datetime
        if not isinstance(self.df.index, pd.DatetimeIndex):
            if "timestamp" in self.df.columns:
                self.df.set_index("timestamp", inplace=True)
            elif "datetime" in self.df.columns:
                self.df.set_index("datetime", inplace=True)
            self.df.index = pd.to_datetime(self.df.index)
        
        self.df.sort_index(inplace=True)
        
        # Валидация
        self._validate_data()
        
        logger.info(
            f"WalkForwardAnalyzer initialized: {symbol} {timeframe}, "
            f"{len(df)} bars from {self.df.index[0]} to {self.df.index[-1]}"
        )
    
    def _validate_data(self):
        """Валидация данных."""
        required_cols = ["open", "high", "low", "close", "volume"]
        missing = [c for c in required_cols if c not in self.df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")
        
        # Проверка достаточности данных
        total_months = self._calculate_months_span()
        min_months_needed = (
            self.config.train_months + 
            self.config.test_months + 
            self.config.step_months * (self.config.min_periods - 1)
        )
        
        if total_months < min_months_needed:
            raise ValueError(
                f"Not enough data: {total_months:.1f} months available, "
                f"need at least {min_months_needed} months for {self.config.min_periods} periods"
            )
    
    def _calculate_months_span(self) -> float:
        """Расчёт количества месяцев данных."""
        delta = self.df.index[-1] - self.df.index[0]
        return delta.days / 30.0
    
    def _generate_periods(self) -> List[Tuple[datetime, datetime, datetime, datetime]]:
        """
        Генерация периодов Train/Test.
        
        Returns:
            List of (train_start, train_end, test_start, test_end)
        """
        periods = []
        
        data_start = self.df.index[0]
        data_end = self.df.index[-1]
        
        train_duration = timedelta(days=self.config.train_months * 30)
        test_duration = timedelta(days=self.config.test_months * 30)
        step_duration = timedelta(days=self.config.step_months * 30)
        
        current_start = data_start
        
        while True:
            train_start = current_start
            train_end = train_start + train_duration
            test_start = train_end
            test_end = test_start + test_duration
            
            # Проверяем что test_end не выходит за пределы данных
            if test_end > data_end:
                break
            
            periods.append((train_start, train_end, test_start, test_end))
            
            # Сдвигаем на step
            current_start += step_duration
        
        return periods
    
    def run(self) -> WalkForwardResult:
        """
        Запуск Walk-Forward Analysis.
        
        Returns:
            WalkForwardResult
        """
        import time
        start_time = time.time()
        
        # Инициализация результата
        result = WalkForwardResult(
            symbol=self.symbol,
            timeframe=self.timeframe,
            config=self.config,
            data_start=self.df.index[0],
            data_end=self.df.index[-1],
            total_bars=len(self.df),
        )
        
        # Генерация периодов
        periods = self._generate_periods()
        result.total_periods = len(periods)
        
        logger.info(f"Walk-Forward: {len(periods)} periods to analyze")
        
        if len(periods) < self.config.min_periods:
            result.failure_reasons.append(
                f"Not enough periods: {len(periods)} < {self.config.min_periods}"
            )
            return result
        
        # Анализ каждого периода
        all_test_trades = []
        
        for idx, (train_start, train_end, test_start, test_end) in enumerate(periods):
            logger.info(f"Period {idx + 1}/{len(periods)}: Train {train_start.date()} - {train_end.date()}, Test {test_start.date()} - {test_end.date()}")
            
            period_result = self._analyze_period(
                idx, train_start, train_end, test_start, test_end
            )
            result.periods.append(period_result)
            
            if period_result.test_result and period_result.test_result.trades:
                all_test_trades.extend(period_result.test_result.trades)
                result.successful_periods += 1
        
        # Агрегированные метрики
        if all_test_trades:
            from .metrics import calculate_all_metrics
            result.aggregated_metrics = calculate_all_metrics(
                all_test_trades, 
                self.config.initial_capital
            )
        
        # Расчёт стабильности
        self._calculate_stability(result)
        
        # Проверка робастности
        self._check_robustness(result)
        
        result.execution_time_sec = time.time() - start_time
        
        logger.info(
            f"Walk-Forward complete: {result.successful_periods}/{result.total_periods} periods, "
            f"robust={result.is_robust}, efficiency={result.avg_efficiency:.2f}"
        )
        
        return result
    
    def _analyze_period(
        self,
        period_idx: int,
        train_start: datetime,
        train_end: datetime,
        test_start: datetime,
        test_end: datetime,
    ) -> WalkForwardPeriod:
        """
        Анализ одного периода Walk-Forward.
        
        Args:
            period_idx: Индекс периода
            train_start, train_end: Границы train
            test_start, test_end: Границы test
            
        Returns:
            WalkForwardPeriod
        """
        period = WalkForwardPeriod(
            period_index=period_idx,
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
        )
        
        try:
            # Выделение данных
            train_df = self.df[(self.df.index >= train_start) & (self.df.index < train_end)]
            test_df = self.df[(self.df.index >= test_start) & (self.df.index < test_end)]
            
            period.train_bars = len(train_df)
            period.test_bars = len(test_df)
            
            if len(train_df) < 100 or len(test_df) < 20:
                logger.warning(f"Period {period_idx}: insufficient data (train={len(train_df)}, test={len(test_df)})")
                return period
            
            # Оптимизация на Train
            optimizer = VelasOptimizer(
                df=train_df,
                symbol=self.symbol,
                timeframe=self.timeframe,
                opt_config=self.config.opt_config,
                tpsl_config=self.config.tpsl_config,
                filter_config=self.config.filter_config,
                initial_capital=self.config.initial_capital,
            )
            
            train_result = optimizer.run_grid_search(parallel=False)
            period.train_result = train_result
            
            if not train_result.best_result:
                logger.warning(f"Period {period_idx}: no valid preset found on train")
                return period
            
            period.best_preset = train_result.best_result.preset
            period.train_score = train_result.best_result.composite_score
            
            # Тестирование лучшего пресета на Test (Out-of-Sample)
            test_config = BacktestConfig(
                symbol=self.symbol,
                timeframe=self.timeframe,
                preset=period.best_preset,
                tpsl_config=self.config.tpsl_config,
                filter_config=self.config.filter_config,
                initial_capital=self.config.initial_capital,
                cascade_stop=True,
                close_on_opposite_signal=True,
            )
            
            engine = BacktestEngine(test_config)
            test_result = engine.run(test_df)
            
            period.test_result = test_result
            period.test_metrics = test_result.metrics
            
            # Расчёт score на test
            period.test_score = self._calculate_test_score(test_result.metrics)
            
            # Эффективность = test_score / train_score
            if period.train_score > 0:
                period.efficiency = period.test_score / period.train_score
            
            logger.info(
                f"Period {period_idx}: preset={period.best_preset.index}, "
                f"train_score={period.train_score:.1f}, test_score={period.test_score:.1f}, "
                f"efficiency={period.efficiency:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Period {period_idx} failed: {e}")
        
        return period
    
    def _calculate_test_score(self, metrics: BacktestMetrics) -> float:
        """Расчёт score для test периода (аналог optimizer scoring)."""
        if metrics.total_trades == 0:
            return 0.0
        
        cfg = self.config.opt_config
        
        # Нормализация метрик
        sharpe_norm = min(100, max(0, (metrics.sharpe_ratio - 1.0) / 2.0 * 100))
        pf_norm = min(100, max(0, (metrics.profit_factor - 1.0) / 2.0 * 100))
        wr_norm = min(100, max(0, (metrics.win_rate_tp1 - 50) / 40 * 100))
        dd_norm = min(100, max(0, (20 - metrics.max_drawdown_percent) / 20 * 100))
        
        score = (
            cfg.weight_sharpe * sharpe_norm +
            cfg.weight_profit_factor * pf_norm +
            cfg.weight_win_rate_tp1 * wr_norm +
            cfg.weight_drawdown * dd_norm
        )
        
        return score
    
    def _calculate_stability(self, result: WalkForwardResult):
        """Расчёт метрик стабильности."""
        valid_periods = [p for p in result.periods if p.efficiency > 0]
        
        if not valid_periods:
            return
        
        efficiencies = [p.efficiency for p in valid_periods]
        result.avg_efficiency = np.mean(efficiencies)
        result.min_efficiency = np.min(efficiencies)
        
        # Частота пресетов
        preset_freq = result.get_preset_frequency()
        if preset_freq:
            result.most_common_preset_index = list(preset_freq.keys())[0]
            most_common_count = list(preset_freq.values())[0]
            result.preset_stability = most_common_count / len(valid_periods)
    
    def _check_robustness(self, result: WalkForwardResult):
        """Проверка робастности результатов."""
        reasons = []
        
        # Минимум успешных периодов
        if result.successful_periods < self.config.min_periods:
            reasons.append(
                f"Not enough successful periods: {result.successful_periods} < {self.config.min_periods}"
            )
        
        # Средняя эффективность > 0.5 (test должен быть хотя бы 50% от train)
        if result.avg_efficiency < 0.5:
            reasons.append(
                f"Low average efficiency: {result.avg_efficiency:.2f} < 0.5"
            )
        
        # Минимальная эффективность > 0.3
        if result.min_efficiency < 0.3:
            reasons.append(
                f"Too low min efficiency: {result.min_efficiency:.2f} < 0.3"
            )
        
        # Агрегированные метрики
        if result.aggregated_metrics:
            m = result.aggregated_metrics
            opt = self.config.opt_config
            
            if m.win_rate_tp1 < opt.min_win_rate_tp1:
                reasons.append(f"Aggregated TP1 WR too low: {m.win_rate_tp1:.1f}% < {opt.min_win_rate_tp1}%")
            
            if m.sharpe_ratio < opt.min_sharpe:
                reasons.append(f"Aggregated Sharpe too low: {m.sharpe_ratio:.2f} < {opt.min_sharpe}")
            
            if m.max_drawdown_percent > opt.max_drawdown:
                reasons.append(f"Aggregated DD too high: {m.max_drawdown_percent:.1f}% > {opt.max_drawdown}%")
        
        result.failure_reasons = reasons
        result.is_robust = len(reasons) == 0


def run_walk_forward(
    df: pd.DataFrame,
    symbol: str = "BTCUSDT",
    timeframe: str = "1h",
    config: WalkForwardConfig = None,
) -> WalkForwardResult:
    """
    Удобная функция для запуска Walk-Forward Analysis.
    
    Args:
        df: OHLCV данные
        symbol: Торговая пара
        timeframe: Таймфрейм
        config: Конфигурация WF
        
    Returns:
        WalkForwardResult
    """
    analyzer = WalkForwardAnalyzer(df, symbol, timeframe, config)
    return analyzer.run()
