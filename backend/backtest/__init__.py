# VELAS Trading System - Backtest Module
# Бэктестинг движок, сделки, метрики, оптимизация

__version__ = "0.4.0"

from .trade import Trade, TradeResult, TradeStatus
from .metrics import (
    BacktestMetrics,
    calculate_win_rate,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_equity_curve,
    calculate_all_metrics,
)
from .engine import BacktestEngine, BacktestConfig, BacktestResult
from .optimizer import (
    VelasOptimizer,
    OptimizationConfig,
    OptimizationResult,
    GridSearchResult,
    optimize_preset,
)
from .walk_forward import (
    WalkForwardAnalyzer,
    WalkForwardConfig,
    WalkForwardPeriod,
    WalkForwardResult,
    run_walk_forward,
)
from .robustness import (
    RobustnessChecker,
    RobustnessConfig,
    RobustnessResult,
    NeighborResult,
    check_robustness,
    full_optimization,
)

__all__ = [
    # Trade
    "Trade",
    "TradeResult",
    "TradeStatus",
    # Metrics
    "BacktestMetrics",
    "calculate_win_rate",
    "calculate_sharpe_ratio",
    "calculate_max_drawdown",
    "calculate_profit_factor",
    "calculate_equity_curve",
    "calculate_all_metrics",
    # Engine
    "BacktestEngine",
    "BacktestConfig",
    "BacktestResult",
    # Optimizer
    "VelasOptimizer",
    "OptimizationConfig",
    "OptimizationResult",
    "GridSearchResult",
    "optimize_preset",
    # Walk-Forward
    "WalkForwardAnalyzer",
    "WalkForwardConfig",
    "WalkForwardPeriod",
    "WalkForwardResult",
    "run_walk_forward",
    # Robustness
    "RobustnessChecker",
    "RobustnessConfig",
    "RobustnessResult",
    "NeighborResult",
    "check_robustness",
    "full_optimization",
]
