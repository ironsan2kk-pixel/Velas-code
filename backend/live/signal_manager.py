"""
VELAS Signal Manager - управление сигналами в реальном времени.

Ответственность:
- Генерация сигналов на основе новых свечей
- Фильтрация и валидация сигналов
- Очередь сигналов для обработки
- Интеграция с Portfolio Manager
"""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

import pandas as pd

# Core imports
import sys
sys.path.insert(0, str(__file__).rsplit("/", 3)[0])

from backend.core.signals import Signal, SignalGenerator, SignalType, FilterConfig
from backend.core.tpsl import TPSLManager, TPSLConfig, TPSLLevels
from backend.core.presets import PresetManager, TradingPreset
from backend.core.volatility import VolatilityAnalyzer, VolatilityRegime


logger = logging.getLogger(__name__)


class SignalStatus(Enum):
    """Статус сигнала."""
    PENDING = "pending"       # Ожидает обработки
    APPROVED = "approved"     # Одобрен для исполнения
    REJECTED = "rejected"     # Отклонён (не прошёл фильтры)
    EXECUTED = "executed"     # Исполнен (позиция открыта)
    EXPIRED = "expired"       # Просрочен
    CANCELLED = "cancelled"   # Отменён


@dataclass
class EnrichedSignal:
    """Расширенный сигнал с TP/SL уровнями и метаданными."""
    
    signal: Signal
    tpsl_levels: TPSLLevels
    preset: TradingPreset
    
    status: SignalStatus = SignalStatus.PENDING
    rejection_reason: str = ""
    
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    @property
    def symbol(self) -> str:
        return self.signal.symbol
    
    @property
    def timeframe(self) -> str:
        return self.signal.timeframe
    
    @property
    def signal_id(self) -> str:
        return self.signal.signal_id
    
    @property
    def is_long(self) -> bool:
        return self.signal.is_long
    
    @property
    def entry_price(self) -> float:
        return self.signal.entry_price
    
    @property
    def tp_prices(self) -> List[float]:
        return self.tpsl_levels.tp_prices
    
    @property
    def sl_price(self) -> float:
        return self.tpsl_levels.sl_price
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def is_pending(self) -> bool:
        return self.status == SignalStatus.PENDING
    
    def approve(self) -> None:
        """Одобрить сигнал."""
        self.status = SignalStatus.APPROVED
        self.processed_at = datetime.now()
    
    def reject(self, reason: str) -> None:
        """Отклонить сигнал."""
        self.status = SignalStatus.REJECTED
        self.rejection_reason = reason
        self.processed_at = datetime.now()
    
    def execute(self) -> None:
        """Отметить как исполненный."""
        self.status = SignalStatus.EXECUTED
        self.processed_at = datetime.now()
    
    def expire(self) -> None:
        """Отметить как просроченный."""
        self.status = SignalStatus.EXPIRED
        self.processed_at = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            "signal": self.signal.to_dict(),
            "tp_prices": self.tp_prices,
            "sl_price": self.sl_price,
            "preset_id": self.preset.preset_id if self.preset else "",
            "status": self.status.value,
            "rejection_reason": self.rejection_reason,
            "signal_id": self.signal_id,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class SignalManager:
    """
    Менеджер сигналов для Live торговли.
    
    Использование:
        manager = SignalManager(preset_manager)
        
        # Подписываемся на новые сигналы
        manager.on_signal = lambda signal: print(f"New signal: {signal}")
        
        # Обрабатываем новую свечу
        signal = await manager.process_candle("BTCUSDT", "1h", candle_df)
        
        # Получаем очередь сигналов
        pending = manager.get_pending_signals()
    """
    
    def __init__(
        self,
        preset_manager: PresetManager,
        filter_config: FilterConfig = None,
        signal_ttl_minutes: int = 30,  # Время жизни сигнала
        max_queue_size: int = 100,
    ):
        """
        Args:
            preset_manager: Менеджер пресетов
            filter_config: Конфигурация фильтров
            signal_ttl_minutes: Время жизни сигнала в минутах
            max_queue_size: Максимальный размер очереди
        """
        self.preset_manager = preset_manager
        self.filter_config = filter_config or FilterConfig()
        self.signal_ttl = timedelta(minutes=signal_ttl_minutes)
        self.max_queue_size = max_queue_size
        
        # Очередь сигналов
        self._signal_queue: deque = deque(maxlen=max_queue_size)
        
        # Кэш генераторов по символу/таймфрейму
        self._generators: Dict[str, SignalGenerator] = {}
        
        # TPSL менеджеры по пресету
        self._tpsl_managers: Dict[str, TPSLManager] = {}
        
        # Callback для новых сигналов
        self.on_signal: Optional[Callable[[EnrichedSignal], None]] = None
        
        # История последних сигналов по паре (для дедупликации)
        self._last_signals: Dict[str, datetime] = {}
        self._signal_cooldown = timedelta(minutes=5)  # Минимум между сигналами
    
    def _get_cache_key(self, symbol: str, timeframe: str) -> str:
        """Получить ключ кэша."""
        return f"{symbol}_{timeframe}"
    
    def _get_generator(
        self,
        symbol: str,
        timeframe: str,
        preset: TradingPreset,
    ) -> SignalGenerator:
        """Получить или создать генератор сигналов."""
        key = self._get_cache_key(symbol, timeframe)
        
        if key not in self._generators:
            self._generators[key] = SignalGenerator(
                preset=preset.to_velas_preset(),
                filter_config=self.filter_config,
                symbol=symbol,
                timeframe=timeframe,
            )
        
        return self._generators[key]
    
    def _get_tpsl_manager(self, preset: TradingPreset) -> TPSLManager:
        """Получить или создать TPSL менеджер."""
        preset_id = preset.preset_id
        
        if preset_id not in self._tpsl_managers:
            self._tpsl_managers[preset_id] = TPSLManager(
                config=preset.to_tpsl_config()
            )
        
        return self._tpsl_managers[preset_id]
    
    def _is_on_cooldown(self, symbol: str) -> bool:
        """Проверить находится ли пара на кулдауне."""
        last_signal = self._last_signals.get(symbol)
        if last_signal is None:
            return False
        
        return datetime.now() - last_signal < self._signal_cooldown
    
    def process_candle(
        self,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame,
        volatility_regime: VolatilityRegime = None,
    ) -> Optional[EnrichedSignal]:
        """
        Обработать новую свечу и проверить на сигнал.
        
        Args:
            symbol: Символ пары
            timeframe: Таймфрейм
            df: DataFrame с OHLCV данными (минимум 100 свечей)
            volatility_regime: Текущий режим волатильности (или автоопределение)
            
        Returns:
            EnrichedSignal если есть сигнал, иначе None
        """
        # Проверяем кулдаун
        if self._is_on_cooldown(symbol):
            return None
        
        # Определяем режим волатильности если не указан
        if volatility_regime is None:
            analyzer = VolatilityAnalyzer(df)
            volatility_regime = analyzer.get_regime()
        
        # Получаем адаптивный пресет
        preset = self.preset_manager.get(symbol, timeframe, volatility_regime.value)
        
        if preset is None:
            logger.warning(f"No preset found for {symbol}/{timeframe}/{volatility_regime.value}")
            return None
        
        # Получаем генератор и TPSL менеджер
        generator = self._get_generator(symbol, timeframe, preset)
        tpsl_manager = self._get_tpsl_manager(preset)
        
        # Генерируем сигнал
        signal = generator.generate_single(df)
        
        if signal is None:
            return None
        
        # Пропускаем prepare сигналы (только confirmed)
        if not signal.is_confirmed:
            return None
        
        # Рассчитываем TP/SL уровни
        tpsl_levels = tpsl_manager.calculate_levels(
            entry_price=signal.entry_price,
            is_long=signal.is_long,
            atr=signal.atr if hasattr(signal, 'atr') else None,
        )
        
        # Создаём обогащённый сигнал
        enriched = EnrichedSignal(
            signal=signal,
            tpsl_levels=tpsl_levels,
            preset=preset,
            expires_at=datetime.now() + self.signal_ttl,
        )
        
        # Добавляем в очередь
        self._signal_queue.append(enriched)
        
        # Обновляем время последнего сигнала
        self._last_signals[symbol] = datetime.now()
        
        # Вызываем callback
        if self.on_signal:
            try:
                self.on_signal(enriched)
            except Exception as e:
                logger.error(f"Error in on_signal callback: {e}")
        
        logger.info(f"New signal: {enriched.signal_id} - {signal.signal_type.value} @ {signal.entry_price}")
        
        return enriched
    
    async def process_candle_async(
        self,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame,
        volatility_regime: VolatilityRegime = None,
    ) -> Optional[EnrichedSignal]:
        """Асинхронная версия process_candle."""
        return await asyncio.to_thread(
            self.process_candle,
            symbol,
            timeframe,
            df,
            volatility_regime,
        )
    
    def get_pending_signals(self) -> List[EnrichedSignal]:
        """Получить все pending сигналы (не просроченные)."""
        now = datetime.now()
        pending = []
        
        for signal in self._signal_queue:
            if signal.is_pending:
                if signal.expires_at and now > signal.expires_at:
                    signal.expire()
                else:
                    pending.append(signal)
        
        return pending
    
    def get_signal_by_id(self, signal_id: str) -> Optional[EnrichedSignal]:
        """Найти сигнал по ID."""
        for signal in self._signal_queue:
            if signal.signal_id == signal_id:
                return signal
        return None
    
    def approve_signal(self, signal_id: str) -> bool:
        """Одобрить сигнал."""
        signal = self.get_signal_by_id(signal_id)
        if signal and signal.is_pending:
            signal.approve()
            return True
        return False
    
    def reject_signal(self, signal_id: str, reason: str = "") -> bool:
        """Отклонить сигнал."""
        signal = self.get_signal_by_id(signal_id)
        if signal and signal.is_pending:
            signal.reject(reason)
            return True
        return False
    
    def execute_signal(self, signal_id: str) -> bool:
        """Отметить сигнал как исполненный."""
        signal = self.get_signal_by_id(signal_id)
        if signal:
            signal.execute()
            return True
        return False
    
    def clear_expired(self) -> int:
        """Очистить просроченные сигналы."""
        now = datetime.now()
        count = 0
        
        for signal in self._signal_queue:
            if signal.is_pending and signal.expires_at and now > signal.expires_at:
                signal.expire()
                count += 1
        
        return count
    
    def get_queue_stats(self) -> dict:
        """Получить статистику очереди."""
        stats = {
            "total": len(self._signal_queue),
            "pending": 0,
            "approved": 0,
            "rejected": 0,
            "executed": 0,
            "expired": 0,
        }
        
        for signal in self._signal_queue:
            stats[signal.status.value] = stats.get(signal.status.value, 0) + 1
        
        return stats
    
    def clear_generators_cache(self) -> None:
        """Очистить кэш генераторов."""
        self._generators.clear()
        self._tpsl_managers.clear()
    
    def update_filter_config(self, config: FilterConfig) -> None:
        """Обновить конфигурацию фильтров (сбрасывает кэш)."""
        self.filter_config = config
        self.clear_generators_cache()
