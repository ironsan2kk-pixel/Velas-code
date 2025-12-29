"""
VELAS Telegram Module Tests

Comprehensive tests for Telegram bot, Cornix formatter, and notification manager.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.telegram.cornix import (
    CornixFormatter,
    TradingSignal,
    SignalSide,
    TPHitEvent,
    SLHitEvent,
)
from backend.telegram.bot import (
    TelegramBot,
    TelegramBotMock,
    BotConfig,
    BotState,
)
from backend.telegram.notifications import (
    NotificationManager,
    NotificationSettings,
    NotificationType,
    DailyStats,
    create_notification_manager,
)

# Configure pytest-asyncio
pytestmark = pytest.mark.asyncio(loop_scope="function")


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def formatter():
    """Create CornixFormatter instance."""
    return CornixFormatter(leverage=10)


@pytest.fixture
def sample_long_signal():
    """Create sample LONG signal."""
    return TradingSignal(
        symbol="BTCUSDT",
        side=SignalSide.LONG,
        entry_price=42500.0,
        stop_loss=41225.0,
        take_profits=[42925.0, 43350.0, 43988.0, 44625.0, 45900.0, 47600.0],
        timeframe="1h",
        preset_id="BTCUSDT_1h_normal",
        leverage=10,
    )


@pytest.fixture
def sample_short_signal():
    """Create sample SHORT signal."""
    return TradingSignal(
        symbol="ETHUSDT",
        side=SignalSide.SHORT,
        entry_price=2300.0,
        stop_loss=2369.0,
        take_profits=[2254.0, 2208.0, 2162.0, 2116.0, 2070.0, 2001.0],
        timeframe="30m",
        preset_id="ETHUSDT_30m_high",
        leverage=10,
    )


@pytest.fixture
def bot_config():
    """Create bot configuration."""
    return BotConfig(
        bot_token="123456:ABC-DEF-GHI",
        chat_id="-100123456789",
        enabled=True,
    )


@pytest.fixture
def mock_bot(bot_config):
    """Create mock bot instance."""
    return TelegramBotMock(bot_config)


@pytest.fixture
def notification_settings():
    """Create notification settings."""
    return NotificationSettings(
        signal_new=True,
        tp_hit=True,
        sl_hit=True,
        system_error=True,
        system_info=False,
    )


@pytest_asyncio.fixture
async def notification_manager(bot_config, notification_settings):
    """Create notification manager with mock bot."""
    manager = NotificationManager(
        config=bot_config,
        settings=notification_settings,
        use_mock=True,
        leverage=10,
    )
    await manager.start()
    yield manager
    await manager.stop()


# =============================================================================
# CORNIX FORMATTER TESTS
# =============================================================================

class TestCornixFormatter:
    """Tests for CornixFormatter class."""
    
    def test_format_symbol_btcusdt(self, formatter):
        """Test BTC/USDT symbol formatting."""
        assert formatter.format_symbol("BTCUSDT") == "BTC/USDT"
    
    def test_format_symbol_ethusdt(self, formatter):
        """Test ETH/USDT symbol formatting."""
        assert formatter.format_symbol("ETHUSDT") == "ETH/USDT"
    
    def test_format_symbol_with_btc_quote(self, formatter):
        """Test symbol with BTC quote currency."""
        assert formatter.format_symbol("ETHBTC") == "ETH/BTC"
    
    def test_format_symbol_unknown(self, formatter):
        """Test unknown symbol passes through."""
        assert formatter.format_symbol("UNKNOWN") == "UNKNOWN"
    
    def test_format_price_large(self, formatter):
        """Test formatting large prices (BTC)."""
        assert formatter.format_price(42500.5) == "42500.5"
    
    def test_format_price_medium(self, formatter):
        """Test formatting medium prices (ETH)."""
        assert formatter.format_price(2300.50) == "2300.50"
    
    def test_format_price_small(self, formatter):
        """Test formatting small prices (altcoins)."""
        assert formatter.format_price(1.2345) == "1.2345"
    
    def test_format_price_very_small(self, formatter):
        """Test formatting very small prices."""
        assert formatter.format_price(0.000123) == "0.000123"
    
    def test_format_new_signal_long(self, formatter, sample_long_signal):
        """Test formatting LONG signal."""
        result = formatter.format_new_signal(sample_long_signal)
        
        # Check structure
        assert "⚡⚡ #BTC/USDT ⚡⚡" in result
        assert "Signal Type: Regular (Long)" in result
        assert "Leverage: Cross (10X)" in result
        assert "Entry Zone:" in result
        assert "42500" in result
        assert "Take-Profit Targets:" in result
        assert "1) 42925" in result
        assert "6) 47600" in result
        assert "Stop Targets:" in result
        assert "1) 41225" in result
        
        # Should NOT contain trailing config or exchange
        assert "Trailing" not in result
        assert "Exchanges:" not in result
    
    def test_format_new_signal_short(self, formatter, sample_short_signal):
        """Test formatting SHORT signal."""
        result = formatter.format_new_signal(sample_short_signal)
        
        assert "⚡⚡ #ETH/USDT ⚡⚡" in result
        assert "Signal Type: Regular (Short)" in result
        assert "2300" in result
        assert "1) 2254" in result
        assert "Stop Targets:" in result
    
    def test_format_tp_hit(self, formatter):
        """Test formatting TP hit notification."""
        event = TPHitEvent(
            symbol="BTCUSDT",
            side=SignalSide.LONG,
            tp_level=1,
            tp_price=42925.0,
            entry_price=42500.0,
            pnl_percent=1.0,
            position_closed_percent=20.0,
            remaining_percent=80.0,
            new_sl_price=42500.0,
            sl_moved_to="BE",
        )
        
        result = formatter.format_tp_hit(event)
        
        assert "✅ TP1 HIT" in result
        assert "BTC/USDT" in result
        assert "LONG" in result
        assert "20%" in result
        assert "+1.0%" in result
        assert "БУ" in result
        assert "80%" in result
    
    def test_format_tp_hit_cascade(self, formatter):
        """Test TP hit with cascade SL."""
        event = TPHitEvent(
            symbol="BTCUSDT",
            side=SignalSide.LONG,
            tp_level=2,
            tp_price=43350.0,
            entry_price=42500.0,
            pnl_percent=2.0,
            position_closed_percent=20.0,
            remaining_percent=60.0,
            new_sl_price=42925.0,
            sl_moved_to="TP1",
        )
        
        result = formatter.format_tp_hit(event)
        
        assert "TP2 HIT" in result
        assert "TP1" in result
    
    def test_format_sl_hit(self, formatter):
        """Test formatting SL hit notification."""
        event = SLHitEvent(
            symbol="ARBUSDT",
            side=SignalSide.SHORT,
            sl_price=1.31,
            entry_price=1.28,
            pnl_percent=-2.4,
            pnl_usd=-48.20,
            was_at_breakeven=False,
        )
        
        result = formatter.format_sl_hit(event)
        
        assert "⛔ SL HIT" in result
        assert "ARB/USDT" in result
        assert "SHORT" in result
        assert "-2.4%" in result
        assert "$48.20" in result
    
    def test_format_sl_hit_breakeven(self, formatter):
        """Test SL hit at breakeven."""
        event = SLHitEvent(
            symbol="BTCUSDT",
            side=SignalSide.LONG,
            sl_price=42500.0,
            entry_price=42500.0,
            pnl_percent=0.0,
            pnl_usd=0.0,
            was_at_breakeven=True,
        )
        
        result = formatter.format_sl_hit(event)
        
        assert "(БУ)" in result
    
    def test_format_system_alert_error(self, formatter):
        """Test error system alert."""
        result = formatter.format_system_alert("error", "Connection lost")
        
        assert "🔴" in result
        assert "СИСТЕМА" in result
        assert "Connection lost" in result
    
    def test_format_system_alert_warning(self, formatter):
        """Test warning system alert."""
        result = formatter.format_system_alert("warning", "High latency")
        
        assert "⚠️" in result
    
    def test_format_daily_summary(self, formatter):
        """Test daily summary formatting."""
        result = formatter.format_daily_summary(
            date="29.12.2024",
            total_trades=47,
            winning_trades=34,
            total_pnl_percent=8.92,
            total_pnl_usd=892.50,
            best_trade="BTCUSDT +3.5%",
            worst_trade="ARBUSDT -1.2%",
        )
        
        assert "📊 ИТОГИ ДНЯ" in result
        assert "29.12.2024" in result
        assert "47" in result
        assert "72.3%" in result  # Win rate
        assert "+8.92%" in result
        assert "$892.50" in result
        assert "BTCUSDT +3.5%" in result
    
    def test_calculate_tp_levels_long(self, formatter):
        """Test TP price calculation for LONG."""
        entry = 42500.0
        tp_pcts = [1.0, 2.0, 3.5, 5.0, 8.0, 12.0]
        
        tp_prices = formatter.calculate_tp_levels(entry, SignalSide.LONG, tp_pcts)
        
        assert len(tp_prices) == 6
        assert tp_prices[0] == 42925.0  # +1%
        assert tp_prices[1] == 43350.0  # +2%
        assert all(tp > entry for tp in tp_prices)
    
    def test_calculate_tp_levels_short(self, formatter):
        """Test TP price calculation for SHORT."""
        entry = 2300.0
        tp_pcts = [2.0, 4.0, 6.0, 8.0, 10.0, 13.0]
        
        tp_prices = formatter.calculate_tp_levels(entry, SignalSide.SHORT, tp_pcts)
        
        assert len(tp_prices) == 6
        assert tp_prices[0] == 2254.0  # -2%
        assert all(tp < entry for tp in tp_prices)
    
    def test_calculate_sl_level_long(self, formatter):
        """Test SL price calculation for LONG."""
        sl = formatter.calculate_sl_level(42500.0, SignalSide.LONG, 3.0)
        
        assert sl == 41225.0  # -3%
    
    def test_calculate_sl_level_short(self, formatter):
        """Test SL price calculation for SHORT."""
        sl = formatter.calculate_sl_level(2300.0, SignalSide.SHORT, 3.0)
        
        assert sl == 2369.0  # +3%


class TestTradingSignalValidation:
    """Tests for TradingSignal validation."""
    
    def test_valid_long_signal(self):
        """Test valid LONG signal creation."""
        signal = TradingSignal(
            symbol="BTCUSDT",
            side=SignalSide.LONG,
            entry_price=42500.0,
            stop_loss=41225.0,
            take_profits=[42925.0, 43350.0],
            timeframe="1h",
            preset_id="test",
        )
        
        assert signal.symbol == "BTCUSDT"
        assert signal.leverage == 10  # Default
    
    def test_invalid_long_sl_above_entry(self):
        """Test LONG signal with SL above entry fails."""
        with pytest.raises(ValueError, match="Stop loss must be below entry"):
            TradingSignal(
                symbol="BTCUSDT",
                side=SignalSide.LONG,
                entry_price=42500.0,
                stop_loss=43000.0,  # Above entry
                take_profits=[42925.0],
                timeframe="1h",
                preset_id="test",
            )
    
    def test_invalid_long_tp_below_entry(self):
        """Test LONG signal with TP below entry fails."""
        with pytest.raises(ValueError, match="take profits must be above entry"):
            TradingSignal(
                symbol="BTCUSDT",
                side=SignalSide.LONG,
                entry_price=42500.0,
                stop_loss=41225.0,
                take_profits=[42000.0],  # Below entry
                timeframe="1h",
                preset_id="test",
            )
    
    def test_invalid_short_sl_below_entry(self):
        """Test SHORT signal with SL below entry fails."""
        with pytest.raises(ValueError, match="Stop loss must be above entry"):
            TradingSignal(
                symbol="ETHUSDT",
                side=SignalSide.SHORT,
                entry_price=2300.0,
                stop_loss=2200.0,  # Below entry
                take_profits=[2254.0],
                timeframe="1h",
                preset_id="test",
            )
    
    def test_invalid_empty_take_profits(self):
        """Test signal with no TPs fails."""
        with pytest.raises(ValueError, match="At least one take profit"):
            TradingSignal(
                symbol="BTCUSDT",
                side=SignalSide.LONG,
                entry_price=42500.0,
                stop_loss=41225.0,
                take_profits=[],
                timeframe="1h",
                preset_id="test",
            )
    
    def test_invalid_leverage(self):
        """Test signal with invalid leverage fails."""
        with pytest.raises(ValueError, match="Leverage must be between"):
            TradingSignal(
                symbol="BTCUSDT",
                side=SignalSide.LONG,
                entry_price=42500.0,
                stop_loss=41225.0,
                take_profits=[42925.0],
                timeframe="1h",
                preset_id="test",
                leverage=200,  # Too high
            )


# =============================================================================
# TELEGRAM BOT TESTS
# =============================================================================

class TestBotConfig:
    """Tests for BotConfig validation."""
    
    def test_valid_config(self):
        """Test valid configuration."""
        config = BotConfig(
            bot_token="123456:ABC-DEF",
            chat_id="-100123456789",
        )
        
        assert config.enabled == True
        assert config.retry_attempts == 3
    
    def test_disabled_config_allows_empty_token(self):
        """Test disabled bot allows placeholder token."""
        config = BotConfig(
            bot_token="YOUR_TELEGRAM_BOT_TOKEN",
            chat_id="",
            enabled=False,
        )
        
        assert config.enabled == False
    
    def test_enabled_config_requires_valid_token(self):
        """Test enabled bot requires valid token."""
        with pytest.raises(ValueError, match="Valid bot_token required"):
            BotConfig(
                bot_token="YOUR_TELEGRAM_BOT_TOKEN",
                chat_id="-100123456789",
                enabled=True,
            )


class TestTelegramBotMock:
    """Tests for TelegramBotMock class."""
    
    @pytest.mark.asyncio
    async def test_mock_bot_lifecycle(self, mock_bot):
        """Test mock bot start/stop."""
        assert mock_bot.state == BotState.STOPPED
        
        await mock_bot.start()
        assert mock_bot.state == BotState.RUNNING
        assert mock_bot.is_running == True
        
        await mock_bot.stop()
        assert mock_bot.state == BotState.STOPPED
    
    @pytest.mark.asyncio
    async def test_mock_bot_send_message(self, mock_bot):
        """Test mock bot message sending."""
        await mock_bot.start()
        
        result = await mock_bot.send_message("Test message")
        
        assert result == True
        assert len(mock_bot.sent_messages) == 1
        assert mock_bot.sent_messages[0]["text"] == "Test message"
        assert mock_bot.stats["messages_sent"] == 1
    
    @pytest.mark.asyncio
    async def test_mock_bot_send_signal(self, mock_bot):
        """Test mock bot signal sending."""
        await mock_bot.start()
        
        result = await mock_bot.send_signal("Signal text")
        
        assert result == True
        assert mock_bot.sent_messages[-1]["priority"] == True
    
    @pytest.mark.asyncio
    async def test_mock_bot_get_last_message(self, mock_bot):
        """Test getting last message."""
        await mock_bot.start()
        
        await mock_bot.send_message("First")
        await mock_bot.send_message("Second")
        
        last = mock_bot.get_last_message()
        assert last["text"] == "Second"
    
    @pytest.mark.asyncio
    async def test_mock_bot_clear_messages(self, mock_bot):
        """Test clearing messages."""
        await mock_bot.start()
        
        await mock_bot.send_message("Test")
        assert len(mock_bot.sent_messages) == 1
        
        mock_bot.clear_messages()
        assert len(mock_bot.sent_messages) == 0
    
    @pytest.mark.asyncio
    async def test_mock_bot_test_connection(self, mock_bot):
        """Test connection test."""
        result = await mock_bot.test_connection()
        
        assert result["connected"] == True
        assert result["can_send"] == True
        assert result["error"] is None


# =============================================================================
# NOTIFICATION MANAGER TESTS
# =============================================================================

class TestNotificationManager:
    """Tests for NotificationManager class."""
    
    @pytest.mark.asyncio
    async def test_manager_lifecycle(self, notification_manager):
        """Test manager start/stop."""
        assert notification_manager.is_running == True
    
    @pytest.mark.asyncio
    async def test_notify_new_signal(self, notification_manager, sample_long_signal):
        """Test sending new signal notification."""
        result = await notification_manager.notify_new_signal(sample_long_signal)
        
        assert result == True
        
        # Check message was sent
        last_msg = notification_manager.bot.get_last_message()
        assert last_msg is not None
        assert "BTC/USDT" in last_msg["text"]
        assert "Long" in last_msg["text"]
    
    @pytest.mark.asyncio
    async def test_notify_tp_hit(self, notification_manager):
        """Test TP hit notification."""
        event = TPHitEvent(
            symbol="BTCUSDT",
            side=SignalSide.LONG,
            tp_level=1,
            tp_price=42925.0,
            entry_price=42500.0,
            pnl_percent=1.0,
            position_closed_percent=20.0,
            remaining_percent=80.0,
            new_sl_price=42500.0,
            sl_moved_to="BE",
        )
        
        result = await notification_manager.notify_tp_hit(event)
        
        assert result == True
        
        last_msg = notification_manager.bot.get_last_message()
        assert "TP1 HIT" in last_msg["text"]
    
    @pytest.mark.asyncio
    async def test_notify_sl_hit(self, notification_manager):
        """Test SL hit notification."""
        event = SLHitEvent(
            symbol="ARBUSDT",
            side=SignalSide.SHORT,
            sl_price=1.31,
            entry_price=1.28,
            pnl_percent=-2.4,
            pnl_usd=-48.20,
        )
        
        result = await notification_manager.notify_sl_hit(event)
        
        assert result == True
        
        # Check daily stats updated
        stats = notification_manager.stats
        assert stats["daily_stats"]["total_trades"] == 1
    
    @pytest.mark.asyncio
    async def test_notify_system_error(self, notification_manager):
        """Test system error notification."""
        result = await notification_manager.notify_system_error("Test error")
        
        assert result == True
        
        last_msg = notification_manager.bot.get_last_message()
        assert "🔴" in last_msg["text"]
    
    @pytest.mark.asyncio
    async def test_disabled_notification_not_sent(self, bot_config):
        """Test disabled notification type not sent."""
        settings = NotificationSettings(
            signal_new=False,  # Disabled
            tp_hit=True,
        )
        
        manager = NotificationManager(
            config=bot_config,
            settings=settings,
            use_mock=True,
        )
        await manager.start()
        
        signal = TradingSignal(
            symbol="BTCUSDT",
            side=SignalSide.LONG,
            entry_price=42500.0,
            stop_loss=41225.0,
            take_profits=[42925.0],
            timeframe="1h",
            preset_id="test",
        )
        
        result = await manager.notify_new_signal(signal)
        
        assert result == False
        assert len(manager.bot.sent_messages) == 0
        
        await manager.stop()
    
    @pytest.mark.asyncio
    async def test_daily_stats_tracking(self, notification_manager):
        """Test daily statistics tracking."""
        # Record some trades
        notification_manager.record_trade_result("BTCUSDT", 2.5, 250.0, True)
        notification_manager.record_trade_result("ETHUSDT", -1.0, -100.0, False)
        notification_manager.record_trade_result("SOLUSDT", 1.5, 150.0, True)
        
        stats = notification_manager.stats["daily_stats"]
        
        assert stats["total_trades"] == 3
        assert stats["winning_trades"] == 2
        assert abs(stats["win_rate"] - 66.67) < 0.1
        assert stats["total_pnl_percent"] == 3.0
        assert stats["total_pnl_usd"] == 300.0
    
    @pytest.mark.asyncio
    async def test_notification_history(self, notification_manager, sample_long_signal):
        """Test notification history tracking."""
        await notification_manager.notify_new_signal(sample_long_signal)
        await notification_manager.notify_system_error("Test error")
        
        history = notification_manager.get_notification_history()
        
        assert len(history) == 2
        assert history[0]["type"] == "signal_new"
        assert history[1]["type"] == "system_error"
    
    @pytest.mark.asyncio
    async def test_notification_history_filter(self, notification_manager, sample_long_signal):
        """Test notification history filtering."""
        await notification_manager.notify_new_signal(sample_long_signal)
        await notification_manager.notify_system_error("Test")
        
        filtered = notification_manager.get_notification_history(
            notification_type=NotificationType.SIGNAL_NEW
        )
        
        assert len(filtered) == 1
        assert filtered[0]["type"] == "signal_new"
    
    @pytest.mark.asyncio
    async def test_test_notification(self, notification_manager):
        """Test sending test notification."""
        result = await notification_manager.test_notification()
        
        assert result == True
        
        last_msg = notification_manager.bot.get_last_message()
        assert "Test notification" in last_msg["text"]


class TestNotificationManagerFactory:
    """Tests for notification manager factory."""
    
    @pytest.mark.asyncio
    async def test_create_notification_manager(self):
        """Test factory function."""
        manager = await create_notification_manager(
            bot_token="test-token",
            chat_id="-100123",
            enabled=True,
            use_mock=True,
        )
        
        assert manager.is_running == True
        
        await manager.stop()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for full notification flow."""
    
    @pytest.mark.asyncio
    async def test_full_trade_cycle(self, notification_manager):
        """Test complete trade notification cycle."""
        # 1. Send new signal
        signal = TradingSignal(
            symbol="BTCUSDT",
            side=SignalSide.LONG,
            entry_price=42500.0,
            stop_loss=41225.0,
            take_profits=[42925.0, 43350.0, 43988.0, 44625.0, 45900.0, 47600.0],
            timeframe="1h",
            preset_id="BTCUSDT_1h_normal",
        )
        
        await notification_manager.notify_new_signal(signal)
        
        # 2. TP1 hit
        tp1_event = TPHitEvent(
            symbol="BTCUSDT",
            side=SignalSide.LONG,
            tp_level=1,
            tp_price=42925.0,
            entry_price=42500.0,
            pnl_percent=1.0,
            position_closed_percent=20.0,
            remaining_percent=80.0,
            new_sl_price=42500.0,
            sl_moved_to="BE",
        )
        
        await notification_manager.notify_tp_hit(tp1_event)
        
        # 3. TP2 hit
        tp2_event = TPHitEvent(
            symbol="BTCUSDT",
            side=SignalSide.LONG,
            tp_level=2,
            tp_price=43350.0,
            entry_price=42500.0,
            pnl_percent=2.0,
            position_closed_percent=20.0,
            remaining_percent=60.0,
            new_sl_price=42925.0,
            sl_moved_to="TP1",
        )
        
        await notification_manager.notify_tp_hit(tp2_event)
        
        # 4. Position update
        await notification_manager.notify_position_update(
            symbol="BTCUSDT",
            side=SignalSide.LONG,
            update_type="Частичное закрытие",
            details="40% позиции закрыто с прибылью",
        )
        
        # Verify all messages sent
        messages = notification_manager.bot.sent_messages
        assert len(messages) >= 4
        
        # Verify stats
        stats = notification_manager.stats
        assert stats["daily_stats"]["signals_generated"] == 1
    
    @pytest.mark.asyncio
    async def test_losing_trade(self, notification_manager):
        """Test losing trade flow."""
        # Send signal
        signal = TradingSignal(
            symbol="ARBUSDT",
            side=SignalSide.SHORT,
            entry_price=1.28,
            stop_loss=1.31,
            take_profits=[1.25, 1.22, 1.19],
            timeframe="30m",
            preset_id="ARBUSDT_30m_normal",
        )
        
        await notification_manager.notify_new_signal(signal)
        
        # SL hit
        sl_event = SLHitEvent(
            symbol="ARBUSDT",
            side=SignalSide.SHORT,
            sl_price=1.31,
            entry_price=1.28,
            pnl_percent=-2.34,
            pnl_usd=-46.80,
        )
        
        await notification_manager.notify_sl_hit(sl_event)
        
        # Verify stats
        stats = notification_manager.stats
        assert stats["daily_stats"]["total_trades"] == 1
        assert stats["daily_stats"]["winning_trades"] == 0


# =============================================================================
# CORNIX FORMAT COMPLIANCE TESTS
# =============================================================================

class TestCornixFormatCompliance:
    """Tests to verify Cornix format compliance."""
    
    def test_signal_has_required_fields(self, formatter, sample_long_signal):
        """Test signal contains all Cornix required fields."""
        result = formatter.format_new_signal(sample_long_signal)
        
        # Required by Cornix
        required_patterns = [
            "#",                    # Hashtag with symbol
            "Signal Type:",         # Signal type
            "Leverage:",            # Leverage indication
            "Entry Zone:",          # Entry keyword
            "Take-Profit Targets:", # TP keyword
            "Stop Targets:",        # SL keyword
        ]
        
        for pattern in required_patterns:
            assert pattern in result, f"Missing required pattern: {pattern}"
    
    def test_signal_uses_prices_not_percentages(self, formatter, sample_long_signal):
        """Test targets are prices, not percentages."""
        result = formatter.format_new_signal(sample_long_signal)
        
        # Should contain actual prices
        assert "42925" in result
        assert "41225" in result
        
        # Should NOT contain percentage signs in targets
        lines = result.split("\n")
        for line in lines:
            if line.startswith(("1)", "2)", "3)", "4)", "5)", "6)")):
                assert "%" not in line
    
    def test_signal_plain_text_format(self, formatter, sample_long_signal):
        """Test signal is plain text (no HTML/Markdown)."""
        result = formatter.format_new_signal(sample_long_signal)
        
        # Should NOT contain HTML/Markdown
        assert "<" not in result
        assert ">" not in result
        assert "**" not in result
        assert "__" not in result
    
    def test_max_10_take_profits(self, formatter):
        """Test Cornix max 10 TP limit validation."""
        with pytest.raises(ValueError, match="Maximum 10 take profit"):
            TradingSignal(
                symbol="BTCUSDT",
                side=SignalSide.LONG,
                entry_price=42500.0,
                stop_loss=41225.0,
                take_profits=[42600 + i * 100 for i in range(11)],  # 11 TPs
                timeframe="1h",
                preset_id="test",
            )


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
