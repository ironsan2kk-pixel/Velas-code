"""
VELAS Cornix Signal Formatter

Formats trading signals for Cornix bot compatibility.
Official Cornix format: https://help.cornix.io/en/articles/11659507-signal-posting-format
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
from datetime import datetime


class SignalSide(str, Enum):
    """Trading signal direction."""
    LONG = "Long"
    SHORT = "Short"


@dataclass
class TradingSignal:
    """Trading signal data structure."""
    symbol: str                    # e.g., "BTCUSDT"
    side: SignalSide              # LONG or SHORT
    entry_price: float            # Entry price
    stop_loss: float              # Stop loss price
    take_profits: List[float]     # TP1-TP6 prices
    timeframe: str                # e.g., "1h"
    preset_id: str                # e.g., "BTCUSDT_1h_normal"
    leverage: int = 10            # Default 10x
    signal_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate signal data."""
        if not self.take_profits:
            raise ValueError("At least one take profit level required")
        if len(self.take_profits) > 10:
            raise ValueError("Maximum 10 take profit levels allowed")
        if self.leverage < 1 or self.leverage > 125:
            raise ValueError("Leverage must be between 1 and 125")
        
        # Validate price relationships
        if self.side == SignalSide.LONG:
            if self.stop_loss >= self.entry_price:
                raise ValueError("Stop loss must be below entry for LONG")
            if any(tp <= self.entry_price for tp in self.take_profits):
                raise ValueError("All take profits must be above entry for LONG")
        else:  # SHORT
            if self.stop_loss <= self.entry_price:
                raise ValueError("Stop loss must be above entry for SHORT")
            if any(tp >= self.entry_price for tp in self.take_profits):
                raise ValueError("All take profits must be below entry for SHORT")


@dataclass
class TPHitEvent:
    """Take profit hit event."""
    symbol: str
    side: SignalSide
    tp_level: int                 # 1-6
    tp_price: float
    entry_price: float
    pnl_percent: float
    position_closed_percent: float  # e.g., 20.0
    remaining_percent: float        # e.g., 80.0
    new_sl_price: Optional[float] = None
    sl_moved_to: Optional[str] = None  # "BE" or "TP1", "TP2", etc.


@dataclass
class SLHitEvent:
    """Stop loss hit event."""
    symbol: str
    side: SignalSide
    sl_price: float
    entry_price: float
    pnl_percent: float
    pnl_usd: float
    was_at_breakeven: bool = False


class CornixFormatter:
    """
    Formats trading signals and notifications for Cornix bot.
    
    Cornix requires specific formatting for automatic signal parsing.
    All targets must be prices (not percentages).
    """
    
    # TP distribution percentages
    TP_DISTRIBUTION = [20, 20, 15, 15, 15, 15]
    
    def __init__(self, leverage: int = 10):
        """
        Initialize formatter.
        
        Args:
            leverage: Default leverage (1-125)
        """
        self.default_leverage = leverage
    
    def format_symbol(self, symbol: str) -> str:
        """
        Format symbol for Cornix (add slash).
        
        Args:
            symbol: Trading pair, e.g., "BTCUSDT"
            
        Returns:
            Formatted symbol, e.g., "BTC/USDT"
        """
        # Handle common quote currencies
        for quote in ["USDT", "BUSD", "USDC", "BTC", "ETH"]:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                return f"{base}/{quote}"
        return symbol
    
    def format_price(self, price: float, symbol: str = "") -> str:
        """
        Format price with appropriate precision.
        
        Args:
            price: Price value
            symbol: Optional symbol for context
            
        Returns:
            Formatted price string
        """
        if price >= 10000:
            return f"{price:.1f}"
        elif price >= 100:
            return f"{price:.2f}"
        elif price >= 1:
            return f"{price:.4f}"
        else:
            return f"{price:.6f}"
    
    def format_new_signal(self, signal: TradingSignal) -> str:
        """
        Format new trading signal for Cornix.
        
        Official Cornix format with:
        - Symbol with hashtag
        - Signal type (Regular Long/Short)
        - Leverage (Cross Xx)
        - Single entry price
        - Take profit targets (up to 10)
        - Stop loss target
        
        Args:
            signal: Trading signal data
            
        Returns:
            Formatted Cornix-compatible message
        """
        formatted_symbol = self.format_symbol(signal.symbol)
        leverage = signal.leverage or self.default_leverage
        
        # Build message
        lines = [
            f"⚡⚡ #{formatted_symbol} ⚡⚡",
            "",
            f"Signal Type: Regular ({signal.side.value})",
            "",
            f"Leverage: Cross ({leverage}X)",
            "",
            "Entry Zone:",
            self.format_price(signal.entry_price, signal.symbol),
            "",
            "Take-Profit Targets:",
        ]
        
        # Add take profit levels
        for i, tp in enumerate(signal.take_profits, 1):
            lines.append(f"{i}) {self.format_price(tp, signal.symbol)}")
        
        lines.extend([
            "",
            "Stop Targets:",
            f"1) {self.format_price(signal.stop_loss, signal.symbol)}",
        ])
        
        return "\n".join(lines)
    
    def format_tp_hit(self, event: TPHitEvent) -> str:
        """
        Format take profit hit notification.
        
        Args:
            event: TP hit event data
            
        Returns:
            Formatted notification message
        """
        formatted_symbol = self.format_symbol(event.symbol)
        pnl_sign = "+" if event.pnl_percent >= 0 else ""
        
        lines = [
            f"✅ TP{event.tp_level} HIT — {formatted_symbol} {event.side.value.upper()}",
            f"Закрыто {event.position_closed_percent:.0f}% по {self.format_price(event.tp_price)} ({pnl_sign}{event.pnl_percent:.1f}%)",
        ]
        
        # Add SL movement info
        if event.new_sl_price and event.sl_moved_to:
            if event.sl_moved_to == "BE":
                lines.append(f"SL перемещён: → {self.format_price(event.new_sl_price)} (БУ)")
            else:
                lines.append(f"SL перемещён: → {self.format_price(event.new_sl_price)} ({event.sl_moved_to})")
        
        if event.remaining_percent > 0:
            lines.append(f"Осталось: {event.remaining_percent:.0f}% позиции")
        else:
            lines.append("Позиция полностью закрыта")
        
        return "\n".join(lines)
    
    def format_sl_hit(self, event: SLHitEvent) -> str:
        """
        Format stop loss hit notification.
        
        Args:
            event: SL hit event data
            
        Returns:
            Formatted notification message
        """
        formatted_symbol = self.format_symbol(event.symbol)
        pnl_sign = "+" if event.pnl_percent >= 0 else ""
        usd_sign = "+" if event.pnl_usd >= 0 else ""
        
        sl_type = " (БУ)" if event.was_at_breakeven else ""
        
        lines = [
            f"⛔ SL HIT{sl_type} — {formatted_symbol} {event.side.value.upper()}",
            f"Закрыто 100% по {self.format_price(event.sl_price)} ({pnl_sign}{event.pnl_percent:.1f}%)",
            f"Результат: {usd_sign}${abs(event.pnl_usd):.2f}",
        ]
        
        return "\n".join(lines)
    
    def format_position_update(
        self,
        symbol: str,
        side: SignalSide,
        update_type: str,
        details: str
    ) -> str:
        """
        Format position update notification.
        
        Args:
            symbol: Trading pair
            side: Signal direction
            update_type: Type of update
            details: Update details
            
        Returns:
            Formatted notification message
        """
        formatted_symbol = self.format_symbol(symbol)
        
        return f"📊 {formatted_symbol} {side.value.upper()}\n{update_type}: {details}"
    
    def format_signal_cancelled(self, symbol: str, side: SignalSide, reason: str) -> str:
        """
        Format signal cancellation notification.
        
        Args:
            symbol: Trading pair
            side: Signal direction
            reason: Cancellation reason
            
        Returns:
            Formatted notification message
        """
        formatted_symbol = self.format_symbol(symbol)
        
        return f"❌ ОТМЕНЁН — {formatted_symbol} {side.value.upper()}\nПричина: {reason}"
    
    def format_system_alert(self, alert_type: str, message: str) -> str:
        """
        Format system alert notification.
        
        Args:
            alert_type: Type of alert (error, warning, info)
            message: Alert message
            
        Returns:
            Formatted notification message
        """
        icons = {
            "error": "🔴",
            "warning": "⚠️",
            "info": "ℹ️",
            "success": "✅",
        }
        icon = icons.get(alert_type.lower(), "📢")
        
        return f"{icon} СИСТЕМА\n{message}"
    
    def format_daily_summary(
        self,
        date: str,
        total_trades: int,
        winning_trades: int,
        total_pnl_percent: float,
        total_pnl_usd: float,
        best_trade: Optional[str] = None,
        worst_trade: Optional[str] = None
    ) -> str:
        """
        Format daily trading summary.
        
        Args:
            date: Summary date
            total_trades: Total closed trades
            winning_trades: Number of winning trades
            total_pnl_percent: Total PnL in percent
            total_pnl_usd: Total PnL in USD
            best_trade: Best trade description
            worst_trade: Worst trade description
            
        Returns:
            Formatted summary message
        """
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        pnl_sign = "+" if total_pnl_percent >= 0 else ""
        usd_sign = "+" if total_pnl_usd >= 0 else ""
        
        lines = [
            f"📊 ИТОГИ ДНЯ — {date}",
            "",
            f"Сделок: {total_trades}",
            f"Win Rate: {win_rate:.1f}%",
            f"PnL: {pnl_sign}{total_pnl_percent:.2f}% ({usd_sign}${abs(total_pnl_usd):.2f})",
        ]
        
        if best_trade:
            lines.append(f"Лучшая: {best_trade}")
        if worst_trade:
            lines.append(f"Худшая: {worst_trade}")
        
        return "\n".join(lines)
    
    def calculate_tp_levels(
        self,
        entry_price: float,
        side: SignalSide,
        tp_percentages: List[float]
    ) -> List[float]:
        """
        Calculate TP price levels from percentages.
        
        Args:
            entry_price: Entry price
            side: Signal direction
            tp_percentages: TP levels as percentages (e.g., [1.0, 2.0, 3.0])
            
        Returns:
            List of TP price levels
        """
        tp_prices = []
        
        for pct in tp_percentages:
            if side == SignalSide.LONG:
                tp_price = entry_price * (1 + pct / 100)
            else:  # SHORT
                tp_price = entry_price * (1 - pct / 100)
            tp_prices.append(tp_price)
        
        return tp_prices
    
    def calculate_sl_level(
        self,
        entry_price: float,
        side: SignalSide,
        sl_percentage: float
    ) -> float:
        """
        Calculate SL price level from percentage.
        
        Args:
            entry_price: Entry price
            side: Signal direction
            sl_percentage: SL distance as percentage
            
        Returns:
            SL price level
        """
        if side == SignalSide.LONG:
            return entry_price * (1 - sl_percentage / 100)
        else:  # SHORT
            return entry_price * (1 + sl_percentage / 100)
