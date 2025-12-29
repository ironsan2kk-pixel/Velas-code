"""
VELAS Backtest Module - бэктестинг и оптимизация.

Компоненты:
- BacktestEngine: Движок бэктестинга
- BacktestMetrics: Расчёт метрик
- Trade: Модель сделки
"""

from .engine import BacktestEngine, BacktestConfig, BacktestResult
from .metrics import BacktestMetrics
from .trade import Trade, TradeResult, TradeStatus, TradeDirection

__all__ = [
    "BacktestEngine",
    "BacktestConfig",
    "BacktestResult",
    "BacktestMetrics",
    "Trade",
    "TradeResult",
    "TradeStatus",
    "TradeDirection",
]
