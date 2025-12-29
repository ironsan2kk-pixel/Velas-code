# VELAS TRADING SYSTEM v2 — МАСТЕР-ПЛАН

**Версия:** 2.0 | **Дата:** 2024-12-29

---

## 📋 ОБЗОР

| Параметр | Значение |
|----------|----------|
| Название | VELAS Trading System |
| Тип | Локальная торговая система |
| Платформа | Windows VPS |
| Исполнение | Telegram → Cornix |

---

## 🎯 ЦЕЛИ

| Метрика | Цель |
|---------|------|
| WinRate TP1 | ≥ 70% |
| Sharpe Ratio | ≥ 1.2 |
| Max Drawdown | ≤ 15% |
| Max Positions | 5 |

---

## 📊 МАСШТАБ

- **20 пар:** BTC, ETH, BNB, SOL, XRP, ADA, AVAX, DOGE, DOT, MATIC, LINK, UNI, ATOM, LTC, ETC, NEAR, APT, ARB, OP, INJ
- **3 таймфрейма:** 30m, 1h, 2h
- **3 режима волатильности:** low, normal, high
- **180 пресетов** (20 × 3 × 3)

---

## 💰 TP/SL СИСТЕМА

```
TP1 (20%) → SL → БУ (Breakeven)
TP2 (20%) → SL → TP1 (каскад)
TP3 (15%) → SL → TP2
TP4 (15%) → SL → TP3
TP5 (15%) → SL → TP4
TP6 (15%) → Закрыть всё
```

---

## 🔬 ОПТИМИЗАЦИЯ

**Walk-Forward Analysis:**
- Train: 6 месяцев
- Test: 2 месяца (unseen)
- Минимум 4 периода

**Критерии пресета:**
- Sharpe ≥ 1.2 (не > 2.5!)
- WinRate TP1 ≥ 65%
- Profit Factor ≥ 1.4
- Max DD ≤ 15%
- Robustness ≥ 0.8

---

## 🖥 DASHBOARD (10 страниц)

| # | Страница | URL |
|---|----------|-----|
| 1 | Главная | `/` |
| 2 | Позиции | `/positions` |
| 3 | История | `/history` |
| 4 | Сигналы | `/signals` |
| 5 | Пары | `/pairs` |
| 6 | Аналитика | `/analytics` |
| 7 | Бэктест | `/backtest` |
| 8 | Настройки | `/settings` |
| 9 | Уведомления | `/alerts` |
| 10 | Система | `/system` |

---

## 📅 ФАЗЫ

| Чат | Фаза | Описание |
|-----|------|----------|
| VELAS-01 | Инфраструктура | Git, структура, конфиги |
| VELAS-02 | Data Engine | Binance API |
| VELAS-03 | Velas Core | Индикатор |
| VELAS-04 | Backtester | Тестирование |
| VELAS-05 | Optimizer | Walk-Forward |
| VELAS-06 | Live Engine | Торговля |
| VELAS-07 | Telegram | Бот + Cornix |
| VELAS-08 | Frontend Base | Layout, компоненты |
| VELAS-09 | Frontend Pages 1 | Dashboard, Positions, History |
| VELAS-10 | Frontend Pages 2 | Signals, Pairs, Analytics |
| VELAS-11 | Frontend Final | Backtest, Settings, System |
| VELAS-12 | Integration | Финал, тесты |

---

## 🛠 TECH STACK

**Backend:** Python 3.11, FastAPI, SQLAlchemy, python-binance  
**Frontend:** React 18, TypeScript, Tailwind, Recharts  
**Data:** Parquet, SQLite  
**Telegram:** python-telegram-bot, Cornix format

---

## 📁 СТРУКТУРА

```
C:\velas\
├── code\Velas-code\    ← Git репозиторий
│   ├── backend\
│   ├── frontend\
│   ├── scripts\
│   ├── tests\
│   └── docs\
├── data\               ← НЕ в Git
├── logs\               ← НЕ в Git
├── config.yaml         ← НЕ в Git
└── START.bat           ← НЕ в Git
```

---

*Полная документация в отдельных файлах*
