"""
VELAS Live Engine - Главный торговый движок.

Обрабатывает реальные данные, генерирует сигналы и отправляет в Telegram.
"""

import asyncio
import signal
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import logging

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import yaml
from loguru import logger

from backend.core.velas_core import VelasIndicator
from backend.core.signals import SignalGenerator
from backend.data.binance_ws import BinanceWebSocket
from backend.portfolio.manager import PortfolioManager
from backend.telegram.bot import TelegramNotifier
from backend.db.database import SessionLocal
from backend.db.models import PositionModel, SignalModel, SystemLogModel

# Конфигурация логгера
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
    level="INFO",
)
logger.add(
    ROOT / "logs" / "live_engine_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="DEBUG",
)


class LiveEngine:
    """Главный торговый движок VELAS."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.running = False
        
        # Компоненты
        self.ws: Optional[BinanceWebSocket] = None
        self.telegram: Optional[TelegramNotifier] = None
        self.portfolio: Optional[PortfolioManager] = None
        self.signal_generator: Optional[SignalGenerator] = None
        
        # Состояние
        self.latest_prices: Dict[str, float] = {}
        self.open_positions: Dict[int, PositionModel] = {}
        
        # 20 пар
        self.pairs = [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
            "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT",
            "LINKUSDT", "UNIUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT",
            "NEARUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "INJUSDT",
        ]
        
        logger.info("Live Engine initialized")
    
    def _load_config(self, path: str) -> dict:
        """Загрузка конфигурации."""
        config_file = ROOT / path
        if not config_file.exists():
            logger.error(f"Config file not found: {config_file}")
            logger.info("Copy config/config.example.yaml to config/config.yaml")
            sys.exit(1)
        
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    async def start(self):
        """Запуск движка."""
        logger.info("=" * 60)
        logger.info("  VELAS Live Engine Starting...")
        logger.info("=" * 60)
        
        self.running = True
        
        # Инициализация компонентов
        await self._init_components()
        
        # Загрузка открытых позиций
        await self._load_open_positions()
        
        # Запуск основного цикла
        await self._main_loop()
    
    async def _init_components(self):
        """Инициализация всех компонентов."""
        logger.info("Initializing components...")
        
        # Telegram
        if self.config.get("telegram", {}).get("enabled", False):
            try:
                self.telegram = TelegramNotifier(
                    token=self.config["telegram"]["bot_token"],
                    chat_id=self.config["telegram"]["chat_id"],
                )
                await self.telegram.send_message("🚀 VELAS Live Engine запущен")
                logger.info("✅ Telegram connected")
            except Exception as e:
                logger.warning(f"⚠️ Telegram init failed: {e}")
        
        # Portfolio Manager
        self.portfolio = PortfolioManager(
            initial_balance=self.config.get("portfolio", {}).get("initial_balance", 10000),
            max_positions=self.config.get("trading", {}).get("max_positions", 5),
            risk_percent=self.config.get("trading", {}).get("risk_percent", 2.0),
        )
        logger.info("✅ Portfolio Manager initialized")
        
        # Signal Generator
        self.signal_generator = SignalGenerator(
            min_confidence=self.config.get("trading", {}).get("min_confidence", 0.6),
        )
        logger.info("✅ Signal Generator initialized")
        
        # WebSocket
        self.ws = BinanceWebSocket(self.pairs)
        await self.ws.connect()
        logger.info("✅ Binance WebSocket connected")
        
        self._log_to_db("INFO", "LiveEngine", "All components initialized")
    
    async def _load_open_positions(self):
        """Загрузка открытых позиций из БД."""
        db = SessionLocal()
        try:
            positions = db.query(PositionModel).filter(
                PositionModel.status == "open"
            ).all()
            
            for pos in positions:
                self.open_positions[pos.id] = pos
            
            logger.info(f"Loaded {len(self.open_positions)} open positions")
        finally:
            db.close()
    
    async def _main_loop(self):
        """Главный цикл обработки."""
        logger.info("Starting main loop...")
        
        update_interval = self.config.get("system", {}).get("data_update_interval", 5)
        
        while self.running:
            try:
                # Получение последних цен
                self.latest_prices = await self.ws.get_latest_prices()
                
                # Обновление позиций
                await self._update_positions()
                
                # Проверка сигналов (каждые 30 секунд)
                # В реальной системе это будет привязано к закрытию свечей
                
                await asyncio.sleep(update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Main loop error: {e}")
                self._log_to_db("ERROR", "LiveEngine", f"Main loop error: {e}")
                await asyncio.sleep(5)
        
        logger.info("Main loop stopped")
    
    async def _update_positions(self):
        """Обновление открытых позиций."""
        if not self.open_positions:
            return
        
        db = SessionLocal()
        try:
            for pos_id, position in list(self.open_positions.items()):
                symbol = position.symbol
                
                if symbol not in self.latest_prices:
                    continue
                
                current_price = self.latest_prices[symbol]
                position.current_price = current_price
                
                # Расчёт PnL
                if position.side == "LONG":
                    pnl_pct = (current_price - position.entry_price) / position.entry_price * 100
                else:
                    pnl_pct = (position.entry_price - current_price) / position.entry_price * 100
                
                position.unrealized_pnl_percent = round(pnl_pct, 2)
                
                # Проверка TP/SL
                await self._check_tp_sl(position, current_price, db)
                
                # Обновление в БД
                db.merge(position)
            
            db.commit()
            
        finally:
            db.close()
    
    async def _check_tp_sl(self, position: PositionModel, price: float, db):
        """Проверка достижения TP/SL."""
        is_long = position.side == "LONG"
        
        # Проверка SL
        sl_hit = (price <= position.current_sl) if is_long else (price >= position.current_sl)
        if sl_hit:
            await self._close_position(position, "SL", price, db)
            return
        
        # Проверка TP уровней
        tp_levels = [
            (position.tp1_price, position.tp1_hit, "tp1_hit", "TP1", 20),
            (position.tp2_price, position.tp2_hit, "tp2_hit", "TP2", 20),
            (position.tp3_price, position.tp3_hit, "tp3_hit", "TP3", 15),
            (position.tp4_price, position.tp4_hit, "tp4_hit", "TP4", 15),
            (position.tp5_price, position.tp5_hit, "tp5_hit", "TP5", 15),
            (position.tp6_price, position.tp6_hit, "tp6_hit", "TP6", 15),
        ]
        
        for tp_price, is_hit, attr, name, close_pct in tp_levels:
            if is_hit or tp_price is None:
                continue
            
            tp_hit = (price >= tp_price) if is_long else (price <= tp_price)
            if tp_hit:
                setattr(position, attr, True)
                position.position_remaining -= close_pct
                
                # Логика каскадного стопа
                if name == "TP1":
                    position.current_sl = position.entry_price  # Перевод в БУ
                elif name in ["TP2", "TP3", "TP4", "TP5"]:
                    # Каскадный стоп к предыдущему TP
                    prev_tp = getattr(position, f"tp{int(name[-1])-1}_price")
                    if prev_tp:
                        position.current_sl = prev_tp
                
                logger.info(f"🎯 {position.symbol} {name} hit @ {price}")
                
                # Уведомление в Telegram
                if self.telegram:
                    await self.telegram.send_tp_hit(position, name, price)
                
                self._log_to_db("INFO", "LiveEngine", f"{position.symbol} {name} hit @ {price}")
                
                # Если TP6 - закрываем полностью
                if name == "TP6":
                    await self._close_position(position, "TP6", price, db)
                
                break
    
    async def _close_position(self, position: PositionModel, reason: str, price: float, db):
        """Закрытие позиции."""
        position.status = "closed"
        position.close_reason = reason
        position.close_price = price
        position.close_time = datetime.utcnow()
        
        # Финальный PnL
        if position.side == "LONG":
            pnl_pct = (price - position.entry_price) / position.entry_price * 100
        else:
            pnl_pct = (position.entry_price - price) / position.entry_price * 100
        
        position.realized_pnl = round(pnl_pct, 2)
        
        # Удаление из активных
        if position.id in self.open_positions:
            del self.open_positions[position.id]
        
        logger.info(f"📊 {position.symbol} closed @ {price} ({reason}) | PnL: {pnl_pct:.2f}%")
        
        # Уведомление в Telegram
        if self.telegram:
            await self.telegram.send_position_closed(position)
        
        self._log_to_db("INFO", "LiveEngine", f"{position.symbol} closed: {reason} @ {price}")
    
    def _log_to_db(self, level: str, component: str, message: str):
        """Запись лога в БД."""
        db = SessionLocal()
        try:
            log = SystemLogModel(
                level=level,
                component=component,
                message=message,
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to log to DB: {e}")
        finally:
            db.close()
    
    async def stop(self):
        """Остановка движка."""
        logger.info("Stopping Live Engine...")
        self.running = False
        
        if self.ws:
            await self.ws.disconnect()
        
        if self.telegram:
            await self.telegram.send_message("🛑 VELAS Live Engine остановлен")
        
        self._log_to_db("INFO", "LiveEngine", "Engine stopped")
        logger.info("Live Engine stopped")


# Глобальный экземпляр для graceful shutdown
engine: Optional[LiveEngine] = None


def handle_shutdown(signum, frame):
    """Обработчик сигнала завершения."""
    logger.info(f"Received signal {signum}, shutting down...")
    if engine:
        asyncio.create_task(engine.stop())


async def main():
    """Точка входа."""
    global engine
    
    # Обработчики сигналов
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    engine = LiveEngine()
    
    try:
        await engine.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await engine.stop()


if __name__ == "__main__":
    asyncio.run(main())
