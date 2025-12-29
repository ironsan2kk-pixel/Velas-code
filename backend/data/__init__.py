"""
VELAS Data Module - работа с данными.

Компоненты:
- BinanceRestClient: REST API клиент
- CandleStorage: Хранилище свечей (Parquet)
"""

from .binance_rest import BinanceRestClient, KlineData, BinanceInterval
from .storage import CandleStorage

__all__ = [
    "BinanceRestClient",
    "KlineData",
    "BinanceInterval",
    "CandleStorage",
]
