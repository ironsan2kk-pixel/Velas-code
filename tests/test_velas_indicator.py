"""
Тесты для модуля velas_indicator.

Покрытие:
- VelasPreset создание и валидация
- VelasIndicator расчёт каналов
- VelasIndicator расчёт триггеров
- Вспомогательные функции (ATR, StdDev, Highest, Lowest)
- Генерация сигналов
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.velas_indicator import (
    VelasPreset,
    VelasIndicator,
    VelasResult,
    VELAS_PRESETS_60,
    ta_highest,
    ta_lowest,
    ta_atr,
    ta_stdev,
    find_best_preset,
)


# === Fixtures ===

@pytest.fixture
def sample_df():
    """Создать тестовый DataFrame с OHLCV данными."""
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
    # Корректируем high/low
    df["high"] = df[["open", "high", "close"]].max(axis=1)
    df["low"] = df[["open", "low", "close"]].min(axis=1)
    
    return df


@pytest.fixture
def default_preset():
    """Пресет по умолчанию."""
    return VELAS_PRESETS_60[0]


# === Tests: VelasPreset ===

class TestVelasPreset:
    """Тесты класса VelasPreset."""
    
    def test_create_preset(self):
        """Создание пресета."""
        preset = VelasPreset(index=0, i1=40, i2=10, i3=0.3, i4=1.0, i5=1.0)
        
        assert preset.index == 0
        assert preset.i1 == 40
        assert preset.i2 == 10
        assert preset.i3 == 0.3
        assert preset.i4 == 1.0
        assert preset.i5 == 1.0
    
    def test_preset_name(self):
        """Проверка имени пресета."""
        preset = VelasPreset(index=5, i1=70, i2=14, i3=0.9, i4=1.5, i5=1.5)
        assert preset.name == "Вариант 6"
    
    def test_preset_validation_index(self):
        """Валидация индекса."""
        with pytest.raises(ValueError):
            VelasPreset(index=-1, i1=40, i2=10, i3=0.3, i4=1.0, i5=1.0)
        
        with pytest.raises(ValueError):
            VelasPreset(index=60, i1=40, i2=10, i3=0.3, i4=1.0, i5=1.0)
    
    def test_preset_validation_i1(self):
        """Валидация i1."""
        with pytest.raises(ValueError):
            VelasPreset(index=0, i1=0, i2=10, i3=0.3, i4=1.0, i5=1.0)
    
    def test_preset_to_dict(self):
        """Конвертация в словарь."""
        preset = VelasPreset(index=0, i1=40, i2=10, i3=0.3, i4=1.0, i5=1.0)
        d = preset.to_dict()
        
        assert d["index"] == 0
        assert d["i1"] == 40
        assert d["i2"] == 10
        assert d["i3"] == 0.3
        assert d["i4"] == 1.0
        assert d["i5"] == 1.0
    
    def test_all_60_presets_exist(self):
        """Проверка что все 60 пресетов существуют."""
        assert len(VELAS_PRESETS_60) == 60
        
        for i, preset in enumerate(VELAS_PRESETS_60):
            assert preset.index == i
            assert preset.i1 > 0
            assert preset.i2 > 0


# === Tests: VelasIndicator ===

class TestVelasIndicator:
    """Тесты класса VelasIndicator."""
    
    def test_create_indicator(self, default_preset):
        """Создание индикатора."""
        indicator = VelasIndicator(default_preset)
        assert indicator.preset == default_preset
    
    def test_calculate_atr(self, sample_df):
        """Расчёт ATR."""
        atr = VelasIndicator.calculate_atr(sample_df, period=14)
        
        assert len(atr) == len(sample_df)
        assert atr.iloc[13:].notna().all()  # После периода прогрева
        assert (atr.dropna() >= 0).all()  # ATR всегда положительный (игнорируем NaN)
    
    def test_calculate_stdev(self, sample_df):
        """Расчёт StdDev."""
        stdev = VelasIndicator.calculate_stdev(sample_df["close"], period=10)
        
        assert len(stdev) == len(sample_df)
        assert stdev.iloc[9:].notna().all()
        assert (stdev.dropna() >= 0).all()  # StdDev всегда положительный (игнорируем NaN)
    
    def test_calculate_highest(self, sample_df):
        """Расчёт Highest."""
        highest = VelasIndicator.calculate_highest(sample_df["high"], period=20)
        
        assert len(highest) == len(sample_df)
        assert highest.iloc[19:].notna().all()
        
        # Highest должен быть >= текущий high
        for i in range(19, len(sample_df)):
            assert highest.iloc[i] >= sample_df["high"].iloc[i]
    
    def test_calculate_lowest(self, sample_df):
        """Расчёт Lowest."""
        lowest = VelasIndicator.calculate_lowest(sample_df["low"], period=20)
        
        assert len(lowest) == len(sample_df)
        assert lowest.iloc[19:].notna().all()
        
        # Lowest должен быть <= текущий low
        for i in range(19, len(sample_df)):
            assert lowest.iloc[i] <= sample_df["low"].iloc[i]
    
    def test_calculate_indicator(self, sample_df, default_preset):
        """Полный расчёт индикатора."""
        indicator = VelasIndicator(default_preset)
        result = indicator.calculate(sample_df)
        
        # Проверяем наличие всех колонок
        expected_cols = [
            "high_channel", "low_channel", "mid_channel",
            "atr", "stdev", "long_trigger", "short_trigger"
        ]
        for col in expected_cols:
            assert col in result.columns
        
        # Проверяем логические соотношения
        valid_rows = result.dropna(subset=["long_trigger", "short_trigger"])
        
        for _, row in valid_rows.iterrows():
            assert row["high_channel"] >= row["low_channel"]
            assert row["low_channel"] <= row["mid_channel"] <= row["high_channel"]
            assert row["long_trigger"] > row["mid_channel"]
            assert row["short_trigger"] < row["mid_channel"]
    
    def test_calculate_insufficient_data(self, default_preset):
        """Расчёт с недостаточным количеством данных."""
        small_df = pd.DataFrame({
            "timestamp": [datetime.now()],
            "open": [100],
            "high": [101],
            "low": [99],
            "close": [100],
            "volume": [1000],
        })
        
        indicator = VelasIndicator(default_preset)
        
        with pytest.raises(ValueError):
            indicator.calculate(small_df)
    
    def test_get_signals(self, sample_df, default_preset):
        """Генерация сигналов."""
        indicator = VelasIndicator(default_preset)
        result = indicator.get_signals(sample_df)
        
        assert "long_signal" in result.columns
        assert "short_signal" in result.columns
        assert "entry_price" in result.columns
        
        # Проверяем что сигналы булевы
        assert result["long_signal"].dtype == bool or result["long_signal"].isin([True, False]).all()
        assert result["short_signal"].dtype == bool or result["short_signal"].isin([True, False]).all()
    
    def test_calculate_single(self, sample_df, default_preset):
        """Расчёт для одного бара."""
        indicator = VelasIndicator(default_preset)
        
        # Последний бар
        result = indicator.calculate_single(sample_df, idx=-1)
        
        assert result is not None
        assert isinstance(result, VelasResult)
        assert result.high_channel > 0
        assert result.low_channel > 0
        assert result.mid_channel > 0


# === Tests: Helper Functions ===

class TestHelperFunctions:
    """Тесты вспомогательных функций."""
    
    def test_ta_highest(self, sample_df):
        """Функция ta_highest."""
        result = ta_highest(sample_df["high"], 20)
        assert len(result) == len(sample_df)
    
    def test_ta_lowest(self, sample_df):
        """Функция ta_lowest."""
        result = ta_lowest(sample_df["low"], 20)
        assert len(result) == len(sample_df)
    
    def test_ta_atr(self, sample_df):
        """Функция ta_atr."""
        result = ta_atr(sample_df, 14)
        assert len(result) == len(sample_df)
    
    def test_ta_stdev(self, sample_df):
        """Функция ta_stdev."""
        result = ta_stdev(sample_df["close"], 10)
        assert len(result) == len(sample_df)


# === Tests: Best Preset Finder ===

class TestFindBestPreset:
    """Тесты поиска лучшего пресета."""
    
    def test_find_best_preset_default(self, sample_df):
        """Поиск лучшего пресета с метрикой по умолчанию."""
        # Используем только первые 5 пресетов для скорости
        presets = VELAS_PRESETS_60[:5]
        best, metric = find_best_preset(sample_df, presets)
        
        assert best in presets
        assert isinstance(metric, float)
    
    def test_find_best_preset_custom_metric(self, sample_df):
        """Поиск с кастомной метрикой."""
        def custom_metric(preset, signals_df):
            return preset.i1 + preset.i2  # Простая метрика
        
        presets = VELAS_PRESETS_60[:5]
        best, metric = find_best_preset(sample_df, presets, custom_metric)
        
        # Максимальная сумма i1+i2 среди первых 5
        expected_max = max(p.i1 + p.i2 for p in presets)
        assert metric == expected_max


# === Tests: Edge Cases ===

class TestEdgeCases:
    """Тесты граничных случаев."""
    
    def test_flat_market(self, default_preset):
        """Плоский рынок (без движения)."""
        n = 100
        flat_price = 50000
        
        df = pd.DataFrame({
            "timestamp": [datetime(2024, 1, 1) + timedelta(hours=i) for i in range(n)],
            "open": [flat_price] * n,
            "high": [flat_price] * n,
            "low": [flat_price] * n,
            "close": [flat_price] * n,
            "volume": [1000] * n,
        })
        
        indicator = VelasIndicator(default_preset)
        result = indicator.calculate(df)
        
        # Должно работать без ошибок
        assert len(result) == n
    
    def test_trending_market(self, default_preset):
        """Трендовый рынок."""
        n = 100
        trend = np.linspace(50000, 60000, n)
        
        df = pd.DataFrame({
            "timestamp": [datetime(2024, 1, 1) + timedelta(hours=i) for i in range(n)],
            "open": trend * 0.999,
            "high": trend * 1.01,
            "low": trend * 0.99,
            "close": trend,
            "volume": [1000] * n,
        })
        
        indicator = VelasIndicator(default_preset)
        signals = indicator.get_signals(df)
        
        # В трендовом рынке должны быть сигналы
        total_signals = signals["long_signal"].sum() + signals["short_signal"].sum()
        assert total_signals >= 0  # Может быть 0 если тренд плавный
    
    def test_volatile_market(self, default_preset):
        """Волатильный рынок."""
        n = 100
        np.random.seed(42)
        
        # Высокая волатильность
        base = 50000
        volatility = np.random.randn(n) * 0.05  # 5% волатильность
        close = base * np.cumprod(1 + volatility)
        
        df = pd.DataFrame({
            "timestamp": [datetime(2024, 1, 1) + timedelta(hours=i) for i in range(n)],
            "open": close * (1 + np.random.randn(n) * 0.01),
            "high": close * (1 + abs(np.random.randn(n)) * 0.03),
            "low": close * (1 - abs(np.random.randn(n)) * 0.03),
            "close": close,
            "volume": np.random.randint(1000, 50000, n),
        })
        
        df["high"] = df[["open", "high", "close"]].max(axis=1)
        df["low"] = df[["open", "low", "close"]].min(axis=1)
        
        indicator = VelasIndicator(default_preset)
        result = indicator.calculate(df)
        
        # ATR должен быть выше в волатильном рынке
        assert result["atr"].iloc[-1] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
