# VELAS Trading System

Полнофункциональная криптовалютная торговая система с индикатором VELAS, бэктестингом и управлением портфелем.

## Содержание

- [Обзор](#обзор)
- [Архитектура](#архитектура)
- [Быстрый старт](#быстрый-старт)
- [Конфигурация](#конфигурация)
- [API Reference](#api-reference)
- [Frontend](#frontend)
- [База данных](#база-данных)
- [Разработка](#разработка)
- [Тестирование](#тестирование)

---

## Обзор

VELAS - это автоматизированная торговая система для криптовалютных фьючерсов на Binance, основанная на индикаторе VELAS с динамическими уровнями Take Profit.

### Ключевые функции

- **20 торговых пар**: BTC, ETH, BNB, SOL, XRP и другие топ криптовалюты
- **3 таймфрейма**: 30m, 1h, 2h
- **6 уровней Take Profit**: Автоматическое частичное закрытие позиций
- **Режимы волатильности**: LOW, NORMAL, HIGH - адаптация под рынок
- **Пресеты параметров**: Оптимизированные настройки для каждой пары
- **Telegram/Cornix интеграция**: Отправка сигналов в каналы
- **Бэктестинг**: Тестирование стратегий на исторических данных
- **Real-time WebSocket**: Потоковые данные с Binance

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                 │
│              React 18 + TypeScript + Vite + TailwindCSS         │
├─────────────────────────────────────────────────────────────────┤
│                          API Layer                               │
│                    FastAPI + WebSocket                           │
├─────────────────────────────────────────────────────────────────┤
│     Signals     │   Portfolio   │   Backtest   │   Telegram     │
│     Engine      │   Manager     │   Engine     │   Bot          │
├─────────────────────────────────────────────────────────────────┤
│                        Data Layer                                │
│           Binance REST/WS + SQLite + Parquet Storage            │
└─────────────────────────────────────────────────────────────────┘
```

### Структура проекта

```
velas/
├── backend/
│   ├── api/
│   │   ├── routes/          # API endpoints
│   │   │   ├── alerts.py    # Уведомления
│   │   │   ├── analytics.py # Аналитика
│   │   │   ├── backtest.py  # Бэктестинг
│   │   │   ├── dashboard.py # Дашборд
│   │   │   ├── history.py   # История сделок
│   │   │   ├── pairs.py     # Торговые пары
│   │   │   ├── positions.py # Позиции
│   │   │   ├── settings.py  # Настройки
│   │   │   ├── signals.py   # Сигналы
│   │   │   └── system.py    # Системные
│   │   └── models.py        # Pydantic модели
│   ├── data/
│   │   ├── binance_rest.py  # REST клиент Binance
│   │   ├── binance_ws.py    # WebSocket клиент
│   │   └── storage.py       # Parquet хранилище
│   ├── db/
│   │   ├── database.py      # SQLAlchemy подключение
│   │   └── models.py        # ORM модели
│   ├── portfolio/
│   │   └── manager.py       # Управление портфелем
│   ├── signals/
│   │   └── signals.py       # Генерация сигналов
│   └── telegram/
│       └── bot.py           # Telegram интеграция
├── frontend/
│   ├── src/
│   │   ├── components/      # React компоненты
│   │   ├── hooks/           # Custom hooks
│   │   ├── pages/           # Страницы
│   │   ├── services/        # API клиент
│   │   ├── stores/          # Zustand сторы
│   │   └── types/           # TypeScript типы
│   └── package.json
├── config/
│   ├── pairs.yaml           # Список торговых пар
│   └── config.example.yaml  # Шаблон конфигурации
├── scripts/
│   └── download_history.py  # Загрузка исторических данных
└── requirements.txt
```

---

## Быстрый старт

### Требования

- Python 3.11+
- Node.js 18+
- npm или yarn

### 1. Клонирование

```bash
git clone https://github.com/ironsan2kk-pixel/Velas-code.git
cd Velas-code
```

### 2. Backend

```bash
# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или: venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Копирование конфигурации
cp config/config.example.yaml config/config.yaml

# Запуск сервера
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend

```bash
cd frontend

# Установка зависимостей
npm install

# Запуск dev-сервера
npm run dev
```

### 4. Открыть в браузере

- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Конфигурация

### config/config.yaml

```yaml
# Основные настройки
app:
  name: "VELAS Trading System"
  debug: false
  log_level: "INFO"

# База данных
database:
  url: "sqlite:///./velas.db"

# Binance API (опционально для live trading)
binance:
  api_key: ""
  api_secret: ""
  testnet: true

# Telegram (опционально)
telegram:
  bot_token: ""
  channel_id: ""

# Торговые настройки
trading:
  initial_capital: 10000
  max_positions: 5
  risk_per_trade: 1.0  # %

# Настройки VELAS индикатора
velas:
  default_params:
    i1: 21
    i2: 34
    i3: 8
    i4: 13
    i5: 10
```

### config/pairs.yaml

```yaml
pairs:
  - symbol: BTCUSDT
    name: Bitcoin
    sector: major

  - symbol: ETHUSDT
    name: Ethereum
    sector: major

  # ... 20 пар
```

---

## API Reference

### Базовый URL
```
http://localhost:8000/api
```

### Endpoints

#### Dashboard
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/dashboard/summary` | Сводка портфеля |
| GET | `/dashboard/metrics` | Метрики производительности |
| GET | `/dashboard/chart` | График эквити |

#### Positions
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/positions` | Список позиций |
| GET | `/positions/{id}` | Детали позиции |
| POST | `/positions/{id}/close` | Закрыть позицию |
| GET | `/positions/summary` | Сводка позиций |

#### Signals
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/signals` | История сигналов |
| GET | `/signals/pending` | Активные сигналы |
| GET | `/signals/{id}` | Детали сигнала |

#### Pairs
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/pairs` | Все торговые пары |
| GET | `/pairs/{symbol}` | Детали пары |
| GET | `/pairs/{symbol}/chart` | График цены |
| GET | `/pairs/{symbol}/signals` | Сигналы по паре |

#### Backtest
| Method | Endpoint | Описание |
|--------|----------|----------|
| POST | `/backtest/run` | Запустить бэктест |
| GET | `/backtest/status/{id}` | Статус бэктеста |
| GET | `/backtest/results` | Все результаты |
| GET | `/backtest/results/{id}` | Результат бэктеста |

#### Settings
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/settings` | Все настройки |
| PUT | `/settings` | Обновить настройки |
| GET | `/settings/presets` | Пресеты параметров |
| GET | `/settings/presets/{id}` | Пресет по ID |
| PUT | `/settings/presets/{id}` | Обновить пресет |

#### Alerts
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/alerts/history` | История уведомлений |
| GET | `/alerts/settings` | Настройки уведомлений |
| PUT | `/alerts/settings` | Обновить настройки |

#### System
| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/system/status` | Статус компонентов |
| GET | `/system/logs` | Системные логи |
| POST | `/system/pause` | Пауза торговли |
| POST | `/system/resume` | Возобновить торговлю |
| POST | `/system/restart` | Перезапуск компонента |

### Формат ответа

```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

// Подписка на каналы
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['signals', 'positions', 'system']
}));

// События
// - signal_new: Новый сигнал
// - position_opened: Открыта позиция
// - position_closed: Закрыта позиция
// - tp_hit: Достигнут Take Profit
// - sl_hit: Сработал Stop Loss
// - system_status: Обновление статуса
```

---

## Frontend

### Технологии

- **React 18** - UI фреймворк
- **TypeScript** - Типизация
- **Vite** - Сборщик
- **TailwindCSS** - Стили
- **Zustand** - Стейт менеджмент
- **React Query** - Кэширование API
- **Recharts** - Графики
- **Lucide** - Иконки

### Страницы

| Путь | Компонент | Описание |
|------|-----------|----------|
| `/` | Dashboard | Главная с метриками |
| `/positions` | Positions | Открытые позиции |
| `/signals` | Signals | История сигналов |
| `/pairs` | Pairs | Торговые пары |
| `/analytics` | Analytics | Аналитика |
| `/backtest` | Backtest | Бэктестинг |
| `/settings` | Settings | Настройки |
| `/history` | History | История сделок |
| `/system` | System | Системный монитор |

### Сборка для production

```bash
cd frontend
npm run build
```

Результат в `frontend/dist/`

---

## База данных

### SQLite таблицы

```sql
-- Позиции
CREATE TABLE positions (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(20),
    side VARCHAR(10),
    entry_price FLOAT,
    quantity FLOAT,
    status VARCHAR(20),
    created_at DATETIME
);

-- Сигналы
CREATE TABLE signals (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(20),
    side VARCHAR(10),
    entry_price FLOAT,
    stop_loss FLOAT,
    status VARCHAR(20),
    created_at DATETIME
);

-- Алерты
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    type VARCHAR(20),
    category VARCHAR(30),
    title VARCHAR(200),
    message TEXT,
    read BOOLEAN,
    created_at DATETIME
);

-- Пресеты
CREATE TABLE presets (
    id INTEGER PRIMARY KEY,
    preset_id VARCHAR(100) UNIQUE,
    symbol VARCHAR(20),
    timeframe VARCHAR(10),
    volatility_regime VARCHAR(20),
    i1 INTEGER,
    i2 INTEGER,
    -- ... параметры
);

-- Настройки
CREATE TABLE settings (
    id INTEGER PRIMARY KEY,
    key VARCHAR(100) UNIQUE,
    value TEXT,
    updated_at DATETIME
);
```

---

## Разработка

### Backend

```bash
# Запуск с автоперезагрузкой
uvicorn backend.api.main:app --reload

# Форматирование
black backend/
isort backend/

# Проверка типов
mypy backend/
```

### Frontend

```bash
# Dev сервер
npm run dev

# Проверка типов
npm run type-check

# Линтинг
npm run lint

# Форматирование
npm run format
```

---

## Тестирование

### Backend тесты

```bash
# Все тесты
python -m pytest backend/tests/ -v

# С покрытием
python -m pytest backend/tests/ --cov=backend

# Только unit тесты
python -m pytest backend/tests/unit/ -v

# Сетевые тесты
SKIP_NETWORK_TESTS=0 python -m pytest backend/tests/ -v
```

### Frontend тесты

```bash
cd frontend

# Unit тесты
npm run test

# E2E тесты
npm run test:e2e
```

---

## Переменные окружения

```bash
# Backend
DATABASE_URL=sqlite:///./velas.db
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHANNEL_ID=your_channel

# Frontend
VITE_API_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws
```

---

## Лицензия

MIT License

---

## Авторы

VELAS Trading System Team
