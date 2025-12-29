"""
VELAS - Telegram уведомления.

Отправляет сигналы в формате Cornix и системные уведомления.
"""

import asyncio
from typing import Optional
from datetime import datetime
import logging

from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Отправка уведомлений в Telegram."""
    
    def __init__(self, token: str, chat_id: str):
        self.bot = Bot(token=token)
        self.chat_id = chat_id
        self.enabled = True
    
    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Отправка простого сообщения."""
        if not self.enabled:
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode=parse_mode,
            )
            return True
        except TelegramError as e:
            logger.error(f"Telegram error: {e}")
            return False
    
    async def send_signal(self, signal: "SignalModel") -> bool:
        """Отправка торгового сигнала в формате Cornix."""
        
        # Определяем направление
        direction = "🟢 LONG" if signal.side == "LONG" else "🔴 SHORT"
        
        # Символ без USDT для Cornix
        symbol_clean = signal.symbol.replace("USDT", "")
        
        # Формируем сообщение в формате Cornix
        message = f"""
<b>{direction}</b>

#️⃣ <b>{signal.symbol}</b>
📊 Spot/Futures

<b>Entry:</b> <code>{signal.entry_price}</code>

<b>Take Profits:</b>
1️⃣ <code>{signal.tp1_price}</code>
2️⃣ <code>{signal.tp2_price}</code>
3️⃣ <code>{signal.tp3_price}</code>
4️⃣ <code>{signal.tp4_price}</code>
5️⃣ <code>{signal.tp5_price}</code>
6️⃣ <code>{signal.tp6_price}</code>

<b>Stop Loss:</b> <code>{signal.sl_price}</code>

<i>⏱ Таймфрейм: {signal.timeframe}</i>
<i>📈 Режим: {signal.volatility_regime}</i>
<i>💡 Уверенность: {signal.confidence:.0%}</i>

<code>#{symbol_clean}USDT</code> <code>#VELAS</code>
"""
        
        return await self.send_message(message.strip())
    
    async def send_tp_hit(self, position: "PositionModel", tp_level: str, price: float) -> bool:
        """Уведомление о достижении TP."""
        
        direction = "🟢" if position.side == "LONG" else "🔴"
        pnl = position.unrealized_pnl_percent
        pnl_emoji = "📈" if pnl >= 0 else "📉"
        
        message = f"""
🎯 <b>{tp_level} HIT</b>

{direction} <b>{position.symbol}</b>

<b>Цена:</b> <code>{price}</code>
<b>P&L:</b> {pnl_emoji} <code>{pnl:+.2f}%</code>
<b>Остаток:</b> <code>{position.position_remaining:.0f}%</code>

<i>⏱ {datetime.utcnow().strftime("%H:%M:%S UTC")}</i>
"""
        
        return await self.send_message(message.strip())
    
    async def send_position_closed(self, position: "PositionModel") -> bool:
        """Уведомление о закрытии позиции."""
        
        direction = "🟢" if position.side == "LONG" else "🔴"
        pnl = position.realized_pnl
        
        if pnl >= 0:
            status = "✅ PROFIT"
            pnl_emoji = "📈"
        else:
            status = "❌ LOSS"
            pnl_emoji = "📉"
        
        # Расчёт длительности
        if position.entry_time and position.close_time:
            duration = position.close_time - position.entry_time
            hours = duration.total_seconds() / 3600
            if hours < 1:
                duration_str = f"{duration.total_seconds() / 60:.0f}m"
            elif hours < 24:
                duration_str = f"{hours:.1f}h"
            else:
                duration_str = f"{hours / 24:.1f}d"
        else:
            duration_str = "N/A"
        
        message = f"""
📊 <b>ПОЗИЦИЯ ЗАКРЫТА</b>

{status}

{direction} <b>{position.symbol}</b>

<b>Вход:</b> <code>{position.entry_price}</code>
<b>Выход:</b> <code>{position.close_price}</code>
<b>P&L:</b> {pnl_emoji} <code>{pnl:+.2f}%</code>

<b>Причина:</b> {position.close_reason}
<b>Длительность:</b> {duration_str}

<i>⏱ {datetime.utcnow().strftime("%H:%M:%S UTC")}</i>
"""
        
        return await self.send_message(message.strip())
    
    async def send_alert(self, alert_type: str, message: str) -> bool:
        """Отправка системного алерта."""
        
        type_emoji = {
            "warning": "⚠️",
            "error": "🚨",
            "info": "ℹ️",
            "success": "✅",
        }
        
        emoji = type_emoji.get(alert_type, "📢")
        
        alert_message = f"""
{emoji} <b>СИСТЕМНЫЙ АЛЕРТ</b>

{message}

<i>⏱ {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</i>
"""
        
        return await self.send_message(alert_message.strip())


# Mock версия для тестирования
class MockTelegramNotifier(TelegramNotifier):
    """Mock Telegram для тестирования без реальной отправки."""
    
    def __init__(self, token: str = "", chat_id: str = ""):
        self.chat_id = chat_id
        self.enabled = True
        self.sent_messages = []
    
    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Имитация отправки."""
        self.sent_messages.append({
            "text": text,
            "parse_mode": parse_mode,
            "timestamp": datetime.utcnow().isoformat(),
        })
        logger.info(f"[MOCK TG] Message sent: {text[:100]}...")
        return True
