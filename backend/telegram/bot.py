"""
DEPRECATED - Use backend.tg_notifier.bot instead.
This module redirects imports to the new location.
"""

from backend.tg_notifier.bot import TelegramNotifier, MockTelegramNotifier

__all__ = ["TelegramNotifier", "MockTelegramNotifier"]
