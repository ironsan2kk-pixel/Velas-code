"""
VELAS Backtest Module - бэктестинг и оптимизация.

Компоненты:
- BacktestEngine: Движок бэктестинга
- BacktestMetrics: Расчёт метрик
- Trade: Модель сделки
"""

from .engine import BacktestEngine
from .metrics import BacktestMetrics
from .trade import Trade, TradeResult, TradeStatus

__all__ = [
    "BacktestEngine",
    "BacktestMetrics",
    "Trade",
    "TradeResult",
    "TradeStatus",
]
