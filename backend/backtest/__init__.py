# VELAS Trading System - Backtest Module
# Бэктестинг движок, сделки, метрики

__version__ = "0.3.0"

from .trade import Trade, TradeResult, TradeStatus
from .metrics import (
    BacktestMetrics,
    calculate_win_rate,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_profit_factor,
    calculate_equity_curve,
)
from .engine import BacktestEngine, BacktestConfig, BacktestResult

__all__ = [
    "Trade",
    "TradeResult",
    "TradeStatus",
    "BacktestMetrics",
    "calculate_win_rate",
    "calculate_sharpe_ratio",
    "calculate_max_drawdown",
    "calculate_profit_factor",
    "calculate_equity_curve",
    "BacktestEngine",
    "BacktestConfig",
    "BacktestResult",
]
