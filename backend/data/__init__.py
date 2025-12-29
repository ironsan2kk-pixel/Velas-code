"""
VELAS Data Module - работа с данными.

Компоненты:
- BinanceREST: REST API клиент
- CandleStorage: Хранилище свечей (Parquet)
"""

from .binance_rest import BinanceREST
from .storage import CandleStorage

__all__ = [
    "BinanceREST",
    "CandleStorage",
]
