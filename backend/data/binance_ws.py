"""
VELAS - Binance WebSocket клиент.

Подключается к Binance WebSocket для получения реальных данных.
"""

import asyncio
import json
from typing import Dict, List, Optional, Callable
from datetime import datetime
import logging

import websockets
from websockets.exceptions import ConnectionClosed

logger = logging.getLogger(__name__)


class BinanceWebSocket:
    """WebSocket клиент для Binance."""
    
    BASE_URL = "wss://stream.binance.com:9443/ws"
    RECONNECT_DELAY = 5  # секунды
    
    def __init__(self, symbols: List[str]):
        self.symbols = [s.lower() for s in symbols]
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        
        # Последние данные
        self.latest_prices: Dict[str, float] = {}
        self.latest_klines: Dict[str, dict] = {}
        
        # Callbacks
        self.on_price_update: Optional[Callable] = None
        self.on_kline_close: Optional[Callable] = None
    
    async def connect(self):
        """Подключение к WebSocket."""
        self.running = True
        
        # Формируем URL для множественных стримов
        streams = []
        for symbol in self.symbols:
            streams.append(f"{symbol}@ticker")  # Тикер для цен
            streams.append(f"{symbol}@kline_1h")  # Свечи 1h
        
        combined_url = f"{self.BASE_URL}/{'/'.join(streams)}"
        
        # Для множества стримов используем combined stream endpoint
        if len(self.symbols) > 1:
            stream_names = "/".join([f"{s}@ticker" for s in self.symbols])
            combined_url = f"wss://stream.binance.com:9443/stream?streams={stream_names}"
        
        logger.info(f"Connecting to Binance WebSocket...")
        
        asyncio.create_task(self._listen())
    
    async def _listen(self):
        """Основной цикл прослушивания."""
        while self.running:
            try:
                # Подключаемся к combined stream
                stream_names = "/".join([f"{s}@ticker" for s in self.symbols])
                url = f"wss://stream.binance.com:9443/stream?streams={stream_names}"
                
                async with websockets.connect(url) as ws:
                    self.ws = ws
                    logger.info("WebSocket connected")
                    
                    while self.running:
                        try:
                            message = await asyncio.wait_for(ws.recv(), timeout=30)
                            await self._handle_message(message)
                        except asyncio.TimeoutError:
                            # Ping для поддержания соединения
                            await ws.ping()
                        except ConnectionClosed:
                            logger.warning("WebSocket connection closed")
                            break
                            
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                
            if self.running:
                logger.info(f"Reconnecting in {self.RECONNECT_DELAY}s...")
                await asyncio.sleep(self.RECONNECT_DELAY)
    
    async def _handle_message(self, message: str):
        """Обработка входящего сообщения."""
        try:
            data = json.loads(message)
            
            # Combined stream format: {"stream": "btcusdt@ticker", "data": {...}}
            if "stream" in data:
                stream = data["stream"]
                payload = data["data"]
                
                if "@ticker" in stream:
                    await self._handle_ticker(payload)
                elif "@kline" in stream:
                    await self._handle_kline(payload)
            else:
                # Single stream format
                if "e" in data:
                    if data["e"] == "24hrTicker":
                        await self._handle_ticker(data)
                    elif data["e"] == "kline":
                        await self._handle_kline(data)
                        
        except Exception as e:
            logger.error(f"Message handling error: {e}")
    
    async def _handle_ticker(self, data: dict):
        """Обработка тикера."""
        symbol = data.get("s", "").upper()
        price = float(data.get("c", 0))  # Last price
        
        if symbol and price > 0:
            self.latest_prices[symbol] = price
            
            if self.on_price_update:
                await self.on_price_update(symbol, price)
    
    async def _handle_kline(self, data: dict):
        """Обработка свечи."""
        kline = data.get("k", {})
        symbol = kline.get("s", "").upper()
        
        kline_data = {
            "symbol": symbol,
            "interval": kline.get("i"),
            "open_time": kline.get("t"),
            "close_time": kline.get("T"),
            "open": float(kline.get("o", 0)),
            "high": float(kline.get("h", 0)),
            "low": float(kline.get("l", 0)),
            "close": float(kline.get("c", 0)),
            "volume": float(kline.get("v", 0)),
            "is_closed": kline.get("x", False),
        }
        
        self.latest_klines[symbol] = kline_data
        
        # Если свеча закрылась
        if kline_data["is_closed"] and self.on_kline_close:
            await self.on_kline_close(symbol, kline_data)
    
    async def get_latest_prices(self) -> Dict[str, float]:
        """Получить последние цены."""
        return self.latest_prices.copy()
    
    async def get_latest_kline(self, symbol: str) -> Optional[dict]:
        """Получить последнюю свечу."""
        return self.latest_klines.get(symbol.upper())
    
    async def disconnect(self):
        """Отключение от WebSocket."""
        self.running = False
        if self.ws:
            await self.ws.close()
            self.ws = None
        logger.info("WebSocket disconnected")


# Mock версия для тестирования без реального подключения
class MockBinanceWebSocket(BinanceWebSocket):
    """Mock WebSocket для тестирования."""
    
    async def connect(self):
        """Имитация подключения."""
        self.running = True
        logger.info("Mock WebSocket connected")
        
        # Генерация фейковых цен
        import random
        base_prices = {
            "BTCUSDT": 95000, "ETHUSDT": 3400, "BNBUSDT": 700,
            "SOLUSDT": 190, "XRPUSDT": 2.1, "ADAUSDT": 0.85,
            "AVAXUSDT": 38, "DOGEUSDT": 0.32, "DOTUSDT": 7.2,
            "MATICUSDT": 0.48, "LINKUSDT": 22, "UNIUSDT": 13.5,
            "ATOMUSDT": 9.5, "LTCUSDT": 105, "ETCUSDT": 26,
            "NEARUSDT": 5.2, "APTUSDT": 9.8, "ARBUSDT": 0.78,
            "OPUSDT": 1.85, "INJUSDT": 24,
        }
        
        for symbol, base in base_prices.items():
            # Добавляем небольшую случайность
            variation = random.uniform(-0.02, 0.02)
            self.latest_prices[symbol] = round(base * (1 + variation), 4)
    
    async def _listen(self):
        """Mock прослушивание."""
        import random
        
        while self.running:
            # Обновляем цены каждые 5 секунд
            for symbol, price in list(self.latest_prices.items()):
                variation = random.uniform(-0.005, 0.005)
                self.latest_prices[symbol] = round(price * (1 + variation), 4)
            
            await asyncio.sleep(5)
    
    async def disconnect(self):
        """Mock отключение."""
        self.running = False
        logger.info("Mock WebSocket disconnected")
