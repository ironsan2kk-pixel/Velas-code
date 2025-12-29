# VELAS v2 — ЧЕКЛИСТ

**Последнее обновление:** 2024-12-29  
**Текущая фаза:** VELAS-03  
**Прогресс:** 3/12 фаз

---

## ИСТОРИЯ ИЗМЕНЕНИЙ

| Дата | Коммит | Что сделано | Исправления |
|------|--------|-------------|-------------|
| 2024-12-29 | — | VELAS-00: Планирование | — |
| 2024-12-29 | — | VELAS-01: Инфраструктура | — |
| 2024-12-29 | — | VELAS-02: Data Engine (binance_rest, binance_ws, storage) | — |
| 2024-12-29 | — | VELAS-03: Backtest Engine (indicator, signals, tpsl, metrics) | Исправлены edge cases в тестах |

---

## Фаза 0: Планирование [2/2]
- [x] Структура проекта определена
- [x] CLAUDE_INSTRUCTIONS.md создан

## Фаза 1: Инфраструктура [1/1]
- [x] Базовая структура папок

## Фаза 2: Data Engine [4/4]
- [x] backend/data/binance_rest.py — REST клиент Binance
- [x] backend/data/binance_ws.py — WebSocket клиент
- [x] backend/data/storage.py — Parquet хранилище
- [x] scripts/download_history.py — Скачивание истории

## Фаза 3: Backtest Engine [6/6]
- [x] backend/core/velas_indicator.py — Pine Script → Python (60 пресетов)
- [x] backend/core/signals.py — Генерация LONG/SHORT + фильтры
- [x] backend/core/tpsl.py — TP1-6, SL, каскадный стоп, БУ
- [x] backend/backtest/trade.py — Симуляция сделок
- [x] backend/backtest/metrics.py — WinRate, Sharpe, MaxDD, PF
- [x] backend/backtest/engine.py — Движок бэктестинга
- [x] tests/test_velas_indicator.py — 24 теста
- [x] tests/test_signals.py — 24 теста

## Фаза 4: Optimizer [ ]
- [ ] backend/backtest/optimizer.py — Grid search
- [ ] backend/backtest/walk_forward.py — Walk-Forward анализ
- [ ] backend/backtest/robustness.py — Проверка устойчивости

## Фаза 5: Portfolio [ ]
- [ ] backend/portfolio/manager.py
- [ ] backend/portfolio/correlation.py
- [ ] backend/portfolio/risk.py

## Фаза 6: Live Engine [ ]
- [ ] backend/live/engine.py
- [ ] backend/live/position_tracker.py
- [ ] backend/live/signal_manager.py
- [ ] backend/live/state.py

## Фаза 7: Telegram [ ]
- [ ] backend/telegram/bot.py
- [ ] backend/telegram/cornix.py

## Фаза 8-11: Frontend [ ]
- [ ] Layout и навигация
- [ ] 10 страниц Dashboard
- [ ] Графики и аналитика
- [ ] PWA и финализация

## Фаза 12: Integration & Launch [ ]
- [ ] Интеграционные тесты
- [ ] Документация
- [ ] Деплой
