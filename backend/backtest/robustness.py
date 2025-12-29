"""
VELAS Robustness Checker - проверка устойчивости параметров.

Принцип:
1. Берём "лучший" пресет
2. Тестируем соседние параметры (±10-20%)
3. Если результаты сильно падают = хрупкий результат
4. Если соседи тоже хорошие = робастный результат

Цель: Отсеять переобученные результаты, которые работают
только при точных параметрах.

Использование:
    checker = RobustnessChecker(df, best_preset, config)
    result = checker.check()
    print(result.is_robust)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any, Set
import pandas as pd
import numpy as np
import logging
import itertools

from ..core.velas_indicator import VelasPreset, VELAS_PRESETS_60
from ..core.tpsl import TPSLConfig
from ..core.signals import FilterConfig
from .engine import BacktestEngine, BacktestConfig, BacktestResult
from .metrics import BacktestMetrics


logger = logging.getLogger(__name__)


@dataclass
class RobustnessConfig:
    """Конфигурация проверки робастности."""
    
    # Вариации параметров
    variation_percent: float = 15.0      # ±15% от базового значения
    min_variation_steps: int = 3         # Минимум 3 шага (base, -15%, +15%)
    
    # Допустимая деградация
    max_score_degradation: float = 30.0  # Максимальное падение score (%)
    max_metric_degradation: float = 25.0 # Максимальное падение отдельных метрик (%)
    
    # Минимальный порог для соседей
    min_neighbors_valid: float = 0.7     # 70% соседей должны быть валидными
    
    # Какие параметры варьировать
    vary_i1: bool = True
    vary_i2: bool = True
    vary_i3: bool = True
    vary_i4: bool = True
    vary_i5: bool = True
    
    # Конфигурация бэктеста
    tpsl_config: TPSLConfig = None
    filter_config: FilterConfig = None
    initial_capital: float = 10000.0
    
    # Минимальные требования
    min_trades: int = 20
    
    def __post_init__(self):
        if self.tpsl_config is None:
            self.tpsl_config = TPSLConfig()
        if self.filter_config is None:
            self.filter_config = FilterConfig()


@dataclass
class NeighborResult:
    """Результат бэктеста для одного соседнего пресета."""
    
    # Параметры
    i1: int
    i2: int
    i3: float
    i4: float
    i5: float
    
    # Расстояние от базового (в %)
    distance_i1: float = 0.0
    distance_i2: float = 0.0
    distance_i3: float = 0.0
    distance_i4: float = 0.0
    distance_i5: float = 0.0
    total_distance: float = 0.0
    
    # Результаты
    backtest_result: BacktestResult = None
    metrics: BacktestMetrics = None
    
    # Score сравнение
    score: float = 0.0
    base_score: float = 0.0
    score_degradation: float = 0.0  # % падения от base
    
    # Статус
    is_valid: bool = False
    is_profitable: bool = False
    
    def to_dict(self) -> dict:
        return {
            "i1": self.i1,
            "i2": self.i2,
            "i3": self.i3,
            "i4": self.i4,
            "i5": self.i5,
            "distance_total": round(self.total_distance, 2),
            "score": round(self.score, 2),
            "score_degradation": round(self.score_degradation, 2),
            "is_valid": self.is_valid,
            "trades": self.metrics.total_trades if self.metrics else 0,
            "win_rate": round(self.metrics.win_rate, 2) if self.metrics else 0,
            "sharpe": round(self.metrics.sharpe_ratio, 2) if self.metrics else 0,
            "pnl": round(self.metrics.total_pnl_percent, 2) if self.metrics else 0,
        }


@dataclass
class RobustnessResult:
    """Полный результат проверки робастности."""
    
    # Базовый пресет
    base_preset: VelasPreset = None
    base_score: float = 0.0
    base_metrics: BacktestMetrics = None
    
    # Соседи
    neighbors: List[NeighborResult] = field(default_factory=list)
    total_neighbors_tested: int = 0
    valid_neighbors_count: int = 0
    profitable_neighbors_count: int = 0
    
    # Анализ
    avg_neighbor_score: float = 0.0
    min_neighbor_score: float = 0.0
    max_neighbor_score: float = 0.0
    score_std: float = 0.0               # Стандартное отклонение scores
    
    avg_score_degradation: float = 0.0   # Средняя деградация
    max_score_degradation: float = 0.0   # Максимальная деградация
    
    # Статус
    is_robust: bool = False
    robustness_score: float = 0.0        # 0-100
    failure_reasons: List[str] = field(default_factory=list)
    
    # Время
    execution_time_sec: float = 0.0
    
    def to_dataframe(self) -> pd.DataFrame:
        """Соседи в DataFrame."""
        rows = [n.to_dict() for n in self.neighbors]
        return pd.DataFrame(rows)
    
    def get_heatmap_data(self) -> Dict[str, Any]:
        """Данные для heatmap визуализации."""
        return {
            "base": {
                "i1": self.base_preset.i1,
                "i2": self.base_preset.i2,
                "i3": self.base_preset.i3,
                "i4": self.base_preset.i4,
                "i5": self.base_preset.i5,
                "score": self.base_score,
            },
            "neighbors": [n.to_dict() for n in self.neighbors],
            "is_robust": self.is_robust,
            "robustness_score": self.robustness_score,
        }


class RobustnessChecker:
    """
    Проверка робастности параметров стратегии.
    
    Тестирует соседние параметры (±10-20%) и проверяет,
    что результаты не падают резко.
    
    Робастный результат = результат, который работает
    не только при точных параметрах, но и рядом.
    """
    
    def __init__(
        self,
        df: pd.DataFrame,
        base_preset: VelasPreset,
        symbol: str = "BTCUSDT",
        timeframe: str = "1h",
        config: RobustnessConfig = None,
        base_score: float = None,
        base_metrics: BacktestMetrics = None,
    ):
        """
        Args:
            df: DataFrame с OHLCV данными
            base_preset: Базовый пресет для проверки
            symbol: Торговая пара
            timeframe: Таймфрейм
            config: Конфигурация проверки
            base_score: Score базового пресета (если уже известен)
            base_metrics: Метрики базового пресета (если уже известны)
        """
        self.df = df.copy()
        self.base_preset = base_preset
        self.symbol = symbol
        self.timeframe = timeframe
        self.config = config or RobustnessConfig()
        self.base_score = base_score
        self.base_metrics = base_metrics
        
        logger.info(
            f"RobustnessChecker initialized: preset={base_preset.index}, "
            f"variation=±{self.config.variation_percent}%"
        )
    
    def _generate_neighbor_params(self) -> List[Tuple[int, int, float, float, float]]:
        """
        Генерация соседних параметров для тестирования.
        
        Returns:
            List of (i1, i2, i3, i4, i5) tuples
        """
        cfg = self.config
        base = self.base_preset
        var_pct = cfg.variation_percent / 100.0
        
        # Генерация вариаций для каждого параметра
        def get_variations(value, is_int: bool = False) -> List:
            """Генерация вариаций параметра."""
            low = value * (1 - var_pct)
            high = value * (1 + var_pct)
            
            if is_int:
                low = max(1, int(low))
                high = int(high) + 1
                return sorted(set([low, int(value), high]))
            else:
                mid = value
                return [round(low, 2), round(mid, 2), round(high, 2)]
        
        # Варианты для каждого параметра
        i1_vars = get_variations(base.i1, is_int=True) if cfg.vary_i1 else [base.i1]
        i2_vars = get_variations(base.i2, is_int=True) if cfg.vary_i2 else [base.i2]
        i3_vars = get_variations(base.i3) if cfg.vary_i3 else [base.i3]
        i4_vars = get_variations(base.i4) if cfg.vary_i4 else [base.i4]
        i5_vars = get_variations(base.i5) if cfg.vary_i5 else [base.i5]
        
        # Все комбинации (кроме базовой)
        all_combos = list(itertools.product(i1_vars, i2_vars, i3_vars, i4_vars, i5_vars))
        
        # Исключаем базовую комбинацию
        base_combo = (base.i1, base.i2, base.i3, base.i4, base.i5)
        neighbors = [c for c in all_combos if c != base_combo]
        
        logger.info(f"Generated {len(neighbors)} neighbor combinations to test")
        
        return neighbors
    
    def _calculate_distance(
        self, 
        i1: int, i2: int, i3: float, i4: float, i5: float
    ) -> Tuple[float, float, float, float, float, float]:
        """
        Расчёт расстояния от базового пресета.
        
        Returns:
            (d_i1, d_i2, d_i3, d_i4, d_i5, total_distance)
        """
        base = self.base_preset
        
        d_i1 = abs(i1 - base.i1) / base.i1 * 100 if base.i1 != 0 else 0
        d_i2 = abs(i2 - base.i2) / base.i2 * 100 if base.i2 != 0 else 0
        d_i3 = abs(i3 - base.i3) / base.i3 * 100 if base.i3 != 0 else 0
        d_i4 = abs(i4 - base.i4) / base.i4 * 100 if base.i4 != 0 else 0
        d_i5 = abs(i5 - base.i5) / base.i5 * 100 if base.i5 != 0 else 0
        
        # Euclidean distance
        total = np.sqrt(d_i1**2 + d_i2**2 + d_i3**2 + d_i4**2 + d_i5**2)
        
        return d_i1, d_i2, d_i3, d_i4, d_i5, total
    
    def _calculate_score(self, metrics: BacktestMetrics) -> float:
        """Расчёт score для метрик."""
        if metrics.total_trades < self.config.min_trades:
            return 0.0
        
        # Нормализация
        sharpe_norm = min(100, max(0, (metrics.sharpe_ratio - 1.0) / 2.0 * 100))
        pf_norm = min(100, max(0, (metrics.profit_factor - 1.0) / 2.0 * 100))
        wr_norm = min(100, max(0, (metrics.win_rate_tp1 - 50) / 40 * 100))
        dd_norm = min(100, max(0, (20 - metrics.max_drawdown_percent) / 20 * 100))
        
        # Веса (как в optimizer)
        return 0.30 * sharpe_norm + 0.25 * pf_norm + 0.25 * wr_norm + 0.20 * dd_norm
    
    def _run_backtest(
        self, 
        i1: int, i2: int, i3: float, i4: float, i5: float
    ) -> Tuple[BacktestResult, BacktestMetrics, float]:
        """
        Запуск бэктеста для одной комбинации параметров.
        
        Returns:
            (backtest_result, metrics, score)
        """
        # Создаём кастомный пресет с индексом базового (для совместимости)
        # Используем индекс 0-59 чтобы пройти валидацию
        preset = VelasPreset(
            index=min(59, max(0, self.base_preset.index)),  # Валидный индекс
            i1=i1,
            i2=i2,
            i3=i3,
            i4=i4,
            i5=i5,
        )
        
        config = BacktestConfig(
            symbol=self.symbol,
            timeframe=self.timeframe,
            preset=preset,
            tpsl_config=self.config.tpsl_config,
            filter_config=self.config.filter_config,
            initial_capital=self.config.initial_capital,
            cascade_stop=True,
            close_on_opposite_signal=True,
        )
        
        engine = BacktestEngine(config)
        result = engine.run(self.df)
        
        score = self._calculate_score(result.metrics)
        
        return result, result.metrics, score
    
    def check(self) -> RobustnessResult:
        """
        Запуск проверки робастности.
        
        Returns:
            RobustnessResult
        """
        import time
        start_time = time.time()
        
        result = RobustnessResult(
            base_preset=self.base_preset,
        )
        
        # Если base_score не передан, считаем
        if self.base_score is None or self.base_metrics is None:
            logger.info("Running base preset backtest...")
            _, base_metrics, base_score = self._run_backtest(
                self.base_preset.i1,
                self.base_preset.i2,
                self.base_preset.i3,
                self.base_preset.i4,
                self.base_preset.i5,
            )
            result.base_score = base_score
            result.base_metrics = base_metrics
        else:
            result.base_score = self.base_score
            result.base_metrics = self.base_metrics
        
        # Генерация соседей
        neighbors = self._generate_neighbor_params()
        result.total_neighbors_tested = len(neighbors)
        
        # Тестирование соседей
        valid_scores = []
        
        for idx, (i1, i2, i3, i4, i5) in enumerate(neighbors):
            if (idx + 1) % 20 == 0:
                logger.info(f"Testing neighbor {idx + 1}/{len(neighbors)}")
            
            try:
                bt_result, metrics, score = self._run_backtest(i1, i2, i3, i4, i5)
                
                # Расстояние от базы
                d_i1, d_i2, d_i3, d_i4, d_i5, total_dist = self._calculate_distance(
                    i1, i2, i3, i4, i5
                )
                
                # Деградация score
                degradation = 0.0
                if result.base_score > 0:
                    degradation = (result.base_score - score) / result.base_score * 100
                
                neighbor = NeighborResult(
                    i1=i1, i2=i2, i3=i3, i4=i4, i5=i5,
                    distance_i1=d_i1,
                    distance_i2=d_i2,
                    distance_i3=d_i3,
                    distance_i4=d_i4,
                    distance_i5=d_i5,
                    total_distance=total_dist,
                    backtest_result=bt_result,
                    metrics=metrics,
                    score=score,
                    base_score=result.base_score,
                    score_degradation=degradation,
                    is_valid=metrics.total_trades >= self.config.min_trades,
                    is_profitable=metrics.total_pnl_percent > 0,
                )
                
                result.neighbors.append(neighbor)
                
                if neighbor.is_valid:
                    result.valid_neighbors_count += 1
                    valid_scores.append(score)
                
                if neighbor.is_profitable:
                    result.profitable_neighbors_count += 1
                    
            except Exception as e:
                logger.warning(f"Neighbor test failed for ({i1},{i2},{i3},{i4},{i5}): {e}")
        
        # Статистика по scores
        if valid_scores:
            result.avg_neighbor_score = np.mean(valid_scores)
            result.min_neighbor_score = np.min(valid_scores)
            result.max_neighbor_score = np.max(valid_scores)
            result.score_std = np.std(valid_scores)
            
            # Деградация
            degradations = [n.score_degradation for n in result.neighbors if n.is_valid]
            if degradations:
                result.avg_score_degradation = np.mean(degradations)
                result.max_score_degradation = np.max(degradations)
        
        # Проверка робастности
        self._evaluate_robustness(result)
        
        result.execution_time_sec = time.time() - start_time
        
        logger.info(
            f"Robustness check complete: {result.valid_neighbors_count}/{result.total_neighbors_tested} valid, "
            f"robust={result.is_robust}, score={result.robustness_score:.1f}"
        )
        
        return result
    
    def _evaluate_robustness(self, result: RobustnessResult):
        """Оценка робастности результатов."""
        cfg = self.config
        reasons = []
        
        # Процент валидных соседей
        if result.total_neighbors_tested > 0:
            valid_ratio = result.valid_neighbors_count / result.total_neighbors_tested
            if valid_ratio < cfg.min_neighbors_valid:
                reasons.append(
                    f"Too few valid neighbors: {valid_ratio:.1%} < {cfg.min_neighbors_valid:.1%}"
                )
        
        # Максимальная деградация score
        if result.max_score_degradation > cfg.max_score_degradation:
            reasons.append(
                f"Score degrades too much: {result.max_score_degradation:.1f}% > {cfg.max_score_degradation}%"
            )
        
        # Средняя деградация
        if result.avg_score_degradation > cfg.max_score_degradation * 0.7:
            reasons.append(
                f"Avg score degradation too high: {result.avg_score_degradation:.1f}%"
            )
        
        # Стандартное отклонение (слишком большое = нестабильно)
        if result.score_std > 20:
            reasons.append(
                f"Scores too variable: std={result.score_std:.1f}"
            )
        
        result.failure_reasons = reasons
        result.is_robust = len(reasons) == 0
        
        # Robustness score (0-100)
        if result.total_neighbors_tested > 0 and result.base_score > 0:
            valid_ratio = result.valid_neighbors_count / result.total_neighbors_tested
            avg_score_ratio = result.avg_neighbor_score / result.base_score if result.base_score > 0 else 0
            stability = 1 - min(1, result.score_std / 50)
            
            result.robustness_score = (
                0.4 * valid_ratio * 100 +
                0.4 * avg_score_ratio * 100 +
                0.2 * stability * 100
            )


def check_robustness(
    df: pd.DataFrame,
    preset: VelasPreset,
    symbol: str = "BTCUSDT",
    timeframe: str = "1h",
    config: RobustnessConfig = None,
) -> RobustnessResult:
    """
    Удобная функция для проверки робастности.
    
    Args:
        df: OHLCV данные
        preset: Пресет для проверки
        symbol: Торговая пара
        timeframe: Таймфрейм
        config: Конфигурация
        
    Returns:
        RobustnessResult
    """
    checker = RobustnessChecker(df, preset, symbol, timeframe, config)
    return checker.check()


@dataclass 
class FullOptimizationResult:
    """Полный результат оптимизации с WF + Robustness."""
    
    symbol: str
    timeframe: str
    
    # Walk-Forward
    wf_result: Any = None  # WalkForwardResult
    
    # Robustness (для лучшего пресета из WF)
    robustness_result: RobustnessResult = None
    
    # Финальный пресет
    final_preset: VelasPreset = None
    
    # Статус
    is_valid: bool = False
    reasons: List[str] = field(default_factory=list)
    
    # Финальные метрики
    final_metrics: BacktestMetrics = None


def full_optimization(
    df: pd.DataFrame,
    symbol: str = "BTCUSDT",
    timeframe: str = "1h",
) -> FullOptimizationResult:
    """
    Полная оптимизация: Walk-Forward + Robustness check.
    
    1. Запускает Walk-Forward Analysis
    2. Берёт лучший пресет
    3. Проверяет его робастность
    4. Возвращает финальный результат
    
    Args:
        df: OHLCV данные
        symbol: Торговая пара
        timeframe: Таймфрейм
        
    Returns:
        FullOptimizationResult
    """
    from .walk_forward import WalkForwardAnalyzer, WalkForwardConfig
    
    result = FullOptimizationResult(symbol=symbol, timeframe=timeframe)
    
    # 1. Walk-Forward Analysis
    logger.info("Step 1: Walk-Forward Analysis")
    wf_config = WalkForwardConfig()
    wf_analyzer = WalkForwardAnalyzer(df, symbol, timeframe, wf_config)
    wf_result = wf_analyzer.run()
    result.wf_result = wf_result
    
    if not wf_result.is_robust:
        result.reasons = wf_result.failure_reasons
        logger.warning(f"Walk-Forward failed: {result.reasons}")
        return result
    
    # 2. Получаем лучший пресет
    best_preset_idx = wf_result.most_common_preset_index
    if best_preset_idx < 0:
        result.reasons = ["No valid preset from Walk-Forward"]
        return result
    
    best_preset = VELAS_PRESETS_60[best_preset_idx]
    
    # 3. Robustness check
    logger.info(f"Step 2: Robustness check for preset {best_preset_idx}")
    rob_config = RobustnessConfig()
    rob_checker = RobustnessChecker(df, best_preset, symbol, timeframe, rob_config)
    rob_result = rob_checker.check()
    result.robustness_result = rob_result
    
    if not rob_result.is_robust:
        result.reasons = rob_result.failure_reasons
        logger.warning(f"Robustness check failed: {result.reasons}")
        return result
    
    # 4. Успех!
    result.final_preset = best_preset
    result.final_metrics = wf_result.aggregated_metrics
    result.is_valid = True
    
    logger.info(
        f"Full optimization complete: preset={best_preset_idx}, "
        f"WF efficiency={wf_result.avg_efficiency:.2f}, "
        f"robustness={rob_result.robustness_score:.1f}"
    )
    
    return result
