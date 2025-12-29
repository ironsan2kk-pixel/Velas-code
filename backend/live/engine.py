"""
VELAS Live Engine - главный движок реальной торговли.

Ответственность:
- Главный цикл обработки
- Координация компонентов (Data, Signals, Portfolio, Tracker)
- WebSocket подключение к Binance
- Восстановление состояния после рестарта
- Генерация уведомлений
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Set
from enum import Enum
import signal as os_signal

import pandas as pd

# Core imports
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])

# Conditional imports - WebSocket может отсутствовать
try:
    from backend.data.binance_ws import BinanceWebSocket, KlineCallback
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False
    BinanceWebSocket = None
    KlineCallback = None

from backend.data.binance_rest import BinanceRestClient
from backend.data.storage import CandleStorage
from backend.core.presets import PresetManager
from backend.core.volatility import VolatilityAnalyzer
from backend.portfolio import PortfolioManager, RiskLimits, Position
from .signal_manager import SignalManager, EnrichedSignal
from .position_tracker import PositionTracker, TrackingEvent, PositionEvent
from .state import StateManager, SystemStatus


logger = logging.getLogger(__name__)


class EngineStatus(Enum):
    """Статус движка."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class EngineConfig:
    """Конфигурация Live Engine."""
    
    # Торговые параметры
    symbols: List[str] = field(default_factory=lambda: [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
        "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT",
        "LINKUSDT", "UNIUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT",
        "NEARUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "INJUSDT",
    ])
    timeframes: List[str] = field(default_factory=lambda: ["30m", "1h", "2h"])
    
    # Режим
    trading_mode: str = "paper"  # "paper" или "live"
    leverage: int = 10
    
    # Риски
    initial_balance: float = 10000.0
    risk_per_trade: float = 2.0
    max_positions: int = 5
    max_portfolio_heat: float = 8.0
    
    # Пути
    presets_path: str = "data/presets"
    db_path: str = "data/velas.db"
    candles_path: str = "data/candles"
    
    # Таймауты
    ws_reconnect_delay: float = 5.0
    candle_buffer_size: int = 200
    
    # Callbacks
    auto_execute_signals: bool = False  # Авто-исполнение сигналов
    
    def to_dict(self) -> dict:
        return {
            "symbols": self.symbols,
            "timeframes": self.timeframes,
            "trading_mode": self.trading_mode,
            "leverage": self.leverage,
            "initial_balance": self.initial_balance,
            "risk_per_trade": self.risk_per_trade,
            "max_positions": self.max_positions,
            "max_portfolio_heat": self.max_portfolio_heat,
            "auto_execute_signals": self.auto_execute_signals,
        }


class LiveEngine:
    """
    Главный движок реальной торговли.
    
    Использование:
        engine = LiveEngine(config)
        
        # Подписываемся на события
        engine.on_signal = lambda signal: print(f"Signal: {signal}")
        engine.on_position_event = lambda event: print(f"Position: {event}")
        
        # Запускаем
        await engine.start()
        
        # Останавливаем
        await engine.stop()
    """
    
    def __init__(self, config: EngineConfig = None):
        """
        Args:
            config: Конфигурация движка
        """
        self.config = config or EngineConfig()
        self.status = EngineStatus.STOPPED
        
        # Компоненты (инициализируются в _init_components)
        self.state: Optional[StateManager] = None
        self.portfolio: Optional[PortfolioManager] = None
        self.preset_manager: Optional[PresetManager] = None
        self.signal_manager: Optional[SignalManager] = None
        self.position_tracker: Optional[PositionTracker] = None
        self.binance_ws: Optional[BinanceWebSocket] = None
        self.binance_rest: Optional[BinanceRestClient] = None
        self.storage: Optional[CandleStorage] = None
        
        # Буферы данных
        self._candle_buffers: Dict[str, pd.DataFrame] = {}  # symbol_timeframe -> DataFrame
        self._last_prices: Dict[str, float] = {}  # symbol -> price
        
        # Задачи
        self._ws_task: Optional[asyncio.Task] = None
        self._tracker_task: Optional[asyncio.Task] = None
        self._main_loop_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.on_signal: Optional[Callable[[EnrichedSignal], None]] = None
        self.on_position_event: Optional[Callable[[TrackingEvent], None]] = None
        self.on_status_change: Optional[Callable[[EngineStatus], None]] = None
        
        # Control
        self._stop_event = asyncio.Event()
        self._initialized = False
    
    def _set_status(self, status: EngineStatus) -> None:
        """Установить статус."""
        old_status = self.status
        self.status = status
        
        if self.state:
            self.state.set_system_status(SystemStatus(status.value))
        
        if self.on_status_change:
            try:
                self.on_status_change(status)
            except Exception as e:
                logger.error(f"Error in on_status_change callback: {e}")
        
        logger.info(f"Engine status: {old_status.value} -> {status.value}")
    
    async def _init_components(self) -> None:
        """Инициализировать компоненты."""
        logger.info("Initializing components...")
        
        # State Manager (первым для логирования)
        from .state import StateConfig
        self.state = StateManager(StateConfig(db_path=self.config.db_path))
        
        # Preset Manager
        self.preset_manager = PresetManager(self.config.presets_path)
        
        # Portfolio Manager
        risk_limits = RiskLimits(
            max_positions=self.config.max_positions,
            max_portfolio_heat=self.config.max_portfolio_heat,
            risk_per_trade=self.config.risk_per_trade,
        )
        self.portfolio = PortfolioManager(
            balance=self.config.initial_balance,
            risk_limits=risk_limits,
            leverage=self.config.leverage,
        )
        
        # Signal Manager
        self.signal_manager = SignalManager(
            preset_manager=self.preset_manager,
        )
        self.signal_manager.on_signal = self._on_new_signal
        
        # Position Tracker
        self.position_tracker = PositionTracker(
            portfolio_manager=self.portfolio,
            cascade_stop=True,
            breakeven_after_tp=1,
        )
        self.position_tracker.on_event = self._on_position_event
        
        # Binance REST & WebSocket
        self.binance_rest = BinanceRestClient()
        self.binance_ws = BinanceWebSocket()
        
        # Storage
        self.storage = CandleStorage(self.config.candles_path)
        
        self._initialized = True
        logger.info("Components initialized")
    
    async def _restore_state(self) -> None:
        """Восстановить состояние после рестарта."""
        logger.info("Restoring state...")
        
        # Загружаем открытые позиции из БД
        open_positions = self.state.get_open_positions()
        
        for pos_data in open_positions:
            position = Position(
                id=pos_data["id"],
                symbol=pos_data["symbol"],
                timeframe=pos_data["timeframe"],
                preset_id=pos_data.get("preset_id", ""),
                direction=pos_data["direction"],
                entry_price=pos_data["entry_price"],
                current_price=pos_data.get("current_price", pos_data["entry_price"]),
                tp_prices=pos_data.get("tp_prices", []),
                sl_price=pos_data["sl_price"],
                current_sl=pos_data.get("current_sl", pos_data["sl_price"]),
                quantity=pos_data["quantity"],
                notional_value=pos_data["notional_value"],
                leverage=pos_data.get("leverage", self.config.leverage),
                tp_hits=pos_data.get("tp_hits", []),
                position_remaining=pos_data.get("position_remaining", 100),
                realized_pnl=pos_data.get("realized_pnl", 0),
            )
            
            # Восстанавливаем в портфеле
            self.portfolio._positions[position.symbol] = position
            self.portfolio.heat_tracker.add_position(position.to_position_risk())
            
            logger.info(f"Restored position: {position.symbol} ({position.direction})")
        
        # Восстанавливаем баланс из настроек
        saved_balance = self.state.get_setting("balance")
        if saved_balance:
            self.portfolio.update_balance(saved_balance)
        
        logger.info(f"State restored: {len(open_positions)} positions")
    
    async def _load_historical_data(self) -> None:
        """Загрузить исторические данные для всех пар/таймфреймов."""
        logger.info("Loading historical data...")
        
        for symbol in self.config.symbols:
            for timeframe in self.config.timeframes:
                try:
                    # Сначала пробуем из хранилища
                    df = self.storage.load(symbol, timeframe)
                    
                    if df is None or len(df) < self.config.candle_buffer_size:
                        # Загружаем с Binance
                        df = await self.binance_rest.get_klines_async(
                            symbol=symbol,
                            interval=timeframe,
                            limit=self.config.candle_buffer_size,
                        )
                    
                    if df is not None and len(df) > 0:
                        key = f"{symbol}_{timeframe}"
                        self._candle_buffers[key] = df.tail(self.config.candle_buffer_size)
                        
                        # Обновляем последнюю цену
                        self._last_prices[symbol] = df["close"].iloc[-1]
                        
                except Exception as e:
                    logger.error(f"Error loading data for {symbol}/{timeframe}: {e}")
        
        logger.info(f"Loaded data for {len(self._candle_buffers)} symbol/timeframe pairs")
    
    def _get_buffer_key(self, symbol: str, timeframe: str) -> str:
        """Получить ключ буфера."""
        return f"{symbol}_{timeframe}"
    
    async def _on_kline(
        self,
        symbol: str,
        timeframe: str,
        kline: dict,
        is_closed: bool,
    ) -> None:
        """Обработчик новой свечи от WebSocket."""
        key = self._get_buffer_key(symbol, timeframe)
        
        # Обновляем последнюю цену
        self._last_prices[symbol] = kline["close"]
        
        # Обновляем буфер
        if key in self._candle_buffers:
            df = self._candle_buffers[key]
            
            # Создаём новую строку
            new_row = pd.DataFrame([{
                "timestamp": kline["timestamp"],
                "open": kline["open"],
                "high": kline["high"],
                "low": kline["low"],
                "close": kline["close"],
                "volume": kline["volume"],
            }])
            
            if is_closed:
                # Добавляем закрытую свечу
                self._candle_buffers[key] = pd.concat([df, new_row]).tail(self.config.candle_buffer_size)
                
                # Генерируем сигнал на закрытой свече
                await self._process_closed_candle(symbol, timeframe)
            else:
                # Обновляем текущую свечу (последнюю)
                if len(df) > 0:
                    df.iloc[-1] = new_row.iloc[0]
        
        # Обновляем позиции по текущей цене
        if symbol in [p.symbol for p in self.portfolio.get_all_positions()]:
            self.position_tracker.update_price(
                symbol=symbol,
                price=kline["close"],
                high=kline["high"],
                low=kline["low"],
            )
    
    async def _process_closed_candle(self, symbol: str, timeframe: str) -> None:
        """Обработать закрытую свечу (генерация сигнала)."""
        key = self._get_buffer_key(symbol, timeframe)
        df = self._candle_buffers.get(key)
        
        if df is None or len(df) < 50:
            return
        
        try:
            # Генерируем сигнал
            signal = await self.signal_manager.process_candle_async(
                symbol=symbol,
                timeframe=timeframe,
                df=df,
            )
            
            if signal:
                logger.info(f"New signal generated: {signal.signal_id}")
                
        except Exception as e:
            logger.error(f"Error processing candle {symbol}/{timeframe}: {e}")
    
    def _on_new_signal(self, signal: EnrichedSignal) -> None:
        """Обработчик нового сигнала."""
        # Сохраняем в БД
        self.state.save_signal(signal.to_dict())
        self.state.log_event(
            event_type="signal",
            symbol=signal.symbol,
            message=f"New {signal.signal.signal_type.value} signal",
            data=signal.to_dict(),
        )
        
        # Callback
        if self.on_signal:
            try:
                self.on_signal(signal)
            except Exception as e:
                logger.error(f"Error in on_signal callback: {e}")
        
        # Авто-исполнение если включено
        if self.config.auto_execute_signals:
            asyncio.create_task(self._execute_signal(signal))
    
    def _on_position_event(self, event: TrackingEvent) -> None:
        """Обработчик события позиции."""
        # Сохраняем позицию в БД
        self.state.save_position(event.position.to_dict())
        
        # Логируем событие
        self.state.log_event(
            event_type=event.event_type.value,
            symbol=event.position.symbol,
            message=event.message,
            data=event.to_dict(),
        )
        
        # При закрытии - сохраняем в историю
        if event.event_type in (
            PositionEvent.CLOSED_TP,
            PositionEvent.CLOSED_SL,
            PositionEvent.CLOSED_SIGNAL,
            PositionEvent.CLOSED_MANUAL,
        ):
            self.state.save_trade_history({
                "position_id": event.position.id,
                "signal_id": event.position.signal_id,
                "symbol": event.position.symbol,
                "timeframe": event.position.timeframe,
                "direction": event.position.direction,
                "entry_price": event.position.entry_price,
                "exit_price": event.close_price,
                "quantity": event.position.quantity,
                "notional_value": event.position.notional_value,
                "pnl_percent": event.pnl_percent,
                "pnl_amount": event.pnl_amount,
                "tp_hits": event.position.tp_hits,
                "exit_reason": event.event_type.value,
                "entry_time": event.position.entry_time.isoformat() if event.position.entry_time else "",
                "exit_time": event.timestamp.isoformat(),
            })
            
            # Удаляем из БД позиций
            self.state.delete_position(event.position.id)
            
            # Обновляем баланс
            self.state.set_setting("balance", self.portfolio.balance)
        
        # Callback
        if self.on_position_event:
            try:
                self.on_position_event(event)
            except Exception as e:
                logger.error(f"Error in on_position_event callback: {e}")
    
    async def _execute_signal(self, signal: EnrichedSignal) -> bool:
        """Исполнить сигнал (открыть позицию)."""
        # Проверяем можно ли открыть
        can_open, reason = self.portfolio.can_open_position(signal.symbol)
        
        if not can_open:
            signal.reject(reason)
            self.state.update_signal_status(signal.signal_id, "rejected")
            logger.warning(f"Signal rejected: {signal.signal_id} - {reason}")
            return False
        
        # Рассчитываем размер позиции
        size_info = self.portfolio.calculate_position_size(
            symbol=signal.symbol,
            entry_price=signal.entry_price,
            stop_loss=signal.sl_price,
            direction="long" if signal.is_long else "short",
            leverage=self.config.leverage,
        )
        
        # Открываем позицию
        position = self.portfolio.open_position(
            symbol=signal.symbol,
            timeframe=signal.timeframe,
            direction="long" if signal.is_long else "short",
            entry_price=signal.entry_price,
            tp_prices=signal.tp_prices,
            sl_price=signal.sl_price,
            quantity=size_info["quantity"],
            notional_value=size_info["position_size"],
            leverage=self.config.leverage,
            preset_id=signal.preset.preset_id if signal.preset else "",
        )
        
        if position:
            signal.execute()
            self.state.update_signal_status(signal.signal_id, "executed")
            self.state.save_position(position.to_dict())
            
            logger.info(f"Signal executed: {signal.signal_id} - Position opened")
            return True
        
        return False
    
    async def _start_websocket(self) -> None:
        """Запустить WebSocket подключение."""
        logger.info("Starting WebSocket connection...")
        
        # Формируем список стримов
        streams = []
        for symbol in self.config.symbols:
            for timeframe in self.config.timeframes:
                streams.append(f"{symbol.lower()}@kline_{timeframe}")
        
        # Callback для klines
        async def kline_callback(data: dict):
            if "k" in data:
                k = data["k"]
                await self._on_kline(
                    symbol=k["s"],
                    timeframe=k["i"],
                    kline={
                        "timestamp": datetime.fromtimestamp(k["t"] / 1000),
                        "open": float(k["o"]),
                        "high": float(k["h"]),
                        "low": float(k["l"]),
                        "close": float(k["c"]),
                        "volume": float(k["v"]),
                    },
                    is_closed=k["x"],
                )
        
        # Подключаемся
        await self.binance_ws.connect_streams(streams, kline_callback)
    
    async def _main_loop(self) -> None:
        """Главный цикл обработки."""
        logger.info("Main loop started")
        
        while not self._stop_event.is_set():
            try:
                # Периодические задачи
                await self._periodic_tasks()
                
                # Ждём
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)
        
        logger.info("Main loop stopped")
    
    async def _periodic_tasks(self) -> None:
        """Периодические задачи."""
        # Очищаем просроченные сигналы
        self.signal_manager.clear_expired()
        
        # Сохраняем баланс
        self.state.set_setting("balance", self.portfolio.balance)
    
    # ========== Public API ==========
    
    async def start(self) -> None:
        """Запустить движок."""
        if self.status == EngineStatus.RUNNING:
            logger.warning("Engine is already running")
            return
        
        self._set_status(EngineStatus.STARTING)
        self._stop_event.clear()
        
        try:
            # Инициализация
            if not self._initialized:
                await self._init_components()
            
            # Восстановление состояния
            await self._restore_state()
            
            # Загрузка исторических данных
            await self._load_historical_data()
            
            # Запуск WebSocket
            self._ws_task = asyncio.create_task(self._start_websocket())
            
            # Запуск главного цикла
            self._main_loop_task = asyncio.create_task(self._main_loop())
            
            self._set_status(EngineStatus.RUNNING)
            logger.info("Engine started successfully")
            
        except Exception as e:
            logger.error(f"Error starting engine: {e}")
            self._set_status(EngineStatus.ERROR)
            raise
    
    async def stop(self) -> None:
        """Остановить движок."""
        if self.status == EngineStatus.STOPPED:
            return
        
        self._set_status(EngineStatus.STOPPING)
        self._stop_event.set()
        
        # Отменяем задачи
        if self._ws_task:
            self._ws_task.cancel()
        
        if self._main_loop_task:
            self._main_loop_task.cancel()
        
        # Закрываем WebSocket
        if self.binance_ws:
            await self.binance_ws.close()
        
        # Сохраняем состояние
        if self.state:
            self.state.set_setting("balance", self.portfolio.balance)
            for pos in self.portfolio.get_all_positions():
                self.state.save_position(pos.to_dict())
        
        self._set_status(EngineStatus.STOPPED)
        logger.info("Engine stopped")
    
    async def pause(self) -> None:
        """Поставить на паузу."""
        self._set_status(EngineStatus.PAUSED)
    
    async def resume(self) -> None:
        """Возобновить после паузы."""
        if self.status == EngineStatus.PAUSED:
            self._set_status(EngineStatus.RUNNING)
    
    def execute_signal(self, signal_id: str) -> bool:
        """Исполнить сигнал вручную."""
        signal = self.signal_manager.get_signal_by_id(signal_id)
        if signal and signal.is_pending:
            asyncio.create_task(self._execute_signal(signal))
            return True
        return False
    
    def close_position(self, symbol: str) -> bool:
        """Закрыть позицию вручную."""
        price = self._last_prices.get(symbol, 0)
        if price > 0:
            event = self.position_tracker.close_manual(symbol, price)
            return event is not None
        return False
    
    def get_status(self) -> dict:
        """Получить статус системы."""
        return {
            "status": self.status.value,
            "trading_mode": self.config.trading_mode,
            "portfolio": self.portfolio.get_portfolio_stats() if self.portfolio else {},
            "risk_metrics": self.portfolio.get_risk_metrics().to_dict() if self.portfolio else {},
            "positions": [p.to_dict() for p in self.portfolio.get_all_positions()] if self.portfolio else [],
            "pending_signals": len(self.signal_manager.get_pending_signals()) if self.signal_manager else 0,
            "signal_queue_stats": self.signal_manager.get_queue_stats() if self.signal_manager else {},
        }
    
    def get_config(self) -> dict:
        """Получить конфигурацию."""
        return self.config.to_dict()
