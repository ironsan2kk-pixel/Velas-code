"""
DEPRECATED - Use backend.tg_notifier instead.
This module is kept for backward compatibility.
"""

# Redirect to new location
from backend.tg_notifier.bot import TelegramNotifier, MockTelegramNotifier

__all__ = ["TelegramNotifier", "MockTelegramNotifier"]
