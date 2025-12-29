"""
Pytest configuration for VELAS tests.
"""

import sys
from pathlib import Path

import pytest

# Добавляем корень проекта в путь
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def project_root():
    """Корневая директория проекта."""
    return PROJECT_ROOT


@pytest.fixture
def sample_ohlcv_data():
    """Создать тестовые OHLCV данные."""
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    dates = pd.date_range(
        start=datetime(2024, 1, 1),
        periods=200,
        freq="1h",
    )
    
    # Генерируем реалистичные данные
    base_price = 42000
    returns = np.random.randn(200) * 0.01
    prices = base_price * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        "timestamp": dates,
        "open": prices * (1 - np.abs(np.random.randn(200) * 0.001)),
        "high": prices * (1 + np.abs(np.random.randn(200) * 0.005)),
        "low": prices * (1 - np.abs(np.random.randn(200) * 0.005)),
        "close": prices,
        "volume": np.random.uniform(100, 1000, 200),
    })
    
    return df
