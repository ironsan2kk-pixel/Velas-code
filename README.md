# VELAS Trading System v2

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![React](https://img.shields.io/badge/react-18+-61dafb)
![License](https://img.shields.io/badge/license-Private-red)

Локальная криптотрейдинговая система для генерации торговых сигналов.

---

## 📋 Описание

VELAS Trading System — это автоматизированная система для:
- Анализа криптовалютных пар (20 пар × 3 таймфрейма)
- Генерации торговых сигналов на основе индикатора Velas
- Отправки сигналов в Telegram (формат Cornix)
- Мониторинга через Web Dashboard

---

## 🏗 Архитектура

```
Binance API → Data Engine → Velas Core → Signal Generator → Telegram Bot
                                ↓
                          Portfolio Manager
                                ↓
                           Live Engine → Dashboard
```

---

## 📊 Торговые пары

| Сектор | Пары |
|--------|------|
| BTC/ETH | BTCUSDT, ETHUSDT |
| L1 | SOLUSDT, AVAXUSDT, ATOMUSDT, NEARUSDT, APTUSDT |
| L2 | MATICUSDT, ARBUSDT, OPUSDT |
| DeFi | LINKUSDT, UNIUSDT, INJUSDT |
| Old | XRPUSDT, ADAUSDT, DOTUSDT, LTCUSDT, ETCUSDT |
| Meme | DOGEUSDT |
| CEX | BNBUSDT |

**Таймфреймы:** 30m, 1h, 2h

---

## 🛠 Технологии

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy
- python-binance
- python-telegram-bot

### Frontend
- React 18 + TypeScript
- Vite
- Tailwind CSS
- TanStack Query
- Recharts

---

## 📁 Структура проекта

```
Velas-code/                    ← Git репозиторий
├── backend/
│   ├── core/                  ← Логика Velas
│   ├── data/                  ← Binance API
│   ├── backtest/              ← Бэктестинг
│   ├── live/                  ← Live Engine
│   ├── portfolio/             ← Portfolio Manager
│   ├── telegram/              ← Telegram Bot
│   ├── api/                   ← FastAPI
│   ├── db/                    ← Database
│   └── config/                ← Конфигурация
├── frontend/
│   └── src/
│       ├── pages/             ← 10 страниц
│       ├── components/        ← UI компоненты
│       └── ...
├── scripts/                   ← Утилиты
├── tests/                     ← Тесты
└── docs/                      ← Документация

C:\velas\                      ← Локально (НЕ в Git)
├── data/                      ← Свечи, пресеты
├── logs/                      ← Логи
├── config.yaml                ← Секреты
└── START.bat                  ← Запуск
```

---

## ⚙️ Установка

### 1. Клонировать репозиторий

```bash
git clone https://github.com/ironsan2kk-pixel/Velas-code.git
cd Velas-code
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Frontend

```bash
cd frontend
npm install
```

### 4. Конфигурация

```bash
# Скопировать пример конфига
copy backend\config\config.example.yaml C:\velas\config.yaml

# Отредактировать config.yaml - добавить API ключи
```

### 5. Создать локальные папки

```bash
mkdir C:\velas\data
mkdir C:\velas\data\candles
mkdir C:\velas\data\presets
mkdir C:\velas\logs
```

---

## 🚀 Запуск

### Через START.bat (рекомендуется)

```bash
C:\velas\START.bat
```

### Вручную

```bash
# Backend
cd Velas-code\backend
python -m uvicorn api.main:app --reload --port 8000

# Frontend
cd Velas-code\frontend
npm run dev
```

---

## 📱 Dashboard

- **URL:** http://localhost:5173
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs

### Страницы

| Страница | Описание |
|----------|----------|
| Главная | Сводка, метрики, графики |
| Позиции | Открытые позиции |
| История | Закрытые сделки |
| Сигналы | Лог сигналов |
| Пары | 20 пар с детализацией |
| Аналитика | Графики, статистика |
| Бэктест | Тестирование стратегий |
| Настройки | Конфигурация |
| Уведомления | Telegram, Push |
| Система | Логи, статус |

---

## 📈 Методология

### Walk-Forward Analysis
- Train: 6 месяцев
- Test: 2 месяца (unseen data)
- Минимум 4-5 периодов

### Критерии пресета
- Sharpe ≥ 1.2
- WinRate TP1 ≥ 65%
- Max Drawdown ≤ 15%
- Robustness ≥ 0.8

---

## 📝 Лицензия

Private. Все права защищены.

---

## 👤 Автор

ironsan2kk-pixel

---

*Версия 2.0.0 | Декабрь 2024*
