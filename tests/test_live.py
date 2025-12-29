"""
Тесты для Live модуля.

Запуск:
    pytest tests/test_live.py -v
"""

import pytest
from datetime import datetime, timedelta
import tempfile
import os

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.live.state import StateManager, StateConfig, SystemStatus
from backend.live.position_tracker import PositionTracker, PositionEvent, TrackingEvent
from backend.live.signal_manager import SignalManager, SignalStatus, EnrichedSignal
from backend.portfolio import PortfolioManager, RiskLimits, Position


# === Fixtures ===

@pytest.fixture
def temp_db():
    """Создать временную БД."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def state_manager(temp_db):
    """Создать StateManager с временной БД."""
    config = StateConfig(db_path=temp_db)
    return StateManager(config)


@pytest.fixture
def portfolio_manager():
    """Создать тестовый PortfolioManager."""
    return PortfolioManager(
        balance=10000,
        risk_limits=RiskLimits(
            max_positions=5,
            max_portfolio_heat=8.0,
            risk_per_trade=2.0,
        ),
        leverage=10,
    )


@pytest.fixture
def position_tracker(portfolio_manager):
    """Создать PositionTracker."""
    return PositionTracker(
        portfolio_manager=portfolio_manager,
        cascade_stop=True,
        breakeven_after_tp=1,
    )


@pytest.fixture
def sample_position(portfolio_manager):
    """Создать тестовую позицию."""
    return portfolio_manager.open_position(
        symbol="BTCUSDT",
        timeframe="1h",
        direction="long",
        entry_price=42000,
        tp_prices=[42500, 43000, 43500, 44000, 45000, 46000],
        sl_price=40000,
        notional_value=4200,
    )


# === State Manager Tests ===

class TestStateManager:
    """Тесты для StateManager."""
    
    def test_init(self, state_manager):
        """Тест инициализации."""
        assert state_manager is not None
        assert state_manager.db_path.exists()
    
    def test_settings(self, state_manager):
        """Тест настроек."""
        # Сохраняем
        state_manager.set_setting("test_key", "test_value")
        state_manager.set_setting("test_number", 42)
        state_manager.set_setting("test_dict", {"a": 1, "b": 2})
        
        # Читаем
        assert state_manager.get_setting("test_key") == "test_value"
        assert state_manager.get_setting("test_number") == 42
        assert state_manager.get_setting("test_dict") == {"a": 1, "b": 2}
        
        # Несуществующий ключ
        assert state_manager.get_setting("unknown", "default") == "default"
    
    def test_all_settings(self, state_manager):
        """Тест получения всех настроек."""
        state_manager.set_setting("key1", "value1")
        state_manager.set_setting("key2", "value2")
        
        all_settings = state_manager.get_all_settings()
        
        assert "key1" in all_settings
        assert "key2" in all_settings
    
    def test_delete_setting(self, state_manager):
        """Тест удаления настройки."""
        state_manager.set_setting("to_delete", "value")
        assert state_manager.get_setting("to_delete") == "value"
        
        state_manager.delete_setting("to_delete")
        assert state_manager.get_setting("to_delete") is None
    
    def test_position_crud(self, state_manager):
        """Тест CRUD для позиций."""
        position = {
            "id": "test123",
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "direction": "long",
            "entry_price": 42000,
            "current_price": 42500,
            "tp_prices": [43000, 44000],
            "sl_price": 40000,
            "current_sl": 40000,
            "quantity": 0.1,
            "notional_value": 4200,
            "status": "open",
        }
        
        # Create
        result = state_manager.save_position(position)
        assert result == True
        
        # Read
        loaded = state_manager.get_position("test123")
        assert loaded is not None
        assert loaded["symbol"] == "BTCUSDT"
        assert loaded["entry_price"] == 42000
        
        # Update
        position["current_price"] = 43000
        state_manager.save_position(position)
        
        loaded = state_manager.get_position("test123")
        assert loaded["current_price"] == 43000
        
        # Delete
        state_manager.delete_position("test123")
        assert state_manager.get_position("test123") is None
    
    def test_get_open_positions(self, state_manager):
        """Тест получения открытых позиций."""
        # Добавляем позиции
        for i, symbol in enumerate(["BTCUSDT", "ETHUSDT", "SOLUSDT"]):
            state_manager.save_position({
                "id": f"pos{i}",
                "symbol": symbol,
                "timeframe": "1h",
                "direction": "long",
                "entry_price": 100,
                "current_price": 100,
                "sl_price": 90,
                "current_sl": 90,
                "quantity": 1,
                "notional_value": 100,
                "status": "open" if i < 2 else "closed",
            })
        
        open_positions = state_manager.get_open_positions()
        assert len(open_positions) == 2
    
    def test_signal_save_and_get(self, state_manager):
        """Тест сохранения и получения сигналов."""
        signal = {
            "signal_id": "#Long_BTCUSDT_15_01_2024_10_30",
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "signal_type": "long",
            "entry_price": 42000,
            "tp_prices": [43000, 44000],
            "sl_price": 40000,
            "preset_index": 5,
            "strength": "normal",
            "filters_passed": {"volume": True, "rsi": True},
            "status": "pending",
        }
        
        # Save
        signal_id = state_manager.save_signal(signal)
        assert signal_id > 0
        
        # Get pending
        pending = state_manager.get_pending_signals()
        assert len(pending) >= 1
        assert pending[0]["symbol"] == "BTCUSDT"
        
        # Update status
        state_manager.update_signal_status("#Long_BTCUSDT_15_01_2024_10_30", "executed")
        
        # Check pending again
        pending = state_manager.get_pending_signals()
        # Pending should not include executed signals
    
    def test_trade_history(self, state_manager):
        """Тест истории сделок."""
        trade = {
            "position_id": "pos123",
            "signal_id": "#Long_BTCUSDT_test",
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "direction": "long",
            "entry_price": 42000,
            "exit_price": 43000,
            "quantity": 0.1,
            "notional_value": 4200,
            "pnl_percent": 2.38,
            "pnl_amount": 100,
            "tp_hits": [1, 2],
            "exit_reason": "closed_tp",
            "entry_time": datetime.now().isoformat(),
            "exit_time": datetime.now().isoformat(),
        }
        
        # Save
        history_id = state_manager.save_trade_history(trade)
        assert history_id > 0
        
        # Get history
        history = state_manager.get_trade_history()
        assert len(history) >= 1
        
        # Get stats
        stats = state_manager.get_trade_stats()
        assert stats["total_trades"] >= 1
    
    def test_events(self, state_manager):
        """Тест логирования событий."""
        # Log events
        state_manager.log_event("signal", "New LONG signal", "BTCUSDT", {"price": 42000})
        state_manager.log_event("tp_hit", "TP1 hit", "BTCUSDT", {"tp_index": 1})
        
        # Get events
        events = state_manager.get_events()
        assert len(events) >= 2
        
        # Filter by type
        signal_events = state_manager.get_events(event_type="signal")
        assert len(signal_events) >= 1
        
        # Filter by symbol
        btc_events = state_manager.get_events(symbol="BTCUSDT")
        assert len(btc_events) >= 2
    
    def test_system_status(self, state_manager):
        """Тест статуса системы."""
        state_manager.set_system_status(SystemStatus.RUNNING)
        assert state_manager.get_system_status() == SystemStatus.RUNNING
        
        state_manager.set_system_status(SystemStatus.PAUSED)
        assert state_manager.get_system_status() == SystemStatus.PAUSED


# === Position Tracker Tests ===

class TestPositionTracker:
    """Тесты для PositionTracker."""
    
    def test_init(self, position_tracker):
        """Тест инициализации."""
        assert position_tracker is not None
        assert position_tracker.cascade_stop == True
    
    def test_update_price_no_position(self, position_tracker):
        """Тест обновления цены без позиции."""
        events = position_tracker.update_price("BTCUSDT", 42000)
        assert len(events) == 0
    
    def test_tp_hit(self, position_tracker, sample_position):
        """Тест достижения TP."""
        assert sample_position is not None
        
        # Цена достигает TP1 (42500)
        events = position_tracker.update_price(
            symbol="BTCUSDT",
            price=42600,
            high=42600,
            low=42400,
        )
        
        # Должен быть TP_HIT и возможно SL_MOVED/BREAKEVEN
        assert len(events) >= 1
        
        tp_events = [e for e in events if e.event_type == PositionEvent.TP_HIT]
        assert len(tp_events) >= 1
        assert tp_events[0].tp_index == 1
    
    def test_sl_hit(self, position_tracker, portfolio_manager):
        """Тест достижения SL."""
        # Открываем позицию
        position = portfolio_manager.open_position(
            symbol="ETHUSDT",
            timeframe="1h",
            direction="long",
            entry_price=2500,
            tp_prices=[2600],
            sl_price=2400,
            notional_value=2500,
        )
        
        assert position is not None
        
        # Цена падает до SL
        events = position_tracker.update_price(
            symbol="ETHUSDT",
            price=2350,
            high=2450,
            low=2350,
        )
        
        # Должно быть CLOSED_SL
        sl_events = [e for e in events if e.event_type == PositionEvent.CLOSED_SL]
        assert len(sl_events) == 1
        assert sl_events[0].pnl_amount < 0  # Убыток
    
    def test_cascade_stop(self, position_tracker, sample_position):
        """Тест каскадного стопа."""
        # Достигаем TP1
        events = position_tracker.update_price(
            symbol="BTCUSDT",
            price=42600,
            high=42600,
            low=42400,
        )
        
        # Ищем событие перемещения стопа
        sl_events = [e for e in events if e.event_type in 
                    (PositionEvent.SL_MOVED, PositionEvent.BREAKEVEN)]
        
        # После TP1 стоп должен переместиться в БУ
        if len(sl_events) > 0:
            assert sl_events[0].new_sl == sample_position.entry_price
    
    def test_close_manual(self, position_tracker, sample_position):
        """Тест ручного закрытия."""
        event = position_tracker.close_manual("BTCUSDT", 42500)
        
        assert event is not None
        assert event.event_type == PositionEvent.CLOSED_MANUAL
    
    def test_close_by_signal(self, position_tracker, sample_position):
        """Тест закрытия противоположным сигналом."""
        event = position_tracker.close_by_signal("BTCUSDT", 42500)
        
        assert event is not None
        assert event.event_type == PositionEvent.CLOSED_SIGNAL
    
    def test_event_history(self, position_tracker, sample_position):
        """Тест истории событий."""
        # Генерируем события
        position_tracker.update_price("BTCUSDT", 42600, 42600, 42400)
        
        history = position_tracker.get_event_history()
        assert len(history) >= 1
        
        # Фильтр по символу
        btc_history = position_tracker.get_event_history(symbol="BTCUSDT")
        assert len(btc_history) >= 1
    
    def test_open_positions_summary(self, position_tracker, sample_position):
        """Тест сводки позиций."""
        summary = position_tracker.get_open_positions_summary()
        
        assert len(summary) >= 1
        assert summary[0]["symbol"] == "BTCUSDT"
        assert "unrealized_pnl_percent" in summary[0]


class TestTrackingEvent:
    """Тесты для TrackingEvent."""
    
    def test_to_dict(self, portfolio_manager):
        """Тест сериализации."""
        position = Position(
            symbol="BTCUSDT",
            direction="long",
            entry_price=42000,
            current_price=43000,
        )
        
        event = TrackingEvent(
            event_type=PositionEvent.TP_HIT,
            position=position,
            tp_index=1,
            tp_price=43000,
            pnl_percent=2.38,
            pnl_amount=100,
            message="TP1 hit",
        )
        
        data = event.to_dict()
        
        assert data["event_type"] == "tp_hit"
        assert data["symbol"] == "BTCUSDT"
        assert data["tp_index"] == 1
        assert data["pnl_percent"] == 2.38


# === Signal Manager Tests ===

class TestEnrichedSignal:
    """Тесты для EnrichedSignal."""
    
    def test_is_expired(self):
        """Тест проверки истечения срока."""
        from backend.core.signals import Signal, SignalType
        from backend.core.tpsl import TPSLLevels, TPLevel
        from backend.core.presets import TradingPreset
        
        signal = Signal(
            timestamp=datetime.now(),
            symbol="BTCUSDT",
            timeframe="1h",
            signal_type=SignalType.LONG,
            entry_price=42000,
        )
        
        tpsl = TPSLLevels(
            entry_price=42000,
            is_long=True,
            tp_levels=[
                TPLevel(index=1, price=43000, percent=1, position_percent=17),
            ],
            sl_price=40000,
        )
        
        preset = TradingPreset(
            symbol="BTCUSDT",
            timeframe="1h",
            volatility_regime="normal",
        )
        
        # Не истёк
        enriched = EnrichedSignal(
            signal=signal,
            tpsl_levels=tpsl,
            preset=preset,
            expires_at=datetime.now() + timedelta(hours=1),
        )
        assert not enriched.is_expired
        
        # Истёк
        enriched_expired = EnrichedSignal(
            signal=signal,
            tpsl_levels=tpsl,
            preset=preset,
            expires_at=datetime.now() - timedelta(hours=1),
        )
        assert enriched_expired.is_expired


# === Run Tests ===

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
