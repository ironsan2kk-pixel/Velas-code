"""
VELAS Telegram Bot Module.

Provides Telegram bot functionality for trading notifications.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

# Импорт telegram с проверкой
try:
    from telegram import Bot as TgBot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    TgBot = None
    TelegramError = Exception

logger = logging.getLogger(__name__)


class BotState(str, Enum):
    """Состояние бота."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class BotConfig:
    """Конфигурация Telegram бота."""
    bot_token: str
    chat_id: str
    enabled: bool = True
    parse_mode: str = "HTML"
    disable_web_page_preview: bool = True
    rate_limit: float = 0.5  # секунды между сообщениями
    max_retries: int = 3
    retry_delay: float = 1.0


class TelegramBot:
    """Telegram бот для отправки уведомлений."""

    def __init__(self, config: BotConfig):
        self.config = config
        self.state = BotState.STOPPED
        self._bot: Optional[TgBot] = None
        self._message_queue: List[Dict[str, Any]] = []
        self._stats = {
            "messages_sent": 0,
            "messages_failed": 0,
            "last_message_time": None,
        }
        self._last_send_time: Optional[float] = None

    @property
    def is_running(self) -> bool:
        """Проверка работы бота."""
        return self.state == BotState.RUNNING

    @property
    def stats(self) -> Dict[str, Any]:
        """Статистика бота."""
        return self._stats.copy()

    async def start(self) -> bool:
        """Запуск бота."""
        if not self.config.enabled:
            logger.info("Telegram bot disabled in config")
            return False

        if not TELEGRAM_AVAILABLE:
            logger.warning("python-telegram-bot not installed")
            self.state = BotState.ERROR
            return False

        self.state = BotState.STARTING

        try:
            self._bot = TgBot(token=self.config.bot_token)
            self.state = BotState.RUNNING
            logger.info("Telegram bot started")
            return True
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            self.state = BotState.ERROR
            return False

    async def stop(self) -> None:
        """Остановка бота."""
        self.state = BotState.STOPPING
        self._bot = None
        self.state = BotState.STOPPED
        logger.info("Telegram bot stopped")

    async def send_message(
        self,
        text: str,
        disable_notification: bool = False,
        priority: bool = False,
        **kwargs
    ) -> bool:
        """Отправка сообщения."""
        if not self.is_running or not self._bot:
            logger.warning("Bot is not running")
            return False

        # Rate limiting
        if self._last_send_time:
            elapsed = asyncio.get_event_loop().time() - self._last_send_time
            if elapsed < self.config.rate_limit and not priority:
                await asyncio.sleep(self.config.rate_limit - elapsed)

        for attempt in range(self.config.max_retries):
            try:
                await self._bot.send_message(
                    chat_id=self.config.chat_id,
                    text=text,
                    parse_mode=self.config.parse_mode,
                    disable_notification=disable_notification,
                    disable_web_page_preview=self.config.disable_web_page_preview,
                )
                self._stats["messages_sent"] += 1
                self._stats["last_message_time"] = datetime.now().isoformat()
                self._last_send_time = asyncio.get_event_loop().time()
                return True
            except TelegramError as e:
                logger.error(f"Telegram error (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
            except Exception as e:
                logger.error(f"Send error: {e}")
                break

        self._stats["messages_failed"] += 1
        return False


class TelegramBotMock(TelegramBot):
    """Mock Telegram бот для тестирования."""

    def __init__(self, config: BotConfig):
        super().__init__(config)
        self.sent_messages: List[Dict[str, Any]] = []

    async def start(self) -> bool:
        """Имитация запуска."""
        self.state = BotState.RUNNING
        logger.info("Mock Telegram bot started")
        return True

    async def send_message(
        self,
        text: str,
        disable_notification: bool = False,
        priority: bool = False,
        **kwargs
    ) -> bool:
        """Имитация отправки."""
        if not self.is_running:
            return False

        self.sent_messages.append({
            "text": text,
            "disable_notification": disable_notification,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
        })
        self._stats["messages_sent"] += 1
        self._stats["last_message_time"] = datetime.now().isoformat()
        logger.debug(f"[MOCK] Message sent: {text[:50]}...")
        return True


# Обратная совместимость с tg_notifier
from backend.tg_notifier.bot import TelegramNotifier, MockTelegramNotifier

__all__ = [
    "TelegramBot",
    "TelegramBotMock",
    "BotConfig",
    "BotState",
    "TelegramNotifier",
    "MockTelegramNotifier",
]
