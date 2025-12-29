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
