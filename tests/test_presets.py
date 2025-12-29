"""
Тесты для модуля presets.py

pytest tests/test_presets.py -v
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.presets import (
    # Constants
    TRADING_PAIRS,
    TIMEFRAMES,
    VOLATILITY_REGIMES,
    SECTORS,
    get_sector,
    get_preset_count,
    
    # Data classes
    IndicatorParams,
    TPLevels,
    TPDistribution,
    OptimizationMeta,
    TradingPreset,
    
    # Managers
    PresetManager,
    PresetGenerator,
    
    # Defaults
    DEFAULT_TP_LEVELS,
    DEFAULT_SL_PERCENT,
    DEFAULT_INDICATOR_PARAMS,
    
    # Functions
    create_default_presets,
    load_preset,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_dir():
    """Создать временную директорию."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


@pytest.fixture
def sample_preset():
    """Создать тестовый пресет."""
    return TradingPreset(
        symbol="BTCUSDT",
        timeframe="1h",
        volatility_regime="normal",
    )


# ============================================================================
# CONSTANTS TESTS
# ============================================================================

class TestConstants:
    """Тесты констант."""
    
    def test_trading_pairs_count(self):
        """Тест количества торговых пар."""
        assert len(TRADING_PAIRS) == 20
    
    def test_trading_pairs_format(self):
        """Тест формата торговых пар."""
        for pair in TRADING_PAIRS:
            assert pair.endswith("USDT")
            assert len(pair) >= 6
    
    def test_timeframes(self):
        """Тест таймфреймов."""
        assert TIMEFRAMES == ["30m", "1h", "2h"]
    
    def test_volatility_regimes(self):
        """Тест режимов волатильности."""
        assert VOLATILITY_REGIMES == ["low", "normal", "high"]
    
    def test_sectors_coverage(self):
        """Тест что все пары покрыты секторами."""
        covered = []
        for pairs in SECTORS.values():
            covered.extend(pairs)
        
        for pair in TRADING_PAIRS:
            assert pair in covered, f"{pair} не в секторах"
    
    def test_get_sector(self):
        """Тест получения сектора."""
        assert get_sector("BTCUSDT") == "BTC"
        assert get_sector("ETHUSDT") == "ETH"
        assert get_sector("SOLUSDT") == "L1"
        assert get_sector("MATICUSDT") == "L2"
        assert get_sector("LINKUSDT") == "DEFI"
        assert get_sector("XRPUSDT") == "OLD"
        assert get_sector("DOGEUSDT") == "MEME"
        assert get_sector("BNBUSDT") == "CEX"
        assert get_sector("UNKNOWN") == "UNKNOWN"
    
    def test_preset_count(self):
        """Тест общего количества пресетов."""
        expected = len(TRADING_PAIRS) * len(TIMEFRAMES) * len(VOLATILITY_REGIMES)
        assert get_preset_count() == expected
        assert get_preset_count() == 180


# ============================================================================
# INDICATOR PARAMS TESTS
# ============================================================================

class TestIndicatorParams:
    """Тесты для IndicatorParams."""
    
    def test_create(self):
        """Тест создания."""
        params = IndicatorParams(i1=40, i2=10, i3=0.5, i4=1.2, i5=1.0)
        
        assert params.i1 == 40
        assert params.i2 == 10
        assert params.i3 == 0.5
        assert params.i4 == 1.2
        assert params.i5 == 1.0
    
    def test_to_dict(self):
        """Тест конвертации в словарь."""
        params = IndicatorParams(i1=40, i2=10, i3=0.5, i4=1.2, i5=1.0)
        d = params.to_dict()
        
        assert d == {"i1": 40, "i2": 10, "i3": 0.5, "i4": 1.2, "i5": 1.0}
    
    def test_from_dict(self):
        """Тест создания из словаря."""
        d = {"i1": 50, "i2": 14, "i3": 1.0, "i4": 1.5, "i5": 1.5}
        params = IndicatorParams.from_dict(d)
        
        assert params.i1 == 50
        assert params.i3 == 1.0


# ============================================================================
# TP LEVELS TESTS
# ============================================================================

class TestTPLevels:
    """Тесты для TPLevels."""
    
    def test_defaults(self):
        """Тест дефолтных значений."""
        tp = TPLevels()
        
        assert tp.tp1 == 1.0
        assert tp.tp2 == 2.0
        assert tp.tp6 == 14.0
    
    def test_to_list(self):
        """Тест конвертации в список."""
        tp = TPLevels()
        lst = tp.to_list()
        
        assert lst == [1.0, 2.0, 3.0, 4.0, 7.5, 14.0]
    
    def test_apply_multiplier(self):
        """Тест применения множителя."""
        tp = TPLevels(tp1=1.0, tp2=2.0, tp3=3.0, tp4=4.0, tp5=5.0, tp6=6.0)
        scaled = tp.apply_multiplier(2.0)
        
        assert scaled.tp1 == 2.0
        assert scaled.tp2 == 4.0
        assert scaled.tp6 == 12.0
    
    def test_from_dict(self):
        """Тест создания из словаря."""
        d = {"tp1": 0.5, "tp2": 1.0, "tp3": 1.5, "tp4": 2.0, "tp5": 3.0, "tp6": 5.0}
        tp = TPLevels.from_dict(d)
        
        assert tp.tp1 == 0.5
        assert tp.tp6 == 5.0


# ============================================================================
# TP DISTRIBUTION TESTS
# ============================================================================

class TestTPDistribution:
    """Тесты для TPDistribution."""
    
    def test_defaults(self):
        """Тест дефолтных значений."""
        dist = TPDistribution()
        
        assert dist.tp1 == 20.0
        assert dist.tp6 == 15.0
    
    def test_normalization(self):
        """Тест нормализации до 100%."""
        dist = TPDistribution(tp1=10, tp2=10, tp3=10, tp4=10, tp5=10, tp6=10)
        
        total = sum(dist.to_list())
        assert abs(total - 100) < 0.01
    
    def test_to_list(self):
        """Тест конвертации в список."""
        dist = TPDistribution()
        lst = dist.to_list()
        
        assert len(lst) == 6
        assert abs(sum(lst) - 100) < 0.01


# ============================================================================
# TRADING PRESET TESTS
# ============================================================================

class TestTradingPreset:
    """Тесты для TradingPreset."""
    
    def test_create_minimal(self):
        """Тест создания с минимальными параметрами."""
        preset = TradingPreset(
            symbol="BTCUSDT",
            timeframe="1h",
            volatility_regime="normal",
        )
        
        assert preset.symbol == "BTCUSDT"
        assert preset.timeframe == "1h"
        assert preset.volatility_regime == "normal"
        assert preset.sector == "BTC"
        assert preset.indicator is not None
        assert preset.tp_levels is not None
        assert preset.tp_distribution is not None
    
    def test_preset_id(self, sample_preset):
        """Тест генерации ID."""
        assert sample_preset.preset_id == "BTCUSDT_1h_normal"
    
    def test_filename(self, sample_preset):
        """Тест генерации имени файла."""
        assert sample_preset.filename == "BTCUSDT_1h_normal.yaml"
    
    def test_to_dict(self, sample_preset):
        """Тест конвертации в словарь."""
        d = sample_preset.to_dict()
        
        assert "symbol" in d
        assert "timeframe" in d
        assert "volatility_regime" in d
        assert "indicator" in d
        assert "tp_levels" in d
        assert "sl_percent" in d
        assert "tp_distribution" in d
        assert "optimization" in d
    
    def test_from_dict(self, sample_preset):
        """Тест создания из словаря."""
        d = sample_preset.to_dict()
        restored = TradingPreset.from_dict(d)
        
        assert restored.symbol == sample_preset.symbol
        assert restored.timeframe == sample_preset.timeframe
        assert restored.volatility_regime == sample_preset.volatility_regime
        assert restored.indicator.i1 == sample_preset.indicator.i1
    
    def test_to_yaml(self, sample_preset):
        """Тест конвертации в YAML."""
        yaml_str = sample_preset.to_yaml()
        
        assert isinstance(yaml_str, str)
        assert "symbol: BTCUSDT" in yaml_str
        assert "timeframe: 1h" in yaml_str
        
        # Должен быть валидным YAML
        data = yaml.safe_load(yaml_str)
        assert data["symbol"] == "BTCUSDT"


# ============================================================================
# PRESET MANAGER TESTS
# ============================================================================

class TestPresetManager:
    """Тесты для PresetManager."""
    
    def test_init(self, temp_dir):
        """Тест инициализации."""
        manager = PresetManager(temp_dir)
        
        assert manager.presets_dir == Path(temp_dir)
    
    def test_save_and_load(self, temp_dir, sample_preset):
        """Тест сохранения и загрузки."""
        manager = PresetManager(temp_dir)
        
        # Сохраняем
        manager.save(sample_preset)
        
        # Проверяем файл
        filepath = Path(temp_dir) / "BTCUSDT_1h_normal.yaml"
        assert filepath.exists()
        
        # Загружаем
        manager.clear_cache()
        loaded = manager.load("BTCUSDT_1h_normal")
        
        assert loaded is not None
        assert loaded.symbol == "BTCUSDT"
        assert loaded.timeframe == "1h"
    
    def test_load_nonexistent(self, temp_dir):
        """Тест загрузки несуществующего пресета."""
        manager = PresetManager(temp_dir)
        
        preset = manager.load("nonexistent")
        assert preset is None
    
    def test_get(self, temp_dir, sample_preset):
        """Тест получения пресета по параметрам."""
        manager = PresetManager(temp_dir)
        manager.save(sample_preset)
        
        loaded = manager.get("BTCUSDT", "1h", "normal")
        
        assert loaded is not None
        assert loaded.symbol == "BTCUSDT"
    
    def test_list_all(self, temp_dir):
        """Тест списка всех пресетов."""
        manager = PresetManager(temp_dir)
        
        # Создаём несколько пресетов
        for regime in VOLATILITY_REGIMES:
            preset = TradingPreset(symbol="BTCUSDT", timeframe="1h", volatility_regime=regime)
            manager.save(preset)
        
        all_presets = manager.list_all()
        
        assert len(all_presets) == 3
        assert "BTCUSDT_1h_normal" in all_presets
    
    def test_load_all(self, temp_dir):
        """Тест загрузки всех пресетов."""
        manager = PresetManager(temp_dir)
        
        # Создаём пресеты
        for tf in TIMEFRAMES:
            preset = TradingPreset(symbol="ETHUSDT", timeframe=tf, volatility_regime="normal")
            manager.save(preset)
        
        all_presets = manager.load_all()
        
        assert len(all_presets) == 3
        assert all(p.symbol == "ETHUSDT" for p in all_presets)
    
    def test_get_by_symbol(self, temp_dir):
        """Тест фильтрации по символу."""
        manager = PresetManager(temp_dir)
        
        # Создаём пресеты для разных символов
        for symbol in ["BTCUSDT", "ETHUSDT", "ETHUSDT"]:
            preset = TradingPreset(symbol=symbol, timeframe="1h", volatility_regime="normal")
            # Меняем regime чтобы были разные ID
            if symbol == "ETHUSDT":
                preset.volatility_regime = "high" if len(manager.list_all()) > 1 else "normal"
            manager.save(preset)
        
        eth_presets = manager.get_by_symbol("ETHUSDT")
        
        assert len(eth_presets) == 2
        assert all(p.symbol == "ETHUSDT" for p in eth_presets)
    
    def test_cache(self, temp_dir, sample_preset):
        """Тест кеширования."""
        manager = PresetManager(temp_dir)
        manager.save(sample_preset)
        
        # Первая загрузка
        loaded1 = manager.load("BTCUSDT_1h_normal")
        
        # Вторая загрузка (должна быть из кеша)
        loaded2 = manager.load("BTCUSDT_1h_normal")
        
        assert loaded1 is loaded2  # Тот же объект
        
        # После очистки кеша - новый объект
        manager.clear_cache()
        loaded3 = manager.load("BTCUSDT_1h_normal")
        
        assert loaded1 is not loaded3


# ============================================================================
# PRESET GENERATOR TESTS
# ============================================================================

class TestPresetGenerator:
    """Тесты для PresetGenerator."""
    
    def test_init(self, temp_dir):
        """Тест инициализации."""
        generator = PresetGenerator(temp_dir)
        
        assert generator.output_dir == Path(temp_dir)
    
    def test_generate_preset(self, temp_dir):
        """Тест генерации одного пресета."""
        generator = PresetGenerator(temp_dir)
        
        preset = generator.generate_preset("BTCUSDT", "1h", "normal")
        
        assert preset.symbol == "BTCUSDT"
        assert preset.timeframe == "1h"
        assert preset.volatility_regime == "normal"
        assert preset.sector == "BTC"
        assert preset.is_active is True
    
    def test_generate_preset_low_regime(self, temp_dir):
        """Тест генерации для LOW режима."""
        generator = PresetGenerator(temp_dir)
        
        preset = generator.generate_preset("BTCUSDT", "1h", "low")
        
        # TP уровни должны быть меньше чем normal
        assert preset.tp_levels.tp1 < DEFAULT_TP_LEVELS["normal"].tp1
        assert preset.sl_percent < DEFAULT_SL_PERCENT["normal"]
    
    def test_generate_preset_high_regime(self, temp_dir):
        """Тест генерации для HIGH режима."""
        generator = PresetGenerator(temp_dir)
        
        preset = generator.generate_preset("BTCUSDT", "1h", "high")
        
        # TP уровни должны быть больше чем normal
        assert preset.tp_levels.tp1 > DEFAULT_TP_LEVELS["normal"].tp1
        assert preset.sl_percent > DEFAULT_SL_PERCENT["normal"]
    
    def test_generate_for_symbol(self, temp_dir):
        """Тест генерации для одного символа."""
        generator = PresetGenerator(temp_dir)
        
        presets = generator.generate_for_symbol("BTCUSDT")
        
        # 3 TF × 3 режима = 9 пресетов
        assert len(presets) == 9
        assert all(p.symbol == "BTCUSDT" for p in presets)
        
        # Все комбинации
        tfs = set(p.timeframe for p in presets)
        regimes = set(p.volatility_regime for p in presets)
        
        assert tfs == set(TIMEFRAMES)
        assert regimes == set(VOLATILITY_REGIMES)
    
    def test_generate_all_no_save(self, temp_dir):
        """Тест генерации всех пресетов без сохранения."""
        generator = PresetGenerator(temp_dir)
        
        presets = generator.generate_all(save=False)
        
        assert len(presets) == 180
        
        # Файлы не должны быть созданы
        files = list(Path(temp_dir).glob("*.yaml"))
        assert len(files) == 0
    
    def test_generate_all_with_save(self, temp_dir):
        """Тест генерации всех пресетов с сохранением."""
        generator = PresetGenerator(temp_dir)
        
        presets = generator.generate_all(save=True)
        
        assert len(presets) == 180
        
        # Файлы должны быть созданы
        files = list(Path(temp_dir).glob("*.yaml"))
        assert len(files) == 180
    
    def test_generate_summary(self, temp_dir):
        """Тест генерации сводки."""
        generator = PresetGenerator(temp_dir)
        generator.generate_all(save=True)
        
        summary = generator.generate_summary()
        
        assert summary["total_presets"] == 180
        assert summary["active_presets"] == 180
        assert len(summary["by_symbol"]) == 20
        assert len(summary["by_timeframe"]) == 3
        assert len(summary["by_regime"]) == 3


# ============================================================================
# HELPER FUNCTIONS TESTS
# ============================================================================

class TestHelperFunctions:
    """Тесты вспомогательных функций."""
    
    def test_create_default_presets(self, temp_dir):
        """Тест функции create_default_presets."""
        count = create_default_presets(temp_dir)
        
        assert count == 180
        
        files = list(Path(temp_dir).glob("*.yaml"))
        assert len(files) == 180
    
    def test_load_preset(self, temp_dir):
        """Тест функции load_preset."""
        # Создаём пресеты
        create_default_presets(temp_dir)
        
        # Загружаем
        preset = load_preset(temp_dir, "BTCUSDT", "1h", "normal")
        
        assert preset is not None
        assert preset.symbol == "BTCUSDT"
        assert preset.timeframe == "1h"
        assert preset.volatility_regime == "normal"
    
    def test_load_preset_not_found(self, temp_dir):
        """Тест загрузки несуществующего пресета."""
        preset = load_preset(temp_dir, "BTCUSDT", "1h", "normal")
        
        assert preset is None


# ============================================================================
# DEFAULTS TESTS
# ============================================================================

class TestDefaults:
    """Тесты дефолтных значений."""
    
    def test_default_tp_levels(self):
        """Тест дефолтных TP уровней."""
        assert "low" in DEFAULT_TP_LEVELS
        assert "normal" in DEFAULT_TP_LEVELS
        assert "high" in DEFAULT_TP_LEVELS
        
        # LOW < NORMAL < HIGH
        assert DEFAULT_TP_LEVELS["low"].tp1 < DEFAULT_TP_LEVELS["normal"].tp1
        assert DEFAULT_TP_LEVELS["normal"].tp1 < DEFAULT_TP_LEVELS["high"].tp1
    
    def test_default_sl_percent(self):
        """Тест дефолтных SL."""
        assert DEFAULT_SL_PERCENT["low"] < DEFAULT_SL_PERCENT["normal"]
        assert DEFAULT_SL_PERCENT["normal"] < DEFAULT_SL_PERCENT["high"]
    
    def test_default_indicator_params(self):
        """Тест дефолтных параметров индикатора."""
        # Все секторы должны быть покрыты
        for sector in SECTORS.keys():
            assert sector in DEFAULT_INDICATOR_PARAMS
        
        # Параметры должны быть валидными
        for params in DEFAULT_INDICATOR_PARAMS.values():
            assert params.i1 >= 1
            assert params.i2 >= 1
            assert params.i3 > 0
            assert params.i4 > 0
            assert params.i5 > 0


# ============================================================================
# YAML SERIALIZATION TESTS
# ============================================================================

class TestYamlSerialization:
    """Тесты YAML сериализации."""
    
    def test_roundtrip(self, sample_preset):
        """Тест полного цикла сериализации."""
        # Preset -> YAML -> Dict -> Preset
        yaml_str = sample_preset.to_yaml()
        data = yaml.safe_load(yaml_str)
        restored = TradingPreset.from_dict(data)
        
        assert restored.symbol == sample_preset.symbol
        assert restored.indicator.i1 == sample_preset.indicator.i1
        assert restored.tp_levels.tp1 == sample_preset.tp_levels.tp1
        assert restored.sl_percent == sample_preset.sl_percent
    
    def test_yaml_readability(self, sample_preset):
        """Тест читаемости YAML."""
        yaml_str = sample_preset.to_yaml()
        
        # Не должно быть flow style
        assert "{" not in yaml_str
        assert "}" not in yaml_str
        
        # Должны быть отступы
        assert "  " in yaml_str


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
