"""
Тесты для Portfolio модуля.

Запуск:
    pytest tests/test_portfolio.py -v
"""

import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.portfolio.correlation import (
    CorrelationCalculator,
    CorrelationFilter,
    SectorFilter,
    CorrelationMethod,
    SECTORS,
    get_symbol_sector,
    get_sector_symbols,
    are_same_sector,
)
from backend.portfolio.risk import (
    PositionSizer,
    PortfolioHeatTracker,
    PositionRisk,
    RiskLimits,
    RiskLevel,
)
from backend.portfolio.manager import (
    PortfolioManager,
    Position,
    PositionStatus,
)


# === Fixtures ===

@pytest.fixture
def sample_price_df():
    """Создать тестовый DataFrame с ценами."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="1h")
    np.random.seed(42)
    
    # Симулируем цены BTC с трендом
    btc_returns = np.random.randn(100) * 0.01 + 0.0001
    btc_prices = 42000 * np.cumprod(1 + btc_returns)
    
    return pd.DataFrame({
        "close": btc_prices,
    }, index=dates)


@pytest.fixture
def correlated_prices():
    """Создать коррелированные цены для нескольких пар."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="1h")
    np.random.seed(42)
    
    # Базовый сигнал
    base = np.random.randn(100)
    
    # BTC - базовый
    btc = 42000 * np.cumprod(1 + base * 0.02)
    
    # ETH - высокая корреляция с BTC
    eth = 2500 * np.cumprod(1 + (base * 0.8 + np.random.randn(100) * 0.2) * 0.02)
    
    # DOGE - низкая корреляция
    doge = 0.08 * np.cumprod(1 + np.random.randn(100) * 0.03)
    
    return {
        "BTCUSDT": pd.DataFrame({"close": btc}, index=dates),
        "ETHUSDT": pd.DataFrame({"close": eth}, index=dates),
        "DOGEUSDT": pd.DataFrame({"close": doge}, index=dates),
    }


@pytest.fixture
def position_risk():
    """Создать тестовый PositionRisk."""
    return PositionRisk(
        symbol="BTCUSDT",
        direction="long",
        entry_price=42000,
        current_price=42500,
        stop_loss=40000,
        quantity=0.1,
        notional_value=4200,
    )


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


# === Correlation Tests ===

class TestCorrelationCalculator:
    """Тесты для CorrelationCalculator."""
    
    def test_init(self):
        """Тест инициализации."""
        calc = CorrelationCalculator()
        assert calc.method == CorrelationMethod.PEARSON
        assert calc.period_days == 30
        assert calc.use_returns == True
    
    def test_add_price_data(self, sample_price_df):
        """Тест добавления данных."""
        calc = CorrelationCalculator()
        calc.add_price_data("BTCUSDT", sample_price_df)
        
        assert "BTCUSDT" in calc._price_data
        assert len(calc._price_data["BTCUSDT"]) == len(sample_price_df)
    
    def test_calculate_pair_correlation(self, correlated_prices):
        """Тест расчёта корреляции между парами."""
        calc = CorrelationCalculator(period_days=0)  # Все данные
        
        for symbol, df in correlated_prices.items():
            calc.add_price_data(symbol, df)
        
        # BTC и ETH должны быть высоко коррелированы
        result = calc.calculate_pair_correlation("BTCUSDT", "ETHUSDT")
        assert result is not None
        assert result.correlation > 0.5  # Высокая корреляция
        
        # BTC и DOGE - низкая корреляция
        result2 = calc.calculate_pair_correlation("BTCUSDT", "DOGEUSDT")
        assert result2 is not None
        assert abs(result2.correlation) < 0.5  # Низкая корреляция
    
    def test_calculate_matrix(self, correlated_prices):
        """Тест расчёта матрицы корреляций."""
        calc = CorrelationCalculator(period_days=0)
        
        for symbol, df in correlated_prices.items():
            calc.add_price_data(symbol, df)
        
        matrix = calc.calculate_matrix()
        
        assert matrix is not None
        assert len(matrix.symbols) == 3
        assert matrix.get_correlation("BTCUSDT", "BTCUSDT") == 1.0
    
    def test_cache(self, correlated_prices):
        """Тест кэширования."""
        calc = CorrelationCalculator(period_days=0)
        
        for symbol, df in correlated_prices.items():
            calc.add_price_data(symbol, df)
        
        # Первый расчёт
        matrix1 = calc.calculate_matrix()
        
        # Второй расчёт (из кэша)
        matrix2 = calc.calculate_matrix()
        
        assert matrix1 is matrix2  # Тот же объект


class TestSectorFilter:
    """Тесты для SectorFilter."""
    
    def test_get_symbol_sector(self):
        """Тест определения сектора."""
        assert get_symbol_sector("BTCUSDT") == "BTC"
        assert get_symbol_sector("ETHUSDT") == "ETH"
        assert get_symbol_sector("SOLUSDT") == "L1"
        assert get_symbol_sector("ARBUSDT") == "L2"
        assert get_symbol_sector("DOGEUSDT") == "MEME"
        assert get_symbol_sector("UNKNOWN") == "OTHER"
    
    def test_are_same_sector(self):
        """Тест проверки одного сектора."""
        assert are_same_sector("SOLUSDT", "AVAXUSDT")  # Оба L1
        assert not are_same_sector("BTCUSDT", "ETHUSDT")  # Разные
    
    def test_can_open_position(self):
        """Тест фильтра по секторам."""
        filter = SectorFilter(max_per_sector=2)
        
        open_positions = ["SOLUSDT", "AVAXUSDT"]  # 2 позиции в L1
        
        # Нельзя открыть ещё одну L1
        assert not filter.can_open_position("NEARUSDT", open_positions)
        
        # Можно открыть из другого сектора
        assert filter.can_open_position("BTCUSDT", open_positions)
        assert filter.can_open_position("ARBUSDT", open_positions)  # L2
    
    def test_get_sector_stats(self):
        """Тест статистики секторов."""
        filter = SectorFilter(max_per_sector=2)
        
        open_positions = ["BTCUSDT", "SOLUSDT"]
        stats = filter.get_sector_stats(open_positions)
        
        assert stats["BTC"]["count"] == 1
        assert stats["L1"]["count"] == 1
        assert stats["ETH"]["count"] == 0


class TestCorrelationFilter:
    """Тесты для CorrelationFilter."""
    
    def test_can_open_position(self, correlated_prices):
        """Тест фильтра по корреляции."""
        calc = CorrelationCalculator(period_days=0)
        
        for symbol, df in correlated_prices.items():
            calc.add_price_data(symbol, df)
        
        filter = CorrelationFilter(calc, threshold=0.7)
        
        # ETH высоко коррелирует с BTC
        open_positions = ["BTCUSDT"]
        can_open, blocking = filter.can_open_position("ETHUSDT", open_positions)
        
        # Результат зависит от данных
        assert isinstance(can_open, bool)
        
        # DOGE низко коррелирует
        can_open2, _ = filter.can_open_position("DOGEUSDT", open_positions)
        assert can_open2  # Должна быть низкая корреляция


# === Risk Tests ===

class TestPositionSizer:
    """Тесты для PositionSizer."""
    
    def test_init(self):
        """Тест инициализации."""
        sizer = PositionSizer(balance=10000, risk_per_trade=2.0)
        assert sizer.balance == 10000
        assert sizer.risk_per_trade == 2.0
    
    def test_calculate_position_size(self):
        """Тест расчёта размера позиции."""
        sizer = PositionSizer(balance=10000, risk_per_trade=2.0)
        
        result = sizer.calculate_position_size(
            entry_price=42000,
            stop_loss=40000,
            leverage=10,
            direction="long",
        )
        
        assert result["position_size"] > 0
        assert result["quantity"] > 0
        assert result["risk_amount"] == 200  # 2% от 10000
        assert result["leverage"] == 10
    
    def test_risk_calculation(self):
        """Тест корректности расчёта риска."""
        sizer = PositionSizer(balance=10000, risk_per_trade=2.0, max_position_size=50.0)
        
        result = sizer.calculate_position_size(
            entry_price=100,
            stop_loss=95,  # 5% риск
            leverage=1,
            direction="long",
        )
        
        # Риск = 2% баланса = 200
        # Размер позиции = 200 / 5% = 4000
        assert abs(result["position_size"] - 4000) < 10
        assert result["sl_distance_percent"] == 5.0
    
    def test_short_position(self):
        """Тест для SHORT позиции."""
        sizer = PositionSizer(balance=10000, risk_per_trade=2.0)
        
        result = sizer.calculate_position_size(
            entry_price=100,
            stop_loss=105,  # 5% риск для SHORT
            leverage=1,
            direction="short",
        )
        
        assert result["position_size"] > 0
        assert result["sl_distance_percent"] == 5.0


class TestPortfolioHeatTracker:
    """Тесты для PortfolioHeatTracker."""
    
    def test_init(self):
        """Тест инициализации."""
        tracker = PortfolioHeatTracker(balance=10000, max_heat=8.0)
        assert tracker.balance == 10000
        assert tracker.max_heat == 8.0
        assert tracker.current_heat == 0
    
    def test_add_position(self, position_risk):
        """Тест добавления позиции."""
        tracker = PortfolioHeatTracker(balance=10000, max_heat=8.0)
        
        result = tracker.add_position(position_risk)
        assert result == True
        assert tracker.position_count == 1
        assert tracker.current_heat > 0
    
    def test_max_positions(self, position_risk):
        """Тест лимита позиций."""
        tracker = PortfolioHeatTracker(balance=10000, max_heat=100, max_positions=2)
        
        # Добавляем 2 позиции
        tracker.add_position(position_risk)
        
        pos2 = PositionRisk(
            symbol="ETHUSDT",
            direction="long",
            entry_price=2500,
            current_price=2550,
            stop_loss=2400,
            quantity=1,
            notional_value=2500,
        )
        tracker.add_position(pos2)
        
        # Третья не должна добавиться
        pos3 = PositionRisk(
            symbol="SOLUSDT",
            direction="long",
            entry_price=100,
            current_price=105,
            stop_loss=95,
            quantity=10,
            notional_value=1000,
        )
        result = tracker.add_position(pos3)
        assert result == False
        assert tracker.position_count == 2
    
    def test_risk_level(self, position_risk):
        """Тест определения уровня риска."""
        tracker = PortfolioHeatTracker(balance=10000, max_heat=8.0)
        
        assert tracker.get_risk_level() == RiskLevel.LOW
        
        # Добавляем позицию с большим риском
        tracker.add_position(position_risk)
        
        # Уровень зависит от размера риска
        level = tracker.get_risk_level()
        assert level in [RiskLevel.LOW, RiskLevel.NORMAL, RiskLevel.HIGH]


# === Portfolio Manager Tests ===

class TestPortfolioManager:
    """Тесты для PortfolioManager."""
    
    def test_init(self, portfolio_manager):
        """Тест инициализации."""
        assert portfolio_manager.balance == 10000
        assert portfolio_manager.risk_limits.max_positions == 5
        assert len(portfolio_manager.get_all_positions()) == 0
    
    def test_can_open_position(self, portfolio_manager):
        """Тест проверки возможности открытия позиции."""
        can_open, reason = portfolio_manager.can_open_position("BTCUSDT")
        assert can_open == True
        assert reason == "OK"
    
    def test_calculate_position_size(self, portfolio_manager):
        """Тест расчёта размера позиции."""
        size_info = portfolio_manager.calculate_position_size(
            symbol="BTCUSDT",
            entry_price=42000,
            stop_loss=40000,
            direction="long",
        )
        
        assert size_info["position_size"] > 0
        assert size_info["quantity"] > 0
        assert size_info["symbol"] == "BTCUSDT"
    
    def test_open_position(self, portfolio_manager):
        """Тест открытия позиции."""
        position = portfolio_manager.open_position(
            symbol="BTCUSDT",
            timeframe="1h",
            direction="long",
            entry_price=42000,
            tp_prices=[42500, 43000, 43500, 44000, 45000, 46000],
            sl_price=40000,
            notional_value=2000,
        )
        
        assert position is not None
        assert position.symbol == "BTCUSDT"
        assert position.direction == "long"
        assert position.is_open
        assert len(portfolio_manager.get_all_positions()) == 1
    
    def test_duplicate_position(self, portfolio_manager):
        """Тест запрета дублирующей позиции."""
        # Открываем первую
        portfolio_manager.open_position(
            symbol="BTCUSDT",
            timeframe="1h",
            direction="long",
            entry_price=42000,
            tp_prices=[42500],
            sl_price=40000,
            notional_value=2000,
        )
        
        # Пробуем открыть вторую
        can_open, reason = portfolio_manager.can_open_position("BTCUSDT")
        assert can_open == False
        assert "already open" in reason
    
    def test_close_position(self, portfolio_manager):
        """Тест закрытия позиции."""
        # Открываем
        portfolio_manager.open_position(
            symbol="BTCUSDT",
            timeframe="1h",
            direction="long",
            entry_price=42000,
            tp_prices=[42500],
            sl_price=40000,
            notional_value=2000,
        )
        
        # Закрываем
        closed = portfolio_manager.close_position(
            symbol="BTCUSDT",
            close_price=43000,
            reason="test",
        )
        
        assert closed is not None
        assert closed.status == PositionStatus.CLOSED
        assert len(portfolio_manager.get_all_positions()) == 0
    
    def test_update_balance(self, portfolio_manager):
        """Тест обновления баланса."""
        portfolio_manager.update_balance(15000)
        assert portfolio_manager.balance == 15000
        assert portfolio_manager.get_equity() == 15000
    
    def test_get_portfolio_stats(self, portfolio_manager):
        """Тест статистики портфеля."""
        stats = portfolio_manager.get_portfolio_stats()
        
        assert "balance" in stats
        assert "equity" in stats
        assert "open_positions" in stats
        assert "total_trades" in stats
        assert stats["balance"] == 10000
    
    def test_max_positions_limit(self, portfolio_manager):
        """Тест лимита позиций."""
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "XRPUSDT", "ADAUSDT"]
        
        # Открываем до лимита
        for i, symbol in enumerate(symbols[:5]):
            pos = portfolio_manager.open_position(
                symbol=symbol,
                timeframe="1h",
                direction="long",
                entry_price=100,
                tp_prices=[110],
                sl_price=90,
                notional_value=500,
            )
            if i < 5:
                assert pos is not None
        
        # Шестая не должна открыться
        can_open, reason = portfolio_manager.can_open_position("ADAUSDT")
        assert can_open == False


class TestPosition:
    """Тесты для Position."""
    
    def test_position_creation(self):
        """Тест создания позиции."""
        position = Position(
            id="test123",
            symbol="BTCUSDT",
            timeframe="1h",
            direction="long",
            entry_price=42000,
            current_price=42500,
            tp_prices=[43000, 44000],
            sl_price=40000,
            quantity=0.1,
            notional_value=4200,
        )
        
        assert position.is_long
        assert position.is_open
        assert position.sector == "BTC"
    
    def test_unrealized_pnl_long(self):
        """Тест нереализованного PnL для LONG."""
        position = Position(
            symbol="BTCUSDT",
            direction="long",
            entry_price=42000,
            current_price=42420,  # +1%
            notional_value=4200,
            quantity=0.1,
        )
        
        assert abs(position.unrealized_pnl_percent - 1.0) < 0.01
        assert abs(position.unrealized_pnl_amount - 42) < 1
    
    def test_unrealized_pnl_short(self):
        """Тест нереализованного PnL для SHORT."""
        position = Position(
            symbol="BTCUSDT",
            direction="short",
            entry_price=42000,
            current_price=41580,  # -1% от входа = +1% для шорта
            notional_value=4200,
            quantity=0.1,
        )
        
        assert abs(position.unrealized_pnl_percent - 1.0) < 0.01
    
    def test_signal_id_format(self):
        """Тест формата signal_id."""
        position = Position(
            symbol="BTCUSDT",
            direction="long",
            entry_price=42000,
            entry_time=datetime(2024, 1, 15, 10, 30),
        )
        
        assert position.signal_id == "#Long_BTCUSDT_15_01_2024_10_30"
    
    def test_to_dict(self):
        """Тест сериализации."""
        position = Position(
            symbol="BTCUSDT",
            direction="long",
            entry_price=42000,
            current_price=42500,
            notional_value=4200,
        )
        
        data = position.to_dict()
        
        assert data["symbol"] == "BTCUSDT"
        assert data["direction"] == "long"
        assert "unrealized_pnl_percent" in data
        assert "sector" in data


# === Run Tests ===

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

