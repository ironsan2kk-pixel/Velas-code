"""
Тесты для модуля volatility.py

pytest tests/test_volatility.py -v
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.volatility import (
    VolatilityRegime,
    VolatilityConfig,
    VolatilityResult,
    VolatilityAnalyzer,
    get_volatility_regime,
    analyze_volatility,
    calculate_volatility_stats,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_df():
    """Создать тестовый DataFrame с OHLCV данными."""
    np.random.seed(42)
    n = 200
    
    dates = pd.date_range(start="2024-01-01", periods=n, freq="1H")
    
    # Генерируем случайные цены
    base_price = 50000
    returns = np.random.normal(0, 0.01, n)  # 1% дневная волатильность
    close = base_price * np.cumprod(1 + returns)
    
    # OHLC
    high = close * (1 + np.abs(np.random.normal(0, 0.005, n)))
    low = close * (1 - np.abs(np.random.normal(0, 0.005, n)))
    open_price = np.roll(close, 1)
    open_price[0] = base_price
    
    # Volume
    volume = np.random.uniform(100, 1000, n)
    
    df = pd.DataFrame({
        "timestamp": dates,
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })
    
    df.set_index("timestamp", inplace=True)
    
    return df


@pytest.fixture
def low_volatility_df():
    """DataFrame с низкой волатильностью."""
    np.random.seed(42)
    n = 200
    
    dates = pd.date_range(start="2024-01-01", periods=n, freq="1H")
    
    # Очень маленькие движения
    base_price = 50000
    returns = np.random.normal(0, 0.001, n)  # 0.1% волатильность
    close = base_price * np.cumprod(1 + returns)
    
    high = close * 1.001
    low = close * 0.999
    open_price = np.roll(close, 1)
    open_price[0] = base_price
    
    df = pd.DataFrame({
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.ones(n) * 100,
    }, index=dates)
    
    return df


@pytest.fixture
def high_volatility_df():
    """DataFrame с высокой волатильностью."""
    np.random.seed(42)
    n = 200
    
    dates = pd.date_range(start="2024-01-01", periods=n, freq="1H")
    
    # Большие движения
    base_price = 50000
    returns = np.random.normal(0, 0.05, n)  # 5% волатильность
    close = base_price * np.cumprod(1 + returns)
    
    high = close * (1 + np.abs(np.random.normal(0, 0.03, n)))
    low = close * (1 - np.abs(np.random.normal(0, 0.03, n)))
    open_price = np.roll(close, 1)
    open_price[0] = base_price
    
    df = pd.DataFrame({
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.random.uniform(100, 1000, n),
    }, index=dates)
    
    return df


# ============================================================================
# VOLATILITY REGIME TESTS
# ============================================================================

class TestVolatilityRegime:
    """Тесты для VolatilityRegime."""
    
    def test_from_ratio_low(self):
        """Тест определения LOW режима."""
        assert VolatilityRegime.from_ratio(0.5) == VolatilityRegime.LOW
        assert VolatilityRegime.from_ratio(0.3) == VolatilityRegime.LOW
        assert VolatilityRegime.from_ratio(0.69) == VolatilityRegime.LOW
    
    def test_from_ratio_normal(self):
        """Тест определения NORMAL режима."""
        assert VolatilityRegime.from_ratio(0.7) == VolatilityRegime.NORMAL
        assert VolatilityRegime.from_ratio(1.0) == VolatilityRegime.NORMAL
        assert VolatilityRegime.from_ratio(1.3) == VolatilityRegime.NORMAL
    
    def test_from_ratio_high(self):
        """Тест определения HIGH режима."""
        assert VolatilityRegime.from_ratio(1.31) == VolatilityRegime.HIGH
        assert VolatilityRegime.from_ratio(1.5) == VolatilityRegime.HIGH
        assert VolatilityRegime.from_ratio(2.0) == VolatilityRegime.HIGH
    
    def test_enum_values(self):
        """Тест значений enum."""
        assert VolatilityRegime.LOW.value == "low"
        assert VolatilityRegime.NORMAL.value == "normal"
        assert VolatilityRegime.HIGH.value == "high"


# ============================================================================
# VOLATILITY CONFIG TESTS
# ============================================================================

class TestVolatilityConfig:
    """Тесты для VolatilityConfig."""
    
    def test_default_config(self):
        """Тест дефолтных значений."""
        config = VolatilityConfig()
        
        assert config.atr_period == 14
        assert config.baseline_period == 100
        assert config.low_threshold == 0.7
        assert config.high_threshold == 1.3
    
    def test_get_multipliers_low(self):
        """Тест множителей для LOW режима."""
        config = VolatilityConfig()
        tp_mult, sl_mult = config.get_multipliers(VolatilityRegime.LOW)
        
        assert tp_mult == 0.8
        assert sl_mult == 0.8
    
    def test_get_multipliers_normal(self):
        """Тест множителей для NORMAL режима."""
        config = VolatilityConfig()
        tp_mult, sl_mult = config.get_multipliers(VolatilityRegime.NORMAL)
        
        assert tp_mult == 1.0
        assert sl_mult == 1.0
    
    def test_get_multipliers_high(self):
        """Тест множителей для HIGH режима."""
        config = VolatilityConfig()
        tp_mult, sl_mult = config.get_multipliers(VolatilityRegime.HIGH)
        
        assert tp_mult == 1.3
        assert sl_mult == 1.2


# ============================================================================
# VOLATILITY ANALYZER TESTS
# ============================================================================

class TestVolatilityAnalyzer:
    """Тесты для VolatilityAnalyzer."""
    
    def test_init_with_data(self, sample_df):
        """Тест инициализации с данными."""
        analyzer = VolatilityAnalyzer(sample_df)
        
        assert analyzer.df is not None
        assert len(analyzer.df) == len(sample_df)
    
    def test_init_without_data(self):
        """Тест инициализации без данных."""
        analyzer = VolatilityAnalyzer()
        
        assert analyzer.df is None
        
        with pytest.raises(ValueError):
            analyzer.get_current_atr()
    
    def test_set_data(self, sample_df):
        """Тест установки данных."""
        analyzer = VolatilityAnalyzer()
        analyzer.set_data(sample_df)
        
        assert analyzer.df is not None
        # Теперь должен работать
        atr = analyzer.get_current_atr()
        assert atr > 0
    
    def test_calculate_atr(self, sample_df):
        """Тест расчёта ATR."""
        atr = VolatilityAnalyzer.calculate_atr(sample_df, period=14)
        
        assert isinstance(atr, pd.Series)
        assert len(atr) == len(sample_df)
        
        # Первые 13 значений должны быть NaN
        assert atr.iloc[:13].isna().all()
        
        # Остальные должны быть положительными
        assert (atr.iloc[13:] > 0).all()
    
    def test_get_current_atr(self, sample_df):
        """Тест получения текущего ATR."""
        analyzer = VolatilityAnalyzer(sample_df)
        atr = analyzer.get_current_atr()
        
        assert isinstance(atr, float)
        assert atr > 0
    
    def test_get_average_atr(self, sample_df):
        """Тест получения среднего ATR."""
        analyzer = VolatilityAnalyzer(sample_df)
        avg_atr = analyzer.get_average_atr()
        
        assert isinstance(avg_atr, float)
        assert avg_atr > 0
    
    def test_get_atr_ratio(self, sample_df):
        """Тест получения ATR ratio."""
        analyzer = VolatilityAnalyzer(sample_df)
        ratio = analyzer.get_atr_ratio()
        
        assert isinstance(ratio, float)
        assert ratio > 0
    
    def test_get_regime(self, sample_df):
        """Тест определения режима."""
        analyzer = VolatilityAnalyzer(sample_df)
        regime = analyzer.get_regime()
        
        assert isinstance(regime, VolatilityRegime)
    
    def test_analyze(self, sample_df):
        """Тест полного анализа."""
        analyzer = VolatilityAnalyzer(sample_df)
        result = analyzer.analyze()
        
        assert isinstance(result, VolatilityResult)
        assert result.current_atr > 0
        assert result.average_atr > 0
        assert result.atr_ratio > 0
        assert result.tp_multiplier > 0
        assert result.sl_multiplier > 0
        assert len(result.recommendation) > 0
    
    def test_analyze_to_dict(self, sample_df):
        """Тест конвертации результата в словарь."""
        analyzer = VolatilityAnalyzer(sample_df)
        result = analyzer.analyze()
        d = result.to_dict()
        
        assert "regime" in d
        assert "current_atr" in d
        assert "atr_ratio" in d
        assert "tp_multiplier" in d
    
    def test_get_regime_series(self, sample_df):
        """Тест получения серии режимов."""
        analyzer = VolatilityAnalyzer(sample_df)
        series = analyzer.get_regime_series()
        
        assert isinstance(series, pd.Series)
        assert len(series) == len(sample_df)
        
        # Все значения должны быть VolatilityRegime
        for val in series.dropna().unique():
            assert isinstance(val, VolatilityRegime)


# ============================================================================
# REGIME DETECTION TESTS
# ============================================================================

class TestRegimeDetection:
    """Тесты для определения режимов в разных условиях."""
    
    def test_low_volatility_detection(self, low_volatility_df):
        """Тест обнаружения низкой волатильности."""
        analyzer = VolatilityAnalyzer(low_volatility_df)
        
        # В стабильных данных волатильность должна быть примерно одинаковой
        ratio = analyzer.get_atr_ratio()
        
        # Ratio должен быть близок к 1 (так как волатильность стабильная)
        assert 0.5 < ratio < 1.5
    
    def test_mixed_volatility(self, sample_df):
        """Тест на смешанных данных."""
        analyzer = VolatilityAnalyzer(sample_df)
        
        # Получаем режим
        regime = analyzer.get_regime()
        
        # Должен вернуть какой-то режим
        assert regime in [VolatilityRegime.LOW, VolatilityRegime.NORMAL, VolatilityRegime.HIGH]


# ============================================================================
# HELPER FUNCTIONS TESTS
# ============================================================================

class TestHelperFunctions:
    """Тесты для вспомогательных функций."""
    
    def test_get_volatility_regime(self, sample_df):
        """Тест функции get_volatility_regime."""
        regime = get_volatility_regime(sample_df)
        
        assert isinstance(regime, VolatilityRegime)
    
    def test_analyze_volatility(self, sample_df):
        """Тест функции analyze_volatility."""
        result = analyze_volatility(sample_df)
        
        assert isinstance(result, VolatilityResult)
        assert result.current_atr > 0
    
    def test_calculate_volatility_stats(self, sample_df):
        """Тест функции calculate_volatility_stats."""
        stats = calculate_volatility_stats(sample_df, "BTCUSDT", "1h")
        
        assert stats.symbol == "BTCUSDT"
        assert stats.timeframe == "1h"
        assert isinstance(stats.current_regime, VolatilityRegime)
        assert stats.low_percent >= 0
        assert stats.normal_percent >= 0
        assert stats.high_percent >= 0
        
        # Сумма должна быть ~100%
        total = stats.low_percent + stats.normal_percent + stats.high_percent
        assert 99 < total < 101
    
    def test_stats_to_dict(self, sample_df):
        """Тест конвертации статистики в словарь."""
        stats = calculate_volatility_stats(sample_df, "BTCUSDT", "1h")
        d = stats.to_dict()
        
        assert "symbol" in d
        assert "current_regime" in d
        assert "low_percent" in d


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Тесты граничных случаев."""
    
    def test_minimum_data(self):
        """Тест с минимальным количеством данных."""
        # 100 баров (минимум для baseline)
        n = 100
        dates = pd.date_range(start="2024-01-01", periods=n, freq="1H")
        
        df = pd.DataFrame({
            "open": np.ones(n) * 100,
            "high": np.ones(n) * 101,
            "low": np.ones(n) * 99,
            "close": np.ones(n) * 100,
            "volume": np.ones(n) * 1000,
        }, index=dates)
        
        analyzer = VolatilityAnalyzer(df)
        # Не должно падать
        regime = analyzer.get_regime()
        assert isinstance(regime, VolatilityRegime)
    
    def test_constant_prices(self):
        """Тест с постоянными ценами (нулевая волатильность)."""
        n = 150
        dates = pd.date_range(start="2024-01-01", periods=n, freq="1H")
        
        df = pd.DataFrame({
            "open": np.ones(n) * 100,
            "high": np.ones(n) * 100,
            "low": np.ones(n) * 100,
            "close": np.ones(n) * 100,
            "volume": np.ones(n) * 1000,
        }, index=dates)
        
        analyzer = VolatilityAnalyzer(df)
        
        # ATR будет 0, но не должен падать
        ratio = analyzer.get_atr_ratio()
        # При делении 0/0 возвращается 1.0
        assert ratio == 1.0 or np.isnan(ratio) or ratio >= 0
    
    def test_custom_config(self, sample_df):
        """Тест с кастомной конфигурацией."""
        config = VolatilityConfig(
            atr_period=7,
            baseline_period=50,
            low_threshold=0.5,
            high_threshold=1.5,
        )
        
        analyzer = VolatilityAnalyzer(sample_df, config)
        result = analyzer.analyze()
        
        assert result.current_atr > 0


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
