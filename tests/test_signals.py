"""
Тесты для модуля signals.

Покрытие:
- Signal создание
- FilterConfig
- SignalGenerator генерация
- Проверка фильтров
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.velas_indicator import VelasPreset, VELAS_PRESETS_60
from backend.core.signals import (
    Signal,
    SignalType,
    SignalStrength,
    FilterConfig,
    SignalGenerator,
)


# === Fixtures ===

@pytest.fixture
def sample_df():
    """Создать тестовый DataFrame."""
    np.random.seed(42)
    n = 200
    
    base_price = 50000
    returns = np.random.randn(n) * 0.02
    close = base_price * np.cumprod(1 + returns)
    
    data = {
        "timestamp": [datetime(2024, 1, 1) + timedelta(hours=i) for i in range(n)],
        "open": close * (1 + np.random.randn(n) * 0.001),
        "high": close * (1 + abs(np.random.randn(n)) * 0.01),
        "low": close * (1 - abs(np.random.randn(n)) * 0.01),
        "close": close,
        "volume": np.random.randint(100, 10000, n),
    }
    
    df = pd.DataFrame(data)
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    
    return df


@pytest.fixture
def default_preset():
    """Пресет по умолчанию."""
    return VELAS_PRESETS_60[0]


@pytest.fixture
def default_generator(default_preset):
    """Генератор сигналов по умолчанию."""
    return SignalGenerator(
        preset=default_preset,
        symbol="BTCUSDT",
        timeframe="1h",
    )


# === Tests: Signal ===

class TestSignal:
    """Тесты класса Signal."""
    
    def test_create_long_signal(self):
        """Создание LONG сигнала."""
        signal = Signal(
            timestamp=datetime(2024, 1, 1, 12, 0),
            symbol="BTCUSDT",
            timeframe="1h",
            signal_type=SignalType.LONG,
            entry_price=50000.0,
        )
        
        assert signal.is_long
        assert not signal.is_short
        assert signal.is_confirmed
    
    def test_create_short_signal(self):
        """Создание SHORT сигнала."""
        signal = Signal(
            timestamp=datetime(2024, 1, 1, 12, 0),
            symbol="BTCUSDT",
            timeframe="1h",
            signal_type=SignalType.SHORT,
            entry_price=50000.0,
        )
        
        assert signal.is_short
        assert not signal.is_long
        assert signal.is_confirmed
    
    def test_prepare_signal_not_confirmed(self):
        """PREPARE сигнал не подтверждён."""
        signal = Signal(
            timestamp=datetime(2024, 1, 1, 12, 0),
            symbol="BTCUSDT",
            timeframe="1h",
            signal_type=SignalType.PREPARE_LONG,
            entry_price=50000.0,
        )
        
        assert signal.is_long
        assert not signal.is_confirmed
    
    def test_signal_id_format(self):
        """Формат ID сигнала."""
        signal = Signal(
            timestamp=datetime(2024, 1, 15, 14, 30),
            symbol="ETHUSDT",
            timeframe="30m",
            signal_type=SignalType.LONG,
            entry_price=2500.0,
        )
        
        assert signal.signal_id == "#Long_ETHUSDT_15_01_2024_14_30"
    
    def test_signal_to_dict(self):
        """Конвертация сигнала в словарь."""
        signal = Signal(
            timestamp=datetime(2024, 1, 1, 12, 0),
            symbol="BTCUSDT",
            timeframe="1h",
            signal_type=SignalType.LONG,
            entry_price=50000.0,
            tp_levels=[50500, 51000, 51500],
            sl_level=49000,
        )
        
        d = signal.to_dict()
        
        assert d["symbol"] == "BTCUSDT"
        assert d["signal_type"] == "long"
        assert d["entry_price"] == 50000.0
        assert len(d["tp_levels"]) == 3


# === Tests: FilterConfig ===

class TestFilterConfig:
    """Тесты конфигурации фильтров."""
    
    def test_default_config(self):
        """Конфигурация по умолчанию."""
        config = FilterConfig()
        
        assert not config.use_volume_filter
        assert not config.use_rsi_filter
        assert not config.use_adx_filter
        assert not config.use_session_filter
        assert not config.use_adaptive_filters
    
    def test_volume_filter_config(self):
        """Конфигурация volume фильтра."""
        config = FilterConfig(
            use_volume_filter=True,
            volume_multiplier=1.5,
            volume_period=30,
        )
        
        assert config.use_volume_filter
        assert config.volume_multiplier == 1.5
        assert config.volume_period == 30
    
    def test_rsi_filter_config(self):
        """Конфигурация RSI фильтра."""
        config = FilterConfig(
            use_rsi_filter=True,
            rsi_period=20,
            rsi_long_level=55,
            rsi_short_level=45,
        )
        
        assert config.use_rsi_filter
        assert config.rsi_period == 20
        assert config.rsi_long_level == 55
        assert config.rsi_short_level == 45
    
    def test_adaptive_filters_config(self):
        """Конфигурация адаптивных фильтров."""
        config = FilterConfig(
            use_adaptive_filters=True,
            adaptive_vol_coeff=0.7,
            adaptive_rsi_coeff=15.0,
        )
        
        assert config.use_adaptive_filters
        assert config.adaptive_vol_coeff == 0.7
        assert config.adaptive_rsi_coeff == 15.0


# === Tests: SignalGenerator ===

class TestSignalGenerator:
    """Тесты генератора сигналов."""
    
    def test_create_generator(self, default_preset):
        """Создание генератора."""
        generator = SignalGenerator(
            preset=default_preset,
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        assert generator.symbol == "BTCUSDT"
        assert generator.timeframe == "1h"
        assert generator.preset == default_preset
    
    def test_generate_signals(self, sample_df, default_generator):
        """Генерация сигналов."""
        signals = default_generator.generate(sample_df)
        
        assert isinstance(signals, list)
        # Может быть 0 сигналов в зависимости от данных
        for signal in signals:
            assert isinstance(signal, Signal)
            assert signal.symbol == "BTCUSDT"
            assert signal.timeframe == "1h"
    
    def test_generate_single(self, sample_df, default_generator):
        """Генерация одного сигнала."""
        signal = default_generator.generate_single(sample_df)
        
        # Может быть None если нет сигнала на последнем баре
        if signal is not None:
            assert isinstance(signal, Signal)
    
    def test_calculate_rsi(self, sample_df, default_generator):
        """Расчёт RSI."""
        rsi = default_generator.calculate_rsi(sample_df["close"], 14)
        
        assert len(rsi) == len(sample_df)
        # RSI должен быть в диапазоне 0-100
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
    
    def test_calculate_adx(self, sample_df, default_generator):
        """Расчёт ADX."""
        adx = default_generator.calculate_adx(sample_df, 14)
        
        assert len(adx) == len(sample_df)
        # ADX должен быть положительным
        valid_adx = adx.dropna()
        assert (valid_adx >= 0).all()
    
    def test_check_filters_all_disabled(self, sample_df, default_generator):
        """Проверка фильтров когда все отключены."""
        # Сначала рассчитаем индикатор
        calc_df = default_generator.indicator.calculate(sample_df)
        
        filters = default_generator.check_filters(calc_df, idx=50, is_long=True)
        
        # Все должны быть True (пропущены)
        assert all(filters.values())
    
    def test_check_filters_volume(self, sample_df, default_preset):
        """Проверка volume фильтра."""
        config = FilterConfig(
            use_volume_filter=True,
            volume_multiplier=1.0,  # Низкий порог
        )
        
        generator = SignalGenerator(
            preset=default_preset,
            filter_config=config,
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        calc_df = generator.indicator.calculate(sample_df)
        filters = generator.check_filters(calc_df, idx=50, is_long=True)
        
        assert "volume" in filters
    
    def test_all_filters_passed(self, default_generator):
        """Проверка all_filters_passed."""
        assert default_generator.all_filters_passed({"a": True, "b": True})
        assert not default_generator.all_filters_passed({"a": True, "b": False})
        assert not default_generator.all_filters_passed({"a": False, "b": False})
    
    def test_signals_have_entry_price(self, sample_df, default_generator):
        """Сигналы содержат цену входа."""
        signals = default_generator.generate(sample_df)
        
        for signal in signals:
            assert signal.entry_price > 0
    
    def test_signals_have_indicator_data(self, sample_df, default_generator):
        """Сигналы содержат данные индикатора."""
        signals = default_generator.generate(sample_df)
        
        for signal in signals:
            assert signal.high_channel > 0
            assert signal.low_channel > 0
            assert signal.mid_channel > 0


# === Tests: Filters ===

class TestFilters:
    """Тесты фильтров сигналов."""
    
    def test_rsi_filter(self, sample_df, default_preset):
        """RSI фильтр."""
        config = FilterConfig(
            use_rsi_filter=True,
            rsi_period=14,
            rsi_long_level=50,
            rsi_short_level=50,
        )
        
        generator = SignalGenerator(
            preset=default_preset,
            filter_config=config,
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        signals = generator.generate(sample_df)
        
        # Все сигналы должны проходить RSI фильтр
        for signal in signals:
            assert signal.filters_passed.get("rsi", True)
    
    def test_adx_filter(self, sample_df, default_preset):
        """ADX фильтр."""
        config = FilterConfig(
            use_adx_filter=True,
            adx_period=14,
            adx_level=20,
        )
        
        generator = SignalGenerator(
            preset=default_preset,
            filter_config=config,
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        signals = generator.generate(sample_df)
        
        for signal in signals:
            assert signal.filters_passed.get("adx", True)
    
    def test_combined_filters(self, sample_df, default_preset):
        """Комбинированные фильтры."""
        config = FilterConfig(
            use_volume_filter=True,
            volume_multiplier=0.5,
            use_rsi_filter=True,
            rsi_long_level=40,
            rsi_short_level=60,
        )
        
        generator = SignalGenerator(
            preset=default_preset,
            filter_config=config,
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        signals = generator.generate(sample_df)
        
        # Все фильтры должны быть пройдены
        for signal in signals:
            assert signal.filters_passed.get("volume", True)
            assert signal.filters_passed.get("rsi", True)


# === Tests: Edge Cases ===

class TestSignalEdgeCases:
    """Тесты граничных случаев."""
    
    def test_empty_dataframe(self, default_preset):
        """Пустой DataFrame."""
        generator = SignalGenerator(
            preset=default_preset,
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        df = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        
        # Должно вернуть пустой список
        signals = generator.generate(df)
        assert signals == []
    
    def test_small_dataframe(self, default_preset):
        """Маленький DataFrame (меньше периода индикатора)."""
        generator = SignalGenerator(
            preset=default_preset,
            symbol="BTCUSDT",
            timeframe="1h",
        )
        
        df = pd.DataFrame({
            "timestamp": [datetime(2024, 1, 1) + timedelta(hours=i) for i in range(10)],
            "open": [50000] * 10,
            "high": [50100] * 10,
            "low": [49900] * 10,
            "close": [50000] * 10,
            "volume": [1000] * 10,
        })
        
        # Должно вернуть пустой список (недостаточно данных)
        signals = generator.generate(df)
        assert signals == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
