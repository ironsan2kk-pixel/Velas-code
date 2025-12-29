# VELAS v2 — ЧЕКЛИСТ

**Последнее обновление:** 2024-12-29  
**Текущая фаза:** VELAS-06  
**Прогресс:** 6/12 фаз

---

## ИСТОРИЯ ИЗМЕНЕНИЙ

| Дата | Коммит | Что сделано | Исправления |
|------|--------|-------------|-------------|
| 2024-12-28 | init | Структура проекта, .gitignore | — |
| 2024-12-28 | velas-01 | Core: velas_indicator, signals, tpsl | — |
| 2024-12-28 | velas-02 | Data: binance_rest, binance_ws, storage | 28 тестов |
| 2024-12-29 | velas-03 | Backtest: engine, metrics, trade | 48 тестов |
| 2024-12-29 | velas-04 | Optimizer: optimizer, walk_forward, robustness | — |
| 2024-12-29 | velas-05 | Presets: volatility, presets, generator | — |
| 2024-12-29 | velas-06 | Portfolio: correlation, risk, manager; Live: engine, state | 45+ тестов |

---

## Фаза 1: Инфраструктура [DONE]

### 1.1 Git и структура
- [x] Создать структуру папок
- [x] .gitignore настроен
- [x] README.md написан

### 1.2 Конфигурация
- [x] config.example.yaml
- [x] pairs.yaml (20 пар)

---

## Фаза 2: Data Engine [DONE]

### 2.1 Binance REST API
- [x] backend/data/binance_rest.py
- [x] Публичные эндпоинты (без ключей)
- [x] Загрузка исторических свечей

### 2.2 Binance WebSocket
- [x] backend/data/binance_ws.py
- [x] Стримы klines
- [x] Автопереподключение

### 2.3 Storage
- [x] backend/data/storage.py
- [x] Parquet формат
- [x] Инкрементальное обновление

---

## Фаза 3: Velas Core + Backtest [DONE]

### 3.1 Индикатор Velas
- [x] backend/core/velas_indicator.py
- [x] 60 пресетов i1-i5
- [x] Расчёт каналов и триггеров

### 3.2 Сигналы
- [x] backend/core/signals.py
- [x] LONG/SHORT генерация
- [x] Фильтры (Volume, RSI, ADX)

### 3.3 TP/SL
- [x] backend/core/tpsl.py
- [x] 6 уровней TP
- [x] Каскадный стоп / БУ

### 3.4 Backtest Engine
- [x] backend/backtest/engine.py
- [x] Симуляция сделок
- [x] Equity curve

### 3.5 Метрики
- [x] backend/backtest/metrics.py
- [x] Sharpe, PF, DD, WinRate

### 3.6 Trades
- [x] backend/backtest/trade.py
- [x] Модель сделки
- [x] Частичное закрытие

---

## Фаза 4: Optimizer [DONE]

### 4.1 Grid Search
- [x] backend/backtest/optimizer.py
- [x] Поиск по 60 пресетам
- [x] Composite score

### 4.2 Walk-Forward
- [x] backend/backtest/walk_forward.py
- [x] 6mo train / 2mo test
- [x] Проверка стабильности

### 4.3 Robustness
- [x] backend/backtest/robustness.py
- [x] Проверка соседних параметров ±15%
- [x] Отклонение хрупких результатов

### 4.4 Тесты
- [x] tests/test_optimizer.py
- [x] Запуск на сервере

---

## Фаза 5: Filters & Presets [DONE]

### 5.1 Volatility Analyzer
- [x] backend/core/volatility.py
- [x] ATR Ratio расчёт
- [x] 3 режима (low/normal/high)
- [x] Автоопределение режима
- [x] Множители TP/SL для режимов

### 5.2 Presets Manager
- [x] backend/core/presets.py
- [x] TradingPreset dataclass
- [x] PresetManager (загрузка/сохранение)
- [x] PresetGenerator (генерация 180 пресетов)
- [x] YAML формат

### 5.3 Constants
- [x] 20 торговых пар
- [x] 3 таймфрейма (30m, 1h, 2h)
- [x] 3 режима волатильности
- [x] Секторы для диверсификации

### 5.4 Scripts
- [x] scripts/generate_presets.py
- [x] CLI с опциями (--symbol, --dry-run, --summary)

### 5.5 Тесты
- [x] tests/test_volatility.py
- [x] tests/test_presets.py
- [x] run_tests.bat / run_tests.sh

---

## Фаза 6: Portfolio & Live Engine [DONE]

### 6.1 Portfolio Module
- [x] backend/portfolio/correlation.py (CorrelationCalculator, SectorFilter)
- [x] backend/portfolio/risk.py (PositionSizer, PortfolioHeatTracker)
- [x] backend/portfolio/manager.py (PortfolioManager, Position)
- [x] Секторная диверсификация (8 секторов)
- [x] Корреляционный фильтр (threshold 0.7)
- [x] Portfolio Heat tracking (max 8%)
- [x] Position sizing (Fixed % Risk, Volatility Adjusted, Kelly)

### 6.2 Live Engine
- [x] backend/live/engine.py (LiveEngine, EngineConfig)
- [x] backend/live/position_tracker.py (PositionTracker, TrackingEvent)
- [x] backend/live/signal_manager.py (SignalManager, EnrichedSignal)

### 6.3 State Management
- [x] backend/live/state.py (StateManager, SQLite)
- [x] Персистентное состояние позиций
- [x] История сигналов и сделок
- [x] Восстановление после рестарта

### 6.4 Тесты
- [x] tests/test_portfolio.py (25+ тестов)
- [x] tests/test_live.py (20+ тестов)
- [x] run_tests.bat / run_tests.sh

---

## Фаза 7: Telegram [TODO]

### 7.1 Bot
- [ ] backend/telegram/bot.py
- [ ] Cornix format

### 7.2 Alerts
- [ ] Уведомления о сигналах
- [ ] TP/SL хиты

---

## Фазы 8-12: Frontend [TODO]

- [ ] Layout и компоненты
- [ ] 10 страниц Dashboard
- [ ] API интеграция
- [ ] PWA

---

## 📊 ОБЩИЙ ПРОГРЕСС

```
[██████████████████████████░░░░░░░░░░░░░░] 50%

✅ VELAS-01: Infrastructure
✅ VELAS-02: Data Engine  
✅ VELAS-03: Backtest Engine
✅ VELAS-04: Optimizer
✅ VELAS-05: Filters & Presets
✅ VELAS-06: Portfolio & Live Engine ← CURRENT
⬜ VELAS-07: Telegram
⬜ VELAS-08: Frontend Base
⬜ VELAS-09: Frontend Pages 1
⬜ VELAS-10: Frontend Pages 2
⬜ VELAS-11: Frontend Final
⬜ VELAS-12: Integration
```

---

## 📦 СТРУКТУРА МОДУЛЯ VELAS-05

```
backend/core/
├── __init__.py          ← Экспорт всех компонентов
├── volatility.py        ← Анализатор волатильности (ATR Ratio)
├── presets.py           ← Менеджер и генератор пресетов
├── velas_indicator.py   ← Индикатор (из VELAS-03)
├── signals.py           ← Генератор сигналов
└── tpsl.py              ← TP/SL логика

scripts/
└── generate_presets.py  ← CLI скрипт генерации

tests/
├── test_volatility.py   ← Тесты волатильности
└── test_presets.py      ← Тесты пресетов

run_tests.bat            ← Windows runner
run_tests.sh             ← Unix runner
```

---

## 🎯 КЛЮЧЕВЫЕ КОМПОНЕНТЫ VELAS-05

### VolatilityAnalyzer
```python
from backend.core import VolatilityAnalyzer, VolatilityRegime

analyzer = VolatilityAnalyzer(df)
regime = analyzer.get_regime()  # VolatilityRegime.LOW/NORMAL/HIGH
result = analyzer.analyze()     # Полный анализ с метриками
```

### PresetManager
```python
from backend.core import PresetManager, TradingPreset

manager = PresetManager("data/presets")

# Загрузка
preset = manager.get("BTCUSDT", "1h", "normal")

# Адаптивная загрузка (автоопределение режима)
preset = manager.get_adaptive("BTCUSDT", "1h", df)

# Список всех
all_presets = manager.load_all()
```

### PresetGenerator
```python
from backend.core import PresetGenerator

generator = PresetGenerator("data/presets")
generator.generate_all()  # 180 пресетов
```

---

*Обновлено: 2024-12-29*

---

## 📦 СТРУКТУРА МОДУЛЯ VELAS-06

```
backend/portfolio/
├── __init__.py          ← Экспорт всех компонентов
├── correlation.py       ← Корреляции, секторы, фильтры
├── risk.py              ← Position sizing, Portfolio heat
└── manager.py           ← PortfolioManager, Position

backend/live/
├── __init__.py          ← Экспорт всех компонентов
├── engine.py            ← LiveEngine (главный движок)
├── signal_manager.py    ← SignalManager, EnrichedSignal
├── position_tracker.py  ← PositionTracker, события
└── state.py             ← StateManager (SQLite)

tests/
├── conftest.py          ← Pytest fixtures
├── test_portfolio.py    ← Тесты Portfolio модуля
└── test_live.py         ← Тесты Live модуля

run_tests.bat            ← Windows runner
run_tests.sh             ← Unix runner
```

---

## 🎯 КЛЮЧЕВЫЕ КОМПОНЕНТЫ VELAS-06

### PortfolioManager
```python
from backend.portfolio import PortfolioManager, RiskLimits

manager = PortfolioManager(
    balance=10000,
    risk_limits=RiskLimits(
        max_positions=5,
        max_portfolio_heat=8.0,
        risk_per_trade=2.0,
        max_per_sector=2,
        correlation_threshold=0.7,
    ),
    leverage=10,
)

# Проверяем можно ли открыть
can_open, reason = manager.can_open_position("BTCUSDT")

# Рассчитываем размер
size = manager.calculate_position_size(
    symbol="BTCUSDT",
    entry_price=42000,
    stop_loss=40000,
)

# Открываем позицию
position = manager.open_position(...)
```

### LiveEngine
```python
from backend.live import LiveEngine, EngineConfig

config = EngineConfig(
    symbols=["BTCUSDT", "ETHUSDT"],
    timeframes=["30m", "1h", "2h"],
    trading_mode="paper",
    initial_balance=10000,
)

engine = LiveEngine(config)

# Callbacks
engine.on_signal = lambda s: send_to_telegram(s)
engine.on_position_event = lambda e: log_event(e)

# Запуск
await engine.start()
```

### StateManager
```python
from backend.live import StateManager

state = StateManager()

# Сохраняем позицию
state.save_position(position.to_dict())

# Загружаем открытые
positions = state.get_open_positions()

# История сделок
history = state.get_trade_history(symbol="BTCUSDT")
stats = state.get_trade_stats()
```
