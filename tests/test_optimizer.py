"""
Tests for VELAS-04 Optimizer modules.

Тесты:
- optimizer.py — Grid search
- walk_forward.py — Walk-Forward Analysis
- robustness.py — Robustness checker
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.core.velas_indicator import VelasPreset, VELAS_PRESETS_60
from backend.core.tpsl import TPSLConfig
from backend.core.signals import FilterConfig
from backend.backtest.engine import BacktestEngine, BacktestConfig, BacktestResult
from backend.backtest.metrics import BacktestMetrics
from backend.backtest.optimizer import (
    VelasOptimizer,
    OptimizationConfig,
    OptimizationResult,
    GridSearchResult,
    optimize_preset,
)
from backend.backtest.walk_forward import (
    WalkForwardAnalyzer,
    WalkForwardConfig,
    WalkForwardPeriod,
    WalkForwardResult,
    run_walk_forward,
)
from backend.backtest.robustness import (
    RobustnessChecker,
    RobustnessConfig,
    RobustnessResult,
    NeighborResult,
    check_robustness,
    full_optimization,
)


# =============================================================================
# Fixtures
# =============================================================================

def generate_mock_ohlcv(
    bars: int = 1000,
    start_date: datetime = None,
    timeframe_minutes: int = 60,
    base_price: float = 40000.0,
    volatility: float = 0.02,
) -> pd.DataFrame:
    """Генерация мок-данных OHLCV."""
    if start_date is None:
        start_date = datetime(2023, 1, 1)
    
    dates = [start_date + timedelta(minutes=timeframe_minutes * i) for i in range(bars)]
    
    # Симуляция цен с трендами
    np.random.seed(42)
    returns = np.random.normal(0, volatility, bars)
    
    # Добавляем тренды
    trend = np.sin(np.linspace(0, 4 * np.pi, bars)) * 0.1
    returns = returns + trend / bars
    
    prices = [base_price]
    for r in returns[1:]:
        prices.append(prices[-1] * (1 + r))
    
    # OHLCV
    data = []
    for i, price in enumerate(prices):
        noise = abs(np.random.normal(0, volatility * 0.3))
        high = price * (1 + noise)
        low = price * (1 - noise)
        open_price = prices[i - 1] if i > 0 else price
        close = price
        volume = np.random.uniform(100, 1000) * base_price / 1000
        
        data.append({
            "timestamp": dates[i],
            "open": open_price,
            "high": max(high, open_price, close),
            "low": min(low, open_price, close),
            "close": close,
            "volume": volume,
        })
    
    df = pd.DataFrame(data)
    df.set_index("timestamp", inplace=True)
    return df


@pytest.fixture
def short_df():
    """Короткий датасет для быстрых тестов."""
    return generate_mock_ohlcv(bars=500, timeframe_minutes=60)


@pytest.fixture
def medium_df():
    """Средний датасет для стандартных тестов."""
    return generate_mock_ohlcv(bars=2000, timeframe_minutes=60)


@pytest.fixture
def long_df():
    """Длинный датасет для Walk-Forward (18 месяцев)."""
    # 18 месяцев * 30 дней * 24 часа = 12960 часовых баров
    return generate_mock_ohlcv(bars=13000, timeframe_minutes=60)


# =============================================================================
# Test OptimizationConfig
# =============================================================================

class TestOptimizationConfig:
    """Тесты конфигурации оптимизации."""
    
    def test_default_config(self):
        """Тест дефолтной конфигурации."""
        config = OptimizationConfig()
        
        assert config.min_trades == 20
        assert config.min_win_rate_tp1 == 65.0
        assert config.min_sharpe == 1.2
        assert config.max_sharpe == 2.5
        assert config.min_profit_factor == 1.4
        assert config.max_drawdown == 15.0
        assert len(config.preset_indices) == 60
    
    def test_custom_config(self):
        """Тест кастомной конфигурации."""
        config = OptimizationConfig(
            min_trades=50,
            min_sharpe=1.5,
            preset_indices=[0, 1, 2, 3, 4],
        )
        
        assert config.min_trades == 50
        assert config.min_sharpe == 1.5
        assert len(config.preset_indices) == 5
    
    def test_weights_sum(self):
        """Проверка что веса в сумме = 1."""
        config = OptimizationConfig()
        total = (
            config.weight_sharpe +
            config.weight_profit_factor +
            config.weight_win_rate_tp1 +
            config.weight_drawdown
        )
        assert abs(total - 1.0) < 0.001


# =============================================================================
# Test VelasOptimizer
# =============================================================================

class TestVelasOptimizer:
    """Тесты оптимизатора."""
    
    def test_init(self, short_df):
        """Тест инициализации."""
        optimizer = VelasOptimizer(
            df=short_df,
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        assert optimizer.symbol == "BTCUSDT"
        assert optimizer.timeframe == "1h"
        assert len(optimizer.df) == len(short_df)
    
    def test_init_validation(self):
        """Тест валидации данных."""
        # Недостаточно данных
        small_df = generate_mock_ohlcv(bars=50)
        
        with pytest.raises(ValueError, match="Not enough data"):
            VelasOptimizer(df=small_df)
        
        # Отсутствуют колонки
        bad_df = pd.DataFrame({"a": [1, 2, 3]})
        
        with pytest.raises(ValueError, match="Missing columns"):
            VelasOptimizer(df=bad_df)
    
    def test_grid_search_limited(self, short_df):
        """Тест grid search с ограниченным набором пресетов."""
        config = OptimizationConfig(
            preset_indices=[0, 1, 2],  # Только 3 пресета
            min_trades=5,              # Низкий порог для тестов
        )
        
        optimizer = VelasOptimizer(
            df=short_df,
            symbol="BTCUSDT",
            timeframe="1h",
            opt_config=config,
        )
        
        result = optimizer.run_grid_search(parallel=False)
        
        assert isinstance(result, GridSearchResult)
        assert result.total_presets_tested == 3
        assert len(result.all_results) == 3
        assert result.execution_time_sec > 0
    
    def test_optimization_result_structure(self, short_df):
        """Тест структуры результата."""
        config = OptimizationConfig(
            preset_indices=[0],
            min_trades=1,
        )
        
        optimizer = VelasOptimizer(df=short_df, opt_config=config)
        result = optimizer.run_grid_search(parallel=False)
        
        assert len(result.all_results) == 1
        
        opt_result = result.all_results[0]
        assert isinstance(opt_result, OptimizationResult)
        assert opt_result.preset.index == 0
        assert isinstance(opt_result.metrics, BacktestMetrics)
        
        # Check to_dict
        d = opt_result.to_dict()
        assert "preset_index" in d
        assert "composite_score" in d
        assert "is_valid" in d
    
    def test_result_to_dataframe(self, short_df):
        """Тест конвертации в DataFrame."""
        config = OptimizationConfig(
            preset_indices=[0, 1, 2],
            min_trades=1,
        )
        
        optimizer = VelasOptimizer(df=short_df, opt_config=config)
        result = optimizer.run_grid_search(parallel=False)
        
        df = result.to_dataframe()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "composite_score" in df.columns
        assert "is_valid" in df.columns


# =============================================================================
# Test WalkForwardConfig
# =============================================================================

class TestWalkForwardConfig:
    """Тесты конфигурации Walk-Forward."""
    
    def test_default_config(self):
        """Тест дефолтной конфигурации."""
        config = WalkForwardConfig()
        
        assert config.train_months == 6
        assert config.test_months == 2
        assert config.step_months == 2
        assert config.min_periods == 4
    
    def test_custom_config(self):
        """Тест кастомной конфигурации."""
        config = WalkForwardConfig(
            train_months=3,
            test_months=1,
            step_months=1,
        )
        
        assert config.train_months == 3
        assert config.test_months == 1


# =============================================================================
# Test WalkForwardAnalyzer
# =============================================================================

class TestWalkForwardAnalyzer:
    """Тесты Walk-Forward анализатора."""
    
    def test_init(self, long_df):
        """Тест инициализации."""
        analyzer = WalkForwardAnalyzer(
            df=long_df,
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        assert analyzer.symbol == "BTCUSDT"
        assert len(analyzer.df) == len(long_df)
    
    def test_period_generation(self, long_df):
        """Тест генерации периодов."""
        config = WalkForwardConfig(
            train_months=2,
            test_months=1,
            step_months=1,
        )
        
        analyzer = WalkForwardAnalyzer(
            df=long_df,
            config=config,
        )
        
        periods = analyzer._generate_periods()
        
        assert len(periods) >= 4  # Должно быть несколько периодов
        
        # Каждый период: (train_start, train_end, test_start, test_end)
        for train_start, train_end, test_start, test_end in periods:
            assert train_end == test_start  # Без overlap
            assert train_end > train_start
            assert test_end > test_start
    
    def test_insufficient_data(self, short_df):
        """Тест с недостаточным количеством данных."""
        config = WalkForwardConfig(
            train_months=6,
            test_months=2,
            min_periods=4,
        )
        
        with pytest.raises(ValueError, match="Not enough data"):
            WalkForwardAnalyzer(df=short_df, config=config)
    
    def test_run_quick(self, long_df):
        """Быстрый тест запуска (ограниченные пресеты)."""
        # Ограничиваем пресеты для скорости
        opt_config = OptimizationConfig(
            preset_indices=[0, 1],
            min_trades=5,
        )
        
        wf_config = WalkForwardConfig(
            train_months=2,
            test_months=1,
            step_months=1,
            min_periods=2,
            opt_config=opt_config,
        )
        
        analyzer = WalkForwardAnalyzer(
            df=long_df,
            config=wf_config,
        )
        
        result = analyzer.run()
        
        assert isinstance(result, WalkForwardResult)
        assert result.total_periods >= 2
        assert len(result.periods) == result.total_periods
        assert result.execution_time_sec > 0
    
    def test_result_to_dataframe(self, long_df):
        """Тест конвертации результатов в DataFrame."""
        opt_config = OptimizationConfig(preset_indices=[0], min_trades=1)
        wf_config = WalkForwardConfig(
            train_months=2,
            test_months=1,
            min_periods=2,
            opt_config=opt_config,
        )
        
        result = run_walk_forward(long_df, config=wf_config)
        
        df = result.to_dataframe()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == result.total_periods


# =============================================================================
# Test RobustnessConfig
# =============================================================================

class TestRobustnessConfig:
    """Тесты конфигурации робастности."""
    
    def test_default_config(self):
        """Тест дефолтной конфигурации."""
        config = RobustnessConfig()
        
        assert config.variation_percent == 15.0
        assert config.max_score_degradation == 30.0
        assert config.min_neighbors_valid == 0.7
    
    def test_parameter_flags(self):
        """Тест флагов параметров."""
        config = RobustnessConfig(
            vary_i1=True,
            vary_i2=False,
            vary_i3=True,
            vary_i4=False,
            vary_i5=True,
        )
        
        assert config.vary_i1 is True
        assert config.vary_i2 is False


# =============================================================================
# Test RobustnessChecker
# =============================================================================

class TestRobustnessChecker:
    """Тесты проверки робастности."""
    
    def test_init(self, medium_df):
        """Тест инициализации."""
        preset = VELAS_PRESETS_60[0]
        
        checker = RobustnessChecker(
            df=medium_df,
            base_preset=preset,
            symbol="BTCUSDT",
        )
        
        assert checker.base_preset == preset
        assert checker.symbol == "BTCUSDT"
    
    def test_neighbor_generation(self, medium_df):
        """Тест генерации соседних параметров."""
        preset = VELAS_PRESETS_60[0]
        
        config = RobustnessConfig(
            vary_i1=True,
            vary_i2=True,
            vary_i3=False,  # Отключаем для уменьшения комбинаций
            vary_i4=False,
            vary_i5=False,
        )
        
        checker = RobustnessChecker(
            df=medium_df,
            base_preset=preset,
            config=config,
        )
        
        neighbors = checker._generate_neighbor_params()
        
        # 3 варианта i1 × 3 варианта i2 - 1 (базовый) = 8
        assert len(neighbors) == 8
    
    def test_distance_calculation(self, medium_df):
        """Тест расчёта расстояния."""
        preset = VELAS_PRESETS_60[0]
        checker = RobustnessChecker(df=medium_df, base_preset=preset)
        
        # Точно базовые параметры = расстояние 0
        d = checker._calculate_distance(preset.i1, preset.i2, preset.i3, preset.i4, preset.i5)
        assert d[-1] == 0.0  # total_distance
        
        # Другие параметры = расстояние > 0
        d2 = checker._calculate_distance(preset.i1 * 2, preset.i2, preset.i3, preset.i4, preset.i5)
        assert d2[-1] > 0
    
    def test_check_limited(self, medium_df):
        """Тест проверки с ограниченными вариациями."""
        preset = VELAS_PRESETS_60[0]
        
        config = RobustnessConfig(
            vary_i1=True,
            vary_i2=False,
            vary_i3=False,
            vary_i4=False,
            vary_i5=False,
            min_trades=1,
        )
        
        checker = RobustnessChecker(
            df=medium_df,
            base_preset=preset,
            config=config,
        )
        
        result = checker.check()
        
        assert isinstance(result, RobustnessResult)
        assert result.base_preset == preset
        assert result.total_neighbors_tested == 2  # -15% и +15% от i1
        assert result.execution_time_sec > 0
    
    def test_result_to_dataframe(self, medium_df):
        """Тест конвертации в DataFrame."""
        preset = VELAS_PRESETS_60[0]
        config = RobustnessConfig(
            vary_i1=True,
            vary_i2=False,
            vary_i3=False,
            vary_i4=False,
            vary_i5=False,
        )
        
        result = check_robustness(medium_df, preset, config=config)
        
        df = result.to_dataframe()
        
        assert isinstance(df, pd.DataFrame)
        assert "score" in df.columns
        assert "score_degradation" in df.columns


# =============================================================================
# Test NeighborResult
# =============================================================================

class TestNeighborResult:
    """Тесты результата соседа."""
    
    def test_to_dict(self):
        """Тест конвертации в словарь."""
        neighbor = NeighborResult(
            i1=50, i2=12, i3=0.5, i4=1.2, i5=1.3,
            score=75.5,
            score_degradation=10.2,
            is_valid=True,
        )
        
        d = neighbor.to_dict()
        
        assert d["i1"] == 50
        assert d["score"] == 75.5
        assert d["is_valid"] is True


# =============================================================================
# Test optimize_preset convenience function
# =============================================================================

class TestOptimizePresetFunction:
    """Тесты удобной функции optimize_preset."""
    
    def test_basic_call(self, short_df):
        """Тест базового вызова."""
        config = OptimizationConfig(
            preset_indices=[0, 1],
            min_trades=1,
        )
        
        result = optimize_preset(
            df=short_df,
            symbol="BTCUSDT",
            timeframe="1h",
            opt_config=config,
        )
        
        assert isinstance(result, GridSearchResult)
        assert result.symbol == "BTCUSDT"
        assert result.timeframe == "1h"


# =============================================================================
# Test run_walk_forward convenience function
# =============================================================================

class TestRunWalkForwardFunction:
    """Тесты удобной функции run_walk_forward."""
    
    def test_basic_call(self, long_df):
        """Тест базового вызова."""
        opt_config = OptimizationConfig(
            preset_indices=[0],
            min_trades=1,
        )
        
        config = WalkForwardConfig(
            train_months=2,
            test_months=1,
            min_periods=2,
            opt_config=opt_config,
        )
        
        result = run_walk_forward(
            df=long_df,
            symbol="ETHUSDT",
            timeframe="2h",
            config=config,
        )
        
        assert isinstance(result, WalkForwardResult)
        assert result.symbol == "ETHUSDT"
        assert result.timeframe == "2h"


# =============================================================================
# Test check_robustness convenience function
# =============================================================================

class TestCheckRobustnessFunction:
    """Тесты удобной функции check_robustness."""
    
    def test_basic_call(self, medium_df):
        """Тест базового вызова."""
        preset = VELAS_PRESETS_60[5]
        
        config = RobustnessConfig(
            vary_i1=True,
            vary_i2=False,
            vary_i3=False,
            vary_i4=False,
            vary_i5=False,
        )
        
        result = check_robustness(
            df=medium_df,
            preset=preset,
            symbol="SOLUSDT",
            config=config,
        )
        
        assert isinstance(result, RobustnessResult)
        assert result.base_preset == preset


# =============================================================================
# Integration tests
# =============================================================================

class TestIntegration:
    """Интеграционные тесты."""
    
    def test_optimizer_then_robustness(self, medium_df):
        """Тест: оптимизация → проверка робастности лучшего."""
        # 1. Оптимизация
        opt_config = OptimizationConfig(
            preset_indices=[0, 1, 2],
            min_trades=5,
        )
        
        optimizer = VelasOptimizer(df=medium_df, opt_config=opt_config)
        grid_result = optimizer.run_grid_search(parallel=False)
        
        if grid_result.best_result:
            best_preset = grid_result.best_result.preset
            best_score = grid_result.best_result.composite_score
            best_metrics = grid_result.best_result.metrics
            
            # 2. Проверка робастности
            rob_config = RobustnessConfig(
                vary_i1=True,
                vary_i2=False,
                vary_i3=False,
                vary_i4=False,
                vary_i5=False,
            )
            
            checker = RobustnessChecker(
                df=medium_df,
                base_preset=best_preset,
                config=rob_config,
                base_score=best_score,
                base_metrics=best_metrics,
            )
            
            rob_result = checker.check()
            
            assert rob_result.base_score == best_score
            assert isinstance(rob_result.robustness_score, float)


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
