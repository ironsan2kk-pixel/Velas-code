"""
VELAS Database Models - SQLAlchemy ORM модели.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base


class PositionModel(Base):
    """Модель позиции."""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    timeframe = Column(String(10), nullable=False)
    preset_id = Column(String(50), nullable=True)
    
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=True)
    
    tp1_price = Column(Float, nullable=True)
    tp2_price = Column(Float, nullable=True)
    tp3_price = Column(Float, nullable=True)
    tp4_price = Column(Float, nullable=True)
    tp5_price = Column(Float, nullable=True)
    tp6_price = Column(Float, nullable=True)
    
    sl_price = Column(Float, nullable=False)
    current_sl = Column(Float, nullable=True)
    
    tp1_hit = Column(Boolean, default=False)
    tp2_hit = Column(Boolean, default=False)
    tp3_hit = Column(Boolean, default=False)
    tp4_hit = Column(Boolean, default=False)
    tp5_hit = Column(Boolean, default=False)
    tp6_hit = Column(Boolean, default=False)
    
    quantity = Column(Float, nullable=True)
    notional_value = Column(Float, nullable=True)
    leverage = Column(Integer, default=10)
    position_remaining = Column(Float, default=100.0)
    
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_percent = Column(Float, default=0.0)
    
    status = Column(String(20), default="open", index=True)
    close_reason = Column(String(100), nullable=True)
    
    entry_time = Column(DateTime, default=datetime.utcnow)
    close_time = Column(DateTime, nullable=True)
    last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class SignalModel(Base):
    """Модель сигнала."""
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    timeframe = Column(String(10), nullable=False)
    
    entry_price = Column(Float, nullable=False)
    sl_price = Column(Float, nullable=False)
    tp1_price = Column(Float, nullable=True)
    tp2_price = Column(Float, nullable=True)
    tp3_price = Column(Float, nullable=True)
    tp4_price = Column(Float, nullable=True)
    tp5_price = Column(Float, nullable=True)
    tp6_price = Column(Float, nullable=True)
    
    preset_id = Column(String(50), nullable=True)
    volatility_regime = Column(String(10), default="normal")
    confidence = Column(Float, nullable=True)
    
    status = Column(String(20), default="pending", index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    
    telegram_sent = Column(Boolean, default=False)
    telegram_message_id = Column(Integer, nullable=True)
    
    filter_passed = Column(Boolean, default=True)
    filter_reason = Column(String(200), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class TradeModel(Base):
    """Модель закрытой сделки."""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    timeframe = Column(String(10), nullable=False)
    
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=False)
    
    pnl_percent = Column(Float, nullable=False)
    pnl_usd = Column(Float, nullable=False)
    exit_reason = Column(String(50), nullable=False)
    
    tp_hits = Column(Integer, default=0)
    duration_minutes = Column(Integer, nullable=True)
    
    entry_time = Column(DateTime, nullable=True)
    exit_time = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class SystemLogModel(Base):
    """Модель системного лога."""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False, index=True)
    component = Column(String(50), nullable=False, index=True)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class SettingModel(Base):
    """Модель настроек."""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=True)
    description = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AlertModel(Base):
    """Модель алерта/уведомления."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), nullable=False)  # info, success, warning, error
    category = Column(String(30), nullable=False)  # trading, system, portfolio, performance
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=True)
    read = Column(Boolean, default=False)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class PresetModel(Base):
    """Модель пресета торговых параметров."""
    __tablename__ = "presets"

    id = Column(Integer, primary_key=True, index=True)
    preset_id = Column(String(100), unique=True, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)
    volatility_regime = Column(String(20), nullable=False)

    # VELAS indicator parameters
    i1 = Column(Integer, default=20)
    i2 = Column(Integer, default=35)
    i3 = Column(Integer, default=10)
    i4 = Column(Integer, default=15)
    i5 = Column(Integer, default=12)

    # Take profits (%)
    tp1 = Column(Float, default=1.0)
    tp2 = Column(Float, default=2.0)
    tp3 = Column(Float, default=3.0)
    tp4 = Column(Float, default=4.0)
    tp5 = Column(Float, default=7.5)
    tp6 = Column(Float, default=14.0)

    # Stop loss (%)
    sl = Column(Float, default=8.5)

    # TP distribution
    tp_distribution = Column(JSON, default=[10.0, 10.0, 10.0, 20.0, 25.0, 25.0])

    # Filters
    filters = Column(JSON, default=["volume", "rsi", "adx"])

    enabled = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
