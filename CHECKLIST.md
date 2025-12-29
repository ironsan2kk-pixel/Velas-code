# VELAS v2 — ЧЕКЛИСТ

**Версия:** 2.0  
**Последнее обновление:** 2024-12-29  
**Текущая фаза:** VELAS-01 (Инфраструктура)  
**Общий прогресс:** 8/180 задач

---

## 📜 ИСТОРИЯ ИЗМЕНЕНИЙ

| Дата | Коммит | Что сделано | Исправления |
|------|--------|-------------|-------------|
| 2024-12-29 | — | Инициализация проекта | — |
| 2024-12-29 | — | Структура папок + конфиги | — |

---

## 📊 ПРОГРЕСС ПО ФАЗАМ

| Фаза | Название | Статус | Прогресс |
|------|----------|--------|----------|
| VELAS-01 | Инфраструктура | 🔄 В работе | 8/15 |
| VELAS-02 | Data Engine | ⏳ Ожидает | 0/12 |
| VELAS-03 | Velas Core | ⏳ Ожидает | 0/14 |
| VELAS-04 | Backtester | ⏳ Ожидает | 0/10 |
| VELAS-05 | Optimizer | ⏳ Ожидает | 0/12 |
| VELAS-06 | Live Engine | ⏳ Ожидает | 0/14 |
| VELAS-07 | Telegram | ⏳ Ожидает | 0/8 |
| VELAS-08 | Frontend Base | ⏳ Ожидает | 0/18 |
| VELAS-09 | Frontend Pages 1 | ⏳ Ожидает | 0/20 |
| VELAS-10 | Frontend Pages 2 | ⏳ Ожидает | 0/20 |
| VELAS-11 | Frontend Final | ⏳ Ожидает | 0/22 |
| VELAS-12 | Integration | ⏳ Ожидает | 0/15 |

---

## VELAS-01: Инфраструктура [8/15]

### 1.1 Структура проекта [5/5] ✅
- [x] Создать структуру backend (`backend/core/`, `backend/data/`, и т.д.)
- [x] Создать структуру frontend (`frontend/src/`, и т.д.)
- [x] Создать папки `scripts/`, `tests/`
- [x] Создать `__init__.py` для всех Python пакетов
- [x] Создать `.gitkeep` для пустых папок

### 1.2 Git конфигурация [2/3]
- [x] `.gitignore` (Python + Node + секреты + данные)
- [x] `README.md` (описание проекта)
- [ ] Первый коммит структуры

### 1.3 Конфигурационные файлы [4/4] ✅
- [x] `backend/config/config.example.yaml` (шаблон конфигурации)
- [x] `backend/config/pairs.yaml` (20 пар)
- [x] `backend/requirements.txt` (все зависимости)
- [x] `frontend/package.json` (все зависимости)

### 1.4 Скрипты запуска [0/3]
- [ ] `START.bat` (главное меню) — в `C:\velas\` локально
- [ ] `tests/run_all_tests.bat`
- [ ] Локальные папки созданы (`C:\velas\data\`, `C:\velas\logs\`)

---

## VELAS-02: Data Engine [0/12]

### 2.1 Binance REST Client [0/5]
- [ ] `backend/data/binance_rest.py` — базовый клиент
- [ ] Метод `get_klines()` — получение свечей
- [ ] Метод `get_ticker()` — текущая цена
- [ ] Метод `get_exchange_info()` — информация о паре
- [ ] Rate limiting и error handling

### 2.2 Binance WebSocket [0/4]
- [ ] `backend/data/binance_ws.py` — WS клиент
- [ ] Подписка на kline streams (20 пар × 3 TF)
- [ ] Автоматический reconnect
- [ ] Callback система для новых свечей

### 2.3 Storage [0/3]
- [ ] `backend/data/storage.py` — Parquet хранилище
- [ ] Метод `save_candles()` / `load_candles()`
- [ ] `scripts/download_history.py` — скачивание истории

---

## VELAS-03: Velas Core [0/14]

### 3.1 Индикатор [0/5]
- [ ] `backend/core/velas_core.py` — главный файл
- [ ] `calculate_ema()` — EMA расчёт
- [ ] `calculate_atr()` — ATR расчёт  
- [ ] `calculate_channels()` — верхний/средний/нижний каналы
- [ ] `calculate_triggers()` — триггеры входа

### 3.2 Сигналы [0/4]
- [ ] `backend/core/signals.py` — генератор сигналов
- [ ] `Signal` dataclass (все поля)
- [ ] `generate_signal()` — создание сигнала
- [ ] `validate_signal()` — валидация

### 3.3 TP/SL [0/3]
- [ ] `backend/core/tpsl.py` — логика TP/SL
- [ ] `calculate_tp_levels()` — 6 уровней TP
- [ ] `update_sl_on_tp_hit()` — БУ и каскад

### 3.4 Пресеты [0/2]
- [ ] `backend/core/presets.py` — загрузчик пресетов
- [ ] `get_preset_for_conditions()` — выбор по волатильности

---

## VELAS-04: Backtester [0/10]

### 4.1 Движок [0/5]
- [ ] `backend/backtest/engine.py` — BacktestEngine class
- [ ] `run()` — запуск бэктеста
- [ ] `process_candle()` — обработка свечи
- [ ] `execute_trade()` — исполнение сделки
- [ ] `generate_report()` — отчёт

### 4.2 Метрики [0/5]
- [ ] `backend/backtest/metrics.py` — расчёт метрик
- [ ] `sharpe_ratio()` 
- [ ] `profit_factor()`
- [ ] `max_drawdown()`
- [ ] `win_rate()` (TP1, TP3, overall)

---

## VELAS-05: Optimizer [0/12]

### 5.1 Grid Optimizer [0/3]
- [ ] `backend/backtest/optimizer.py` — GridOptimizer
- [ ] `optimize()` — grid search
- [ ] `get_best_params()` — лучшие параметры

### 5.2 Walk-Forward [0/4]
- [ ] `backend/backtest/walk_forward.py` — WalkForwardAnalyzer
- [ ] `create_periods()` — создание периодов train/test
- [ ] `run_analysis()` — запуск анализа
- [ ] `aggregate_results()` — агрегация результатов

### 5.3 Robustness [0/3]
- [ ] `backend/backtest/robustness.py` — проверка устойчивости
- [ ] `check_neighbors()` — соседние параметры ±15%
- [ ] `calculate_score()` — скор устойчивости

### 5.4 Генерация пресетов [0/2]
- [ ] `scripts/generate_presets.py` — генератор
- [ ] Создание 180 YAML файлов пресетов

---

## VELAS-06: Live Engine [0/14]

### 6.1 Главный движок [0/4]
- [ ] `backend/live/engine.py` — LiveEngine class
- [ ] `start()` / `stop()` — управление
- [ ] `on_new_candle()` — обработка новой свечи
- [ ] `process_signal()` — обработка сигнала

### 6.2 Position Tracker [0/4]
- [ ] `backend/live/position_tracker.py` — PositionTracker
- [ ] `open_position()` — открытие позиции
- [ ] `update_position()` — обновление (TP hit, SL move)
- [ ] `close_position()` — закрытие

### 6.3 Signal Manager [0/2]
- [ ] `backend/live/signal_manager.py` — SignalManager
- [ ] Управление активными/pending сигналами

### 6.4 State [0/2]
- [ ] `backend/live/state.py` — персистентность
- [ ] `save_state()` / `load_state()`

### 6.5 Portfolio Manager [0/2]
- [ ] `backend/portfolio/manager.py` — PortfolioManager
- [ ] `backend/portfolio/correlation.py` — корреляции

---

## VELAS-07: Telegram [0/8]

### 7.1 Бот [0/4]
- [ ] `backend/telegram/bot.py` — TelegramBot class
- [ ] `send_signal()` — отправка сигнала
- [ ] `send_update()` — обновление (TP hit, SL move)
- [ ] `send_report()` — ежедневный отчёт

### 7.2 Cornix форматтер [0/4]
- [ ] `backend/telegram/cornix.py` — форматтер
- [ ] `format_signal()` — Cornix формат сигнала
- [ ] `format_tp_hit()` — уведомление о TP
- [ ] `format_sl_hit()` — уведомление о SL

---

## VELAS-08: Frontend Base [0/18]

### 8.1 Проект setup [0/5]
- [ ] Vite + React + TypeScript инициализация
- [ ] Tailwind CSS конфигурация
- [ ] Тёмная/светлая тема (CSS variables)
- [ ] ESLint + Prettier конфигурация
- [ ] PWA базовая настройка

### 8.2 Layout [0/4]
- [ ] `Sidebar.tsx` — навигация
- [ ] `Header.tsx` — шапка
- [ ] `MainLayout.tsx` — общий layout
- [ ] Responsive design (mobile menu)

### 8.3 UI компоненты [0/5]
- [ ] `Button.tsx`, `Input.tsx`, `Select.tsx`
- [ ] `Card.tsx`, `Table.tsx`
- [ ] `Modal.tsx`, `Toast.tsx`
- [ ] `Badge.tsx`, `Spinner.tsx`
- [ ] `Chart` компоненты (Recharts)

### 8.4 Инфраструктура [0/4]
- [ ] React Router — роутинг 10 страниц
- [ ] API client (axios) — `api/client.ts`
- [ ] WebSocket client — `api/websocket.ts`
- [ ] Zustand stores — `store/`

---

## VELAS-09: Frontend Pages 1 [0/20]

### 9.1 Dashboard (/) [0/7]
- [ ] `pages/Dashboard.tsx` — страница
- [ ] Карточки метрик (баланс, прибыль, win rate, DD)
- [ ] Equity chart (Recharts)
- [ ] Open positions widget
- [ ] Recent signals widget
- [ ] Top pairs widget
- [ ] API: `GET /api/dashboard/summary`

### 9.2 Positions (/positions) [0/6]
- [ ] `pages/Positions.tsx` — страница
- [ ] Таблица открытых позиций
- [ ] Фильтры (пара, направление, TF)
- [ ] Детали позиции (sidebar/modal)
- [ ] Position chart с TP/SL уровнями
- [ ] API: `GET /api/positions`

### 9.3 History (/history) [0/7]
- [ ] `pages/History.tsx` — страница
- [ ] Таблица истории с пагинацией
- [ ] Фильтры (период, пара, результат)
- [ ] Статистика периода (карточки)
- [ ] Export CSV
- [ ] API: `GET /api/history`
- [ ] API: `GET /api/history/stats`

---

## VELAS-10: Frontend Pages 2 [0/20]

### 10.1 Signals (/signals) [0/6]
- [ ] `pages/Signals.tsx` — страница
- [ ] Таблица сигналов (active/pending/all)
- [ ] Детали сигнала
- [ ] Copy Cornix format
- [ ] Realtime обновления (WebSocket)
- [ ] API: `GET /api/signals`

### 10.2 Pairs (/pairs) [0/7]
- [ ] `pages/Pairs.tsx` — страница
- [ ] Grid 20 пар с метриками
- [ ] Поиск и фильтры
- [ ] Детали пары
- [ ] TradingView-style chart (lightweight-charts)
- [ ] Статистика по паре
- [ ] API: `GET /api/pairs`, `GET /api/pairs/{symbol}`

### 10.3 Analytics (/analytics) [0/7]
- [ ] `pages/Analytics.tsx` — страница
- [ ] Equity curve (большой график)
- [ ] Drawdown chart
- [ ] Monthly stats table
- [ ] Correlation matrix heatmap
- [ ] PnL distribution chart
- [ ] API: `GET /api/analytics/*`

---

## VELAS-11: Frontend Final [0/22]

### 11.1 Backtest (/backtest) [0/7]
- [ ] `pages/Backtest.tsx` — страница
- [ ] Форма нового бэктеста
- [ ] История бэктестов
- [ ] Результаты бэктеста (графики + метрики)
- [ ] Export результатов
- [ ] API: `POST /api/backtest/run`
- [ ] API: `GET /api/backtest/results`

### 11.2 Settings (/settings) [0/6]
- [ ] `pages/Settings.tsx` — страница
- [ ] Вкладки: Общие, Торговля, Telegram, API, Пресеты
- [ ] Форма настроек с валидацией
- [ ] Активные пары checkboxes
- [ ] API: `GET/PUT /api/settings`
- [ ] Сохранение в config.yaml

### 11.3 Alerts (/alerts) [0/4]
- [ ] `pages/Alerts.tsx` — страница
- [ ] Telegram настройки + тест
- [ ] Типы уведомлений (checkboxes)
- [ ] Web Push настройки

### 11.4 System (/system) [0/5]
- [ ] `pages/System.tsx` — страница
- [ ] Статус компонентов (таблица)
- [ ] Logs viewer (последние 100)
- [ ] Actions (restart, clear cache)
- [ ] API: `GET /api/system/*`

---

## VELAS-12: Integration & Launch [0/15]

### 12.1 Backend API [0/5]
- [ ] `backend/api/main.py` — FastAPI app
- [ ] Все routes подключены
- [ ] WebSocket endpoint `/ws`
- [ ] CORS настройка
- [ ] Error handling middleware

### 12.2 Database [0/3]
- [ ] `backend/db/database.py` — SQLAlchemy setup
- [ ] `backend/db/models.py` — ORM модели
- [ ] Миграции (Alembic)

### 12.3 Тестирование [0/4]
- [ ] Unit tests (pytest)
- [ ] Integration tests
- [ ] E2E tests (frontend)
- [ ] Все тесты проходят ✓

### 12.4 Финализация [0/3]
- [ ] Performance optimization
- [ ] Security review
- [ ] Production deployment готов

---

## 📋 LEGEND

```
[ ] — Не начато
[~] — В процессе
[x] — Выполнено (+ хеш коммита)
✅ — Секция полностью завершена
```

---

*Чеклист обновляется с каждым коммитом*
