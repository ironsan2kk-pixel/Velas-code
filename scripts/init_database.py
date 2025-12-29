"""
VELAS - Инициализация базы данных.

Создаёт все таблицы и наполняет начальными данными.
"""

import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from datetime import datetime, timedelta
import random

from backend.db.database import Base, engine, SessionLocal, init_db
from backend.db.models import (
    PositionModel,
    SignalModel,
    TradeModel,
    SystemLogModel,
    SettingModel,
)

# 20 торговых пар
PAIRS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT",
    "LINKUSDT", "UNIUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT",
    "NEARUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "INJUSDT",
]

TIMEFRAMES = ["30m", "1h", "2h"]
SIDES = ["LONG", "SHORT"]
VOLATILITY_REGIMES = ["low", "normal", "high"]


def create_tables():
    """Создание всех таблиц."""
    print("🔧 Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы")


def seed_settings(db):
    """Начальные настройки системы."""
    print("⚙️ Добавление начальных настроек...")
    
    default_settings = [
        # Trading Settings
        ("trading.enabled", True, "Торговля включена"),
        ("trading.max_positions", 5, "Максимум одновременных позиций"),
        ("trading.risk_percent", 2.0, "Риск на сделку в %"),
        ("trading.portfolio_heat_limit", 15.0, "Лимит portfolio heat в %"),
        ("trading.min_confidence", 0.6, "Минимальная уверенность сигнала"),
        ("trading.signal_expiry_minutes", 30, "Время жизни сигнала в минутах"),
        
        # Portfolio Settings
        ("portfolio.initial_balance", 10000.0, "Начальный баланс USDT"),
        ("portfolio.current_balance", 10000.0, "Текущий баланс USDT"),
        ("portfolio.correlation_limit", 0.7, "Лимит корреляции между парами"),
        ("portfolio.max_drawdown_percent", 15.0, "Максимальная просадка для паузы"),
        ("portfolio.auto_pause_loss_streak", 3, "Пауза после N убытков подряд"),
        
        # Telegram Settings
        ("telegram.enabled", True, "Telegram уведомления включены"),
        ("telegram.send_signals", True, "Отправлять сигналы"),
        ("telegram.send_updates", True, "Отправлять обновления позиций"),
        ("telegram.send_alerts", True, "Отправлять системные алерты"),
        
        # System Settings
        ("system.log_level", "INFO", "Уровень логирования"),
        ("system.data_update_interval", 5, "Интервал обновления данных в секундах"),
        ("system.api_rate_limit", 1200, "API rate limit в запросах/минуту"),
        
        # Alert Settings
        ("alerts.enabled", True, "Алерты включены"),
        ("alerts.loss_streak_threshold", 3, "Порог серии убытков"),
        ("alerts.low_winrate_threshold", 50.0, "Порог низкого WR %"),
        ("alerts.high_drawdown_threshold", 10.0, "Порог высокой просадки %"),
    ]
    
    for key, value, description in default_settings:
        existing = db.query(SettingModel).filter(SettingModel.key == key).first()
        if not existing:
            setting = SettingModel(key=key, value=value, description=description)
            db.add(setting)
    
    db.commit()
    print(f"✅ Добавлено {len(default_settings)} настроек")


def seed_sample_data(db):
    """Примеры данных для демо."""
    print("📊 Добавление демо-данных...")
    
    now = datetime.utcnow()
    
    # Sample Signals (последние 24 часа)
    signals_count = 0
    for i in range(20):
        symbol = random.choice(PAIRS)
        side = random.choice(SIDES)
        timeframe = random.choice(TIMEFRAMES)
        entry = round(random.uniform(100, 100000), 2)
        sl_pct = random.uniform(1.5, 3.0)
        
        signal = SignalModel(
            symbol=symbol,
            side=side,
            timeframe=timeframe,
            entry_price=entry,
            sl_price=round(entry * (1 - sl_pct / 100) if side == "LONG" else entry * (1 + sl_pct / 100), 2),
            tp1_price=round(entry * (1 + 0.8 / 100) if side == "LONG" else entry * (1 - 0.8 / 100), 2),
            tp2_price=round(entry * (1 + 1.5 / 100) if side == "LONG" else entry * (1 - 1.5 / 100), 2),
            tp3_price=round(entry * (1 + 2.5 / 100) if side == "LONG" else entry * (1 - 2.5 / 100), 2),
            tp4_price=round(entry * (1 + 4.0 / 100) if side == "LONG" else entry * (1 - 4.0 / 100), 2),
            tp5_price=round(entry * (1 + 6.0 / 100) if side == "LONG" else entry * (1 - 6.0 / 100), 2),
            tp6_price=round(entry * (1 + 10.0 / 100) if side == "LONG" else entry * (1 - 10.0 / 100), 2),
            volatility_regime=random.choice(VOLATILITY_REGIMES),
            confidence=round(random.uniform(0.6, 0.95), 2),
            status=random.choice(["pending", "filled", "cancelled", "expired"]),
            telegram_sent=random.choice([True, False]),
            created_at=now - timedelta(hours=random.randint(1, 24)),
        )
        db.add(signal)
        signals_count += 1
    
    # Sample Open Positions (3-5)
    positions_count = 0
    for i in range(random.randint(3, 5)):
        symbol = random.choice(PAIRS[:10])  # Top 10 pairs
        side = random.choice(SIDES)
        entry = round(random.uniform(100, 100000), 2)
        current = entry * (1 + random.uniform(-0.02, 0.05))
        
        position = PositionModel(
            symbol=symbol,
            side=side,
            timeframe=random.choice(TIMEFRAMES),
            entry_price=entry,
            current_price=round(current, 2),
            sl_price=round(entry * (0.97 if side == "LONG" else 1.03), 2),
            current_sl=round(entry * (0.97 if side == "LONG" else 1.03), 2),
            tp1_price=round(entry * (1.008 if side == "LONG" else 0.992), 2),
            tp2_price=round(entry * (1.015 if side == "LONG" else 0.985), 2),
            tp3_price=round(entry * (1.025 if side == "LONG" else 0.975), 2),
            tp4_price=round(entry * (1.04 if side == "LONG" else 0.96), 2),
            tp5_price=round(entry * (1.06 if side == "LONG" else 0.94), 2),
            tp6_price=round(entry * (1.10 if side == "LONG" else 0.90), 2),
            tp1_hit=random.choice([True, False]),
            tp2_hit=False,
            quantity=round(random.uniform(0.01, 1.0), 4),
            leverage=10,
            position_remaining=random.choice([100.0, 80.0, 60.0]),
            unrealized_pnl_percent=round((current - entry) / entry * 100 * (1 if side == "LONG" else -1), 2),
            status="open",
            entry_time=now - timedelta(hours=random.randint(1, 48)),
        )
        db.add(position)
        positions_count += 1
    
    # Sample Closed Trades (последние 30 дней)
    trades_count = 0
    for i in range(50):
        symbol = random.choice(PAIRS)
        side = random.choice(SIDES)
        entry = round(random.uniform(100, 100000), 2)
        is_win = random.random() < 0.7  # 70% WR
        pnl_pct = random.uniform(0.5, 5.0) if is_win else -random.uniform(1.0, 3.0)
        exit_price = entry * (1 + pnl_pct / 100) if side == "LONG" else entry * (1 - pnl_pct / 100)
        
        trade = TradeModel(
            symbol=symbol,
            side=side,
            timeframe=random.choice(TIMEFRAMES),
            entry_price=entry,
            exit_price=round(exit_price, 2),
            pnl_percent=round(pnl_pct, 2),
            pnl_usd=round(entry * 0.1 * pnl_pct / 100, 2),  # 10% of position value
            exit_reason=random.choice(["TP1", "TP2", "TP3", "TP4", "TP5", "TP6", "SL"]) if is_win else "SL",
            tp_hits=random.randint(1, 6) if is_win else 0,
            duration_minutes=random.randint(30, 2880),
            entry_time=now - timedelta(days=random.randint(1, 30)),
            exit_time=now - timedelta(days=random.randint(0, 29)),
        )
        db.add(trade)
        trades_count += 1
    
    # Sample System Logs
    logs_count = 0
    components = ["LiveEngine", "DataEngine", "TelegramBot", "APIServer", "Database"]
    levels = ["INFO", "INFO", "INFO", "WARNING", "ERROR"]  # More INFO than errors
    messages = [
        "System started successfully",
        "Connected to Binance WebSocket",
        "New signal generated",
        "Position opened",
        "TP1 hit, moving SL to BE",
        "Database backup completed",
        "Config reloaded",
        "Connection timeout, retrying...",
        "Rate limit warning",
        "API request failed, retrying",
    ]
    
    for i in range(100):
        log = SystemLogModel(
            level=random.choice(levels),
            component=random.choice(components),
            message=random.choice(messages),
            created_at=now - timedelta(minutes=random.randint(1, 1440)),
        )
        db.add(log)
        logs_count += 1
    
    db.commit()
    
    print(f"✅ Добавлено:")
    print(f"   • {signals_count} сигналов")
    print(f"   • {positions_count} открытых позиций")
    print(f"   • {trades_count} закрытых сделок")
    print(f"   • {logs_count} системных логов")


def main():
    """Главная функция инициализации."""
    print()
    print("═" * 60)
    print("  VELAS - Инициализация базы данных")
    print("═" * 60)
    print()
    
    # Create tables
    create_tables()
    
    # Open session
    db = SessionLocal()
    
    try:
        # Seed settings
        seed_settings(db)
        
        # Seed sample data
        seed_sample_data(db)
        
        print()
        print("═" * 60)
        print("  ✅ ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА")
        print("═" * 60)
        print()
        print(f"  База данных: data/velas.db")
        print()
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
