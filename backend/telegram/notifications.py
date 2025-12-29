"""
VELAS Notification Manager

Manages all trading notifications and signal distribution.
Integrates Telegram bot with Cornix formatter.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum

from .bot import TelegramBot, TelegramBotMock, BotConfig, BotState
from .cornix import (
    CornixFormatter,
    TradingSignal,
    SignalSide,
    TPHitEvent,
    SLHitEvent,
)


logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Types of notifications."""
    SIGNAL_NEW = "signal_new"
    SIGNAL_CANCELLED = "signal_cancelled"
    TP_HIT = "tp_hit"
    SL_HIT = "sl_hit"
    POSITION_UPDATE = "position_update"
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_INFO = "system_info"
    DAILY_SUMMARY = "daily_summary"


@dataclass
class NotificationSettings:
    """Notification preferences."""
    signal_new: bool = True
    signal_cancelled: bool = True
    tp_hit: bool = True
    sl_hit: bool = True
    position_update: bool = True
    system_error: bool = True
    system_warning: bool = True
    system_info: bool = False
    daily_summary: bool = True
    
    # Silent notifications (no sound)
    silent_tp_hit: bool = False
    silent_position_update: bool = True
    silent_system_info: bool = True


@dataclass
class DailyStats:
    """Daily trading statistics."""
    date: date
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl_percent: float = 0.0
    total_pnl_usd: float = 0.0
    best_trade_pnl: float = 0.0
    best_trade_symbol: str = ""
    worst_trade_pnl: float = 0.0
    worst_trade_symbol: str = ""
    signals_generated: int = 0
    tp_hits: Dict[int, int] = field(default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0})
    sl_hits: int = 0


class NotificationManager:
    """
    Manages all VELAS trading notifications.
    
    Features:
    - Signal formatting with Cornix compatibility
    - Notification filtering by type
    - Daily statistics tracking
    - Error handling and logging
    - Mock mode for testing
    
    Usage:
        config = BotConfig(bot_token="...", chat_id="...")
        manager = NotificationManager(config)
        await manager.start()
        
        # Send a new signal
        signal = TradingSignal(
            symbol="BTCUSDT",
            side=SignalSide.LONG,
            entry_price=42500,
            stop_loss=41225,
            take_profits=[42925, 43350, 43988, 44625, 45900, 47600],
            timeframe="1h",
            preset_id="BTCUSDT_1h_normal"
        )
        await manager.notify_new_signal(signal)
        
        await manager.stop()
    """
    
    def __init__(
        self,
        config: BotConfig,
        settings: Optional[NotificationSettings] = None,
        use_mock: bool = False,
        leverage: int = 10
    ):
        """
        Initialize notification manager.
        
        Args:
            config: Telegram bot configuration
            settings: Notification preferences
            use_mock: Use mock bot for testing
            leverage: Default leverage for signals
        """
        self.config = config
        self.settings = settings or NotificationSettings()
        self.leverage = leverage
        
        # Initialize formatter
        self.formatter = CornixFormatter(leverage=leverage)
        
        # Initialize bot
        if use_mock:
            self.bot = TelegramBotMock(config)
        else:
            self.bot = TelegramBot(config)
        
        # Daily statistics
        self._daily_stats = DailyStats(date=date.today())
        
        # Notification history
        self._notification_history: List[Dict[str, Any]] = []
        self._max_history_size = 1000
    
    @property
    def is_running(self) -> bool:
        """Check if manager is running."""
        return self.bot.is_running
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get notification statistics."""
        return {
            "bot_stats": self.bot.stats,
            "daily_stats": {
                "date": self._daily_stats.date.isoformat(),
                "total_trades": self._daily_stats.total_trades,
                "winning_trades": self._daily_stats.winning_trades,
                "win_rate": (
                    self._daily_stats.winning_trades / self._daily_stats.total_trades * 100
                    if self._daily_stats.total_trades > 0 else 0
                ),
                "total_pnl_percent": self._daily_stats.total_pnl_percent,
                "total_pnl_usd": self._daily_stats.total_pnl_usd,
                "signals_generated": self._daily_stats.signals_generated,
            },
            "notifications_sent": len(self._notification_history),
        }
    
    async def start(self) -> bool:
        """
        Start the notification manager.
        
        Returns:
            True if started successfully
        """
        logger.info("Starting notification manager...")
        
        result = await self.bot.start()
        
        if result:
            logger.info("Notification manager started")
            
            # Send startup notification
            if self.settings.system_info:
                await self._send_notification(
                    NotificationType.SYSTEM_INFO,
                    self.formatter.format_system_alert(
                        "info",
                        "🚀 VELAS Trading System запущена"
                    ),
                    silent=True
                )
        else:
            logger.error("Failed to start notification manager")
        
        return result
    
    async def stop(self) -> None:
        """Stop the notification manager."""
        logger.info("Stopping notification manager...")
        
        # Send daily summary if enabled
        if self.settings.daily_summary and self._daily_stats.total_trades > 0:
            await self.send_daily_summary()
        
        # Send shutdown notification
        if self.settings.system_info:
            await self._send_notification(
                NotificationType.SYSTEM_INFO,
                self.formatter.format_system_alert(
                    "info",
                    "🛑 VELAS Trading System остановлена"
                ),
                silent=True
            )
        
        await self.bot.stop()
        logger.info("Notification manager stopped")
    
    async def notify_new_signal(self, signal: TradingSignal) -> bool:
        """
        Send new trading signal notification.
        
        Args:
            signal: Trading signal data
            
        Returns:
            True if sent successfully
        """
        if not self.settings.signal_new:
            logger.debug("Signal notifications disabled")
            return False
        
        # Update daily stats
        self._daily_stats.signals_generated += 1
        
        # Format and send signal
        formatted = self.formatter.format_new_signal(signal)
        
        result = await self._send_notification(
            NotificationType.SIGNAL_NEW,
            formatted,
            silent=False,
            priority=True,
            metadata={
                "symbol": signal.symbol,
                "side": signal.side.value,
                "entry": signal.entry_price,
                "sl": signal.stop_loss,
                "tps": signal.take_profits,
            }
        )
        
        if result:
            logger.info(f"Signal sent: {signal.symbol} {signal.side.value}")
        
        return result
    
    async def notify_signal_cancelled(
        self,
        symbol: str,
        side: SignalSide,
        reason: str
    ) -> bool:
        """
        Send signal cancellation notification.
        
        Args:
            symbol: Trading pair
            side: Signal direction
            reason: Cancellation reason
            
        Returns:
            True if sent successfully
        """
        if not self.settings.signal_cancelled:
            return False
        
        formatted = self.formatter.format_signal_cancelled(symbol, side, reason)
        
        return await self._send_notification(
            NotificationType.SIGNAL_CANCELLED,
            formatted,
            metadata={"symbol": symbol, "side": side.value, "reason": reason}
        )
    
    async def notify_tp_hit(self, event: TPHitEvent) -> bool:
        """
        Send take profit hit notification.
        
        Args:
            event: TP hit event data
            
        Returns:
            True if sent successfully
        """
        if not self.settings.tp_hit:
            return False
        
        # Update daily stats
        self._daily_stats.tp_hits[event.tp_level] += 1
        
        formatted = self.formatter.format_tp_hit(event)
        
        result = await self._send_notification(
            NotificationType.TP_HIT,
            formatted,
            silent=self.settings.silent_tp_hit,
            metadata={
                "symbol": event.symbol,
                "side": event.side.value,
                "tp_level": event.tp_level,
                "pnl_percent": event.pnl_percent,
            }
        )
        
        if result:
            logger.info(
                f"TP{event.tp_level} hit: {event.symbol} {event.side.value} "
                f"+{event.pnl_percent:.1f}%"
            )
        
        return result
    
    async def notify_sl_hit(self, event: SLHitEvent) -> bool:
        """
        Send stop loss hit notification.
        
        Args:
            event: SL hit event data
            
        Returns:
            True if sent successfully
        """
        if not self.settings.sl_hit:
            return False
        
        # Update daily stats
        self._daily_stats.sl_hits += 1
        self._daily_stats.total_trades += 1
        self._daily_stats.losing_trades += 1
        self._daily_stats.total_pnl_percent += event.pnl_percent
        self._daily_stats.total_pnl_usd += event.pnl_usd
        
        # Track worst trade
        if event.pnl_percent < self._daily_stats.worst_trade_pnl:
            self._daily_stats.worst_trade_pnl = event.pnl_percent
            self._daily_stats.worst_trade_symbol = event.symbol
        
        formatted = self.formatter.format_sl_hit(event)
        
        result = await self._send_notification(
            NotificationType.SL_HIT,
            formatted,
            metadata={
                "symbol": event.symbol,
                "side": event.side.value,
                "pnl_percent": event.pnl_percent,
                "pnl_usd": event.pnl_usd,
            }
        )
        
        if result:
            logger.info(
                f"SL hit: {event.symbol} {event.side.value} "
                f"{event.pnl_percent:.1f}% (${event.pnl_usd:.2f})"
            )
        
        return result
    
    async def notify_position_update(
        self,
        symbol: str,
        side: SignalSide,
        update_type: str,
        details: str
    ) -> bool:
        """
        Send position update notification.
        
        Args:
            symbol: Trading pair
            side: Signal direction
            update_type: Type of update
            details: Update details
            
        Returns:
            True if sent successfully
        """
        if not self.settings.position_update:
            return False
        
        formatted = self.formatter.format_position_update(
            symbol, side, update_type, details
        )
        
        return await self._send_notification(
            NotificationType.POSITION_UPDATE,
            formatted,
            silent=self.settings.silent_position_update,
            metadata={
                "symbol": symbol,
                "side": side.value,
                "update_type": update_type,
            }
        )
    
    async def notify_system_error(self, message: str) -> bool:
        """
        Send system error notification.
        
        Args:
            message: Error message
            
        Returns:
            True if sent successfully
        """
        if not self.settings.system_error:
            return False
        
        formatted = self.formatter.format_system_alert("error", message)
        
        result = await self._send_notification(
            NotificationType.SYSTEM_ERROR,
            formatted,
            priority=True,
            metadata={"message": message}
        )
        
        if result:
            logger.error(f"System error notified: {message}")
        
        return result
    
    async def notify_system_warning(self, message: str) -> bool:
        """
        Send system warning notification.
        
        Args:
            message: Warning message
            
        Returns:
            True if sent successfully
        """
        if not self.settings.system_warning:
            return False
        
        formatted = self.formatter.format_system_alert("warning", message)
        
        return await self._send_notification(
            NotificationType.SYSTEM_WARNING,
            formatted,
            metadata={"message": message}
        )
    
    async def notify_system_info(self, message: str) -> bool:
        """
        Send system info notification.
        
        Args:
            message: Info message
            
        Returns:
            True if sent successfully
        """
        if not self.settings.system_info:
            return False
        
        formatted = self.formatter.format_system_alert("info", message)
        
        return await self._send_notification(
            NotificationType.SYSTEM_INFO,
            formatted,
            silent=self.settings.silent_system_info,
            metadata={"message": message}
        )
    
    async def send_daily_summary(self) -> bool:
        """
        Send daily trading summary.
        
        Returns:
            True if sent successfully
        """
        if not self.settings.daily_summary:
            return False
        
        stats = self._daily_stats
        
        best_trade = None
        if stats.best_trade_symbol:
            best_trade = f"{stats.best_trade_symbol} +{stats.best_trade_pnl:.1f}%"
        
        worst_trade = None
        if stats.worst_trade_symbol:
            worst_trade = f"{stats.worst_trade_symbol} {stats.worst_trade_pnl:.1f}%"
        
        formatted = self.formatter.format_daily_summary(
            date=stats.date.strftime("%d.%m.%Y"),
            total_trades=stats.total_trades,
            winning_trades=stats.winning_trades,
            total_pnl_percent=stats.total_pnl_percent,
            total_pnl_usd=stats.total_pnl_usd,
            best_trade=best_trade,
            worst_trade=worst_trade,
        )
        
        return await self._send_notification(
            NotificationType.DAILY_SUMMARY,
            formatted,
            metadata={
                "date": stats.date.isoformat(),
                "total_trades": stats.total_trades,
                "pnl_percent": stats.total_pnl_percent,
            }
        )
    
    def record_trade_result(
        self,
        symbol: str,
        pnl_percent: float,
        pnl_usd: float,
        is_win: bool
    ) -> None:
        """
        Record a trade result for daily statistics.
        
        Args:
            symbol: Trading pair
            pnl_percent: PnL in percent
            pnl_usd: PnL in USD
            is_win: Whether trade was profitable
        """
        self._daily_stats.total_trades += 1
        self._daily_stats.total_pnl_percent += pnl_percent
        self._daily_stats.total_pnl_usd += pnl_usd
        
        if is_win:
            self._daily_stats.winning_trades += 1
            if pnl_percent > self._daily_stats.best_trade_pnl:
                self._daily_stats.best_trade_pnl = pnl_percent
                self._daily_stats.best_trade_symbol = symbol
        else:
            self._daily_stats.losing_trades += 1
            if pnl_percent < self._daily_stats.worst_trade_pnl:
                self._daily_stats.worst_trade_pnl = pnl_percent
                self._daily_stats.worst_trade_symbol = symbol
    
    def reset_daily_stats(self) -> None:
        """Reset daily statistics for new day."""
        self._daily_stats = DailyStats(date=date.today())
    
    async def _send_notification(
        self,
        notification_type: NotificationType,
        text: str,
        silent: bool = False,
        priority: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send notification through bot.
        
        Args:
            notification_type: Type of notification
            text: Notification text
            silent: Send without sound
            priority: Send immediately
            metadata: Additional data for logging
            
        Returns:
            True if sent successfully
        """
        # Record in history
        record = {
            "type": notification_type.value,
            "timestamp": datetime.now().isoformat(),
            "text_preview": text[:100],
            "metadata": metadata or {},
        }
        self._notification_history.append(record)
        
        # Trim history if needed
        if len(self._notification_history) > self._max_history_size:
            self._notification_history = self._notification_history[-self._max_history_size:]
        
        # Send through bot
        return await self.bot.send_message(
            text=text,
            disable_notification=silent,
            priority=priority
        )
    
    async def test_notification(self) -> bool:
        """
        Send test notification.
        
        Returns:
            True if sent successfully
        """
        return await self.bot.send_message(
            text="🔧 VELAS Test notification\nБот работает корректно!",
            priority=True
        )
    
    def get_notification_history(
        self,
        limit: int = 100,
        notification_type: Optional[NotificationType] = None
    ) -> List[Dict[str, Any]]:
        """
        Get notification history.
        
        Args:
            limit: Maximum records to return
            notification_type: Filter by type
            
        Returns:
            List of notification records
        """
        history = self._notification_history
        
        if notification_type:
            history = [
                r for r in history
                if r["type"] == notification_type.value
            ]
        
        return history[-limit:]


async def create_notification_manager(
    bot_token: str,
    chat_id: str,
    enabled: bool = True,
    leverage: int = 10,
    settings: Optional[NotificationSettings] = None,
    use_mock: bool = False
) -> NotificationManager:
    """
    Factory function to create and start notification manager.
    
    Args:
        bot_token: Telegram bot token
        chat_id: Target chat ID
        enabled: Enable/disable bot
        leverage: Default leverage
        settings: Notification preferences
        use_mock: Use mock bot
        
    Returns:
        Started NotificationManager instance
    """
    config = BotConfig(
        bot_token=bot_token,
        chat_id=chat_id,
        enabled=enabled,
    )
    
    manager = NotificationManager(
        config=config,
        settings=settings,
        use_mock=use_mock,
        leverage=leverage,
    )
    
    await manager.start()
    
    return manager
