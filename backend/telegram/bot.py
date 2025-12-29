"""
VELAS Telegram Bot

Async Telegram bot for sending trading signals and notifications.
Uses python-telegram-bot library (v20+).
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

try:
    from telegram import Bot, Update
    from telegram.ext import (
        Application,
        CommandHandler,
        ContextTypes,
        MessageHandler,
        filters,
    )
    from telegram.error import TelegramError, NetworkError, TimedOut
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    Bot = None
    Update = None
    Application = None
    TelegramError = Exception


logger = logging.getLogger(__name__)


class BotState(str, Enum):
    """Bot operational state."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class BotConfig:
    """Telegram bot configuration."""
    bot_token: str
    chat_id: str
    enabled: bool = True
    retry_attempts: int = 3
    retry_delay: float = 1.0
    parse_mode: str = "HTML"
    disable_notification: bool = False
    
    def __post_init__(self):
        """Validate configuration."""
        if self.enabled:
            if not self.bot_token or self.bot_token == "YOUR_TELEGRAM_BOT_TOKEN":
                raise ValueError("Valid bot_token required")
            if not self.chat_id:
                raise ValueError("chat_id required")


class TelegramBot:
    """
    Async Telegram bot for VELAS trading system.
    
    Features:
    - Async message sending with retry logic
    - Rate limiting protection
    - Message queue for batch sending
    - Error handling and logging
    - Optional command handlers
    
    Usage:
        config = BotConfig(
            bot_token="123456:ABC-DEF...",
            chat_id="-100123456789"
        )
        bot = TelegramBot(config)
        await bot.start()
        await bot.send_message("Hello!")
        await bot.stop()
    """
    
    # Telegram rate limits
    MAX_MESSAGES_PER_SECOND = 30
    MAX_MESSAGES_PER_MINUTE_PER_CHAT = 20
    
    def __init__(self, config: BotConfig):
        """
        Initialize Telegram bot.
        
        Args:
            config: Bot configuration
        """
        if not TELEGRAM_AVAILABLE:
            raise ImportError(
                "python-telegram-bot not installed. "
                "Install with: pip install python-telegram-bot>=20.7"
            )
        
        self.config = config
        self.state = BotState.STOPPED
        self._bot: Optional[Bot] = None
        self._app: Optional[Application] = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._queue_processor_task: Optional[asyncio.Task] = None
        self._last_message_time: float = 0
        self._message_count_minute: int = 0
        self._minute_start: float = 0
        
        # Statistics
        self._stats = {
            "messages_sent": 0,
            "messages_failed": 0,
            "last_error": None,
            "last_success": None,
        }
    
    @property
    def is_running(self) -> bool:
        """Check if bot is running."""
        return self.state == BotState.RUNNING
    
    @property
    def is_enabled(self) -> bool:
        """Check if bot is enabled."""
        return self.config.enabled
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get bot statistics."""
        return self._stats.copy()
    
    async def start(self) -> bool:
        """
        Start the Telegram bot.
        
        Returns:
            True if started successfully
        """
        if not self.config.enabled:
            logger.info("Telegram bot is disabled in configuration")
            return False
        
        if self.state == BotState.RUNNING:
            logger.warning("Bot is already running")
            return True
        
        try:
            self.state = BotState.STARTING
            logger.info("Starting Telegram bot...")
            
            # Create bot instance
            self._bot = Bot(token=self.config.bot_token)
            
            # Verify bot token
            bot_info = await self._bot.get_me()
            logger.info(f"Bot authenticated: @{bot_info.username}")
            
            # Start message queue processor
            self._queue_processor_task = asyncio.create_task(
                self._process_message_queue()
            )
            
            self.state = BotState.RUNNING
            logger.info("Telegram bot started successfully")
            return True
            
        except TelegramError as e:
            self.state = BotState.ERROR
            self._stats["last_error"] = str(e)
            logger.error(f"Failed to start Telegram bot: {e}")
            return False
        except Exception as e:
            self.state = BotState.ERROR
            self._stats["last_error"] = str(e)
            logger.exception(f"Unexpected error starting bot: {e}")
            return False
    
    async def stop(self) -> None:
        """Stop the Telegram bot."""
        if self.state in (BotState.STOPPED, BotState.STOPPING):
            return
        
        try:
            self.state = BotState.STOPPING
            logger.info("Stopping Telegram bot...")
            
            # Stop queue processor
            if self._queue_processor_task:
                self._queue_processor_task.cancel()
                try:
                    await self._queue_processor_task
                except asyncio.CancelledError:
                    pass
                self._queue_processor_task = None
            
            # Process remaining messages in queue
            while not self._message_queue.empty():
                try:
                    message = self._message_queue.get_nowait()
                    await self._send_message_direct(message)
                except asyncio.QueueEmpty:
                    break
                except Exception as e:
                    logger.error(f"Error sending queued message: {e}")
            
            self._bot = None
            self.state = BotState.STOPPED
            logger.info("Telegram bot stopped")
            
        except Exception as e:
            logger.exception(f"Error stopping bot: {e}")
            self.state = BotState.ERROR
    
    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        priority: bool = False
    ) -> bool:
        """
        Send a message to Telegram.
        
        Args:
            text: Message text
            chat_id: Target chat ID (uses default if not specified)
            parse_mode: Parse mode (HTML, Markdown, etc.)
            disable_notification: Send silently
            priority: If True, send immediately without queue
            
        Returns:
            True if message was sent/queued successfully
        """
        if not self.config.enabled:
            logger.debug("Bot disabled, message not sent")
            return False
        
        if not self.is_running:
            logger.warning("Bot not running, message not sent")
            return False
        
        message_data = {
            "text": text,
            "chat_id": chat_id or self.config.chat_id,
            "parse_mode": parse_mode or self.config.parse_mode,
            "disable_notification": (
                disable_notification 
                if disable_notification is not None 
                else self.config.disable_notification
            ),
        }
        
        if priority:
            return await self._send_message_direct(message_data)
        else:
            await self._message_queue.put(message_data)
            return True
    
    async def send_signal(self, formatted_signal: str) -> bool:
        """
        Send a trading signal message (priority).
        
        Args:
            formatted_signal: Pre-formatted Cornix signal
            
        Returns:
            True if sent successfully
        """
        return await self.send_message(
            text=formatted_signal,
            parse_mode=None,  # Plain text for Cornix
            priority=True
        )
    
    async def send_notification(
        self,
        text: str,
        silent: bool = False
    ) -> bool:
        """
        Send a notification message.
        
        Args:
            text: Notification text
            silent: Send without notification sound
            
        Returns:
            True if sent successfully
        """
        return await self.send_message(
            text=text,
            parse_mode=None,
            disable_notification=silent
        )
    
    async def _send_message_direct(self, message_data: Dict[str, Any]) -> bool:
        """
        Send message directly with retry logic.
        
        Args:
            message_data: Message parameters
            
        Returns:
            True if sent successfully
        """
        if not self._bot:
            logger.error("Bot not initialized")
            return False
        
        # Rate limiting
        await self._wait_for_rate_limit()
        
        for attempt in range(self.config.retry_attempts):
            try:
                await self._bot.send_message(
                    chat_id=message_data["chat_id"],
                    text=message_data["text"],
                    parse_mode=message_data.get("parse_mode"),
                    disable_notification=message_data.get("disable_notification", False),
                )
                
                self._stats["messages_sent"] += 1
                self._stats["last_success"] = datetime.now().isoformat()
                self._update_rate_limit_counters()
                
                logger.debug(f"Message sent to {message_data['chat_id']}")
                return True
                
            except (NetworkError, TimedOut) as e:
                logger.warning(
                    f"Network error (attempt {attempt + 1}/{self.config.retry_attempts}): {e}"
                )
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                    
            except TelegramError as e:
                self._stats["messages_failed"] += 1
                self._stats["last_error"] = str(e)
                logger.error(f"Telegram error: {e}")
                return False
                
            except Exception as e:
                self._stats["messages_failed"] += 1
                self._stats["last_error"] = str(e)
                logger.exception(f"Unexpected error sending message: {e}")
                return False
        
        self._stats["messages_failed"] += 1
        logger.error("Failed to send message after all retry attempts")
        return False
    
    async def _wait_for_rate_limit(self) -> None:
        """Wait if necessary to respect rate limits."""
        current_time = asyncio.get_event_loop().time()
        
        # Reset minute counter if minute has passed
        if current_time - self._minute_start >= 60:
            self._message_count_minute = 0
            self._minute_start = current_time
        
        # Check per-minute limit
        if self._message_count_minute >= self.MAX_MESSAGES_PER_MINUTE_PER_CHAT:
            wait_time = 60 - (current_time - self._minute_start)
            if wait_time > 0:
                logger.debug(f"Rate limit: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
                self._message_count_minute = 0
                self._minute_start = asyncio.get_event_loop().time()
        
        # Check per-second limit
        time_since_last = current_time - self._last_message_time
        if time_since_last < (1.0 / self.MAX_MESSAGES_PER_SECOND):
            await asyncio.sleep((1.0 / self.MAX_MESSAGES_PER_SECOND) - time_since_last)
    
    def _update_rate_limit_counters(self) -> None:
        """Update rate limit tracking counters."""
        self._last_message_time = asyncio.get_event_loop().time()
        self._message_count_minute += 1
    
    async def _process_message_queue(self) -> None:
        """Process queued messages in background."""
        logger.debug("Message queue processor started")
        
        while True:
            try:
                message_data = await self._message_queue.get()
                await self._send_message_direct(message_data)
                self._message_queue.task_done()
                
            except asyncio.CancelledError:
                logger.debug("Message queue processor cancelled")
                break
                
            except Exception as e:
                logger.exception(f"Error processing message queue: {e}")
                await asyncio.sleep(1)
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test bot connection and permissions.
        
        Returns:
            Test results dictionary
        """
        results = {
            "connected": False,
            "bot_username": None,
            "can_send": False,
            "chat_info": None,
            "error": None,
        }
        
        if not self.config.enabled:
            results["error"] = "Bot is disabled"
            return results
        
        try:
            # Test bot authentication
            bot = Bot(token=self.config.bot_token)
            bot_info = await bot.get_me()
            results["connected"] = True
            results["bot_username"] = bot_info.username
            
            # Test chat access
            try:
                chat = await bot.get_chat(self.config.chat_id)
                results["chat_info"] = {
                    "id": chat.id,
                    "type": chat.type,
                    "title": getattr(chat, "title", None),
                }
                
                # Test send permission by sending and deleting
                test_msg = await bot.send_message(
                    chat_id=self.config.chat_id,
                    text="🔧 VELAS Bot connection test",
                )
                await bot.delete_message(
                    chat_id=self.config.chat_id,
                    message_id=test_msg.message_id,
                )
                results["can_send"] = True
                
            except TelegramError as e:
                results["error"] = f"Chat access error: {e}"
                
        except TelegramError as e:
            results["error"] = f"Bot authentication error: {e}"
        except Exception as e:
            results["error"] = f"Unexpected error: {e}"
        
        return results


class TelegramBotMock:
    """
    Mock Telegram bot for testing without actual API calls.
    
    Stores sent messages for verification in tests.
    """
    
    def __init__(self, config: Optional[BotConfig] = None):
        """Initialize mock bot."""
        self.config = config
        self.state = BotState.STOPPED
        self.sent_messages: list = []
        self._stats = {
            "messages_sent": 0,
            "messages_failed": 0,
            "last_error": None,
            "last_success": None,
        }
    
    @property
    def is_running(self) -> bool:
        return self.state == BotState.RUNNING
    
    @property
    def is_enabled(self) -> bool:
        return self.config.enabled if self.config else True
    
    @property
    def stats(self) -> Dict[str, Any]:
        return self._stats.copy()
    
    async def start(self) -> bool:
        self.state = BotState.RUNNING
        return True
    
    async def stop(self) -> None:
        self.state = BotState.STOPPED
    
    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: Optional[str] = None,
        disable_notification: Optional[bool] = None,
        priority: bool = False
    ) -> bool:
        message = {
            "text": text,
            "chat_id": chat_id or (self.config.chat_id if self.config else "test"),
            "parse_mode": parse_mode,
            "disable_notification": disable_notification,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
        }
        self.sent_messages.append(message)
        self._stats["messages_sent"] += 1
        self._stats["last_success"] = message["timestamp"]
        return True
    
    async def send_signal(self, formatted_signal: str) -> bool:
        return await self.send_message(formatted_signal, priority=True)
    
    async def send_notification(self, text: str, silent: bool = False) -> bool:
        return await self.send_message(text, disable_notification=silent)
    
    def clear_messages(self) -> None:
        """Clear sent messages list."""
        self.sent_messages.clear()
    
    def get_last_message(self) -> Optional[Dict[str, Any]]:
        """Get the last sent message."""
        return self.sent_messages[-1] if self.sent_messages else None
    
    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": True,
            "bot_username": "mock_bot",
            "can_send": True,
            "chat_info": {"id": "test", "type": "channel"},
            "error": None,
        }
