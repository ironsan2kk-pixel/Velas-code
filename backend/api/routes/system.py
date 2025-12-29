"""VELAS API - System endpoints."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.db.database import get_db
from backend.db.models import SystemLogModel, SignalModel, TradeModel
from backend.api.models import ApiResponse, SystemStatusResponse, ComponentStatus, LogEntry, SystemStatusEnum

router = APIRouter()

TRADING_STATE = {"active": True, "start_time": datetime.utcnow()}
APP_VERSION = "1.0.0"


@router.get("/status", response_model=ApiResponse[SystemStatusResponse])
async def get_system_status(db: Session = Depends(get_db)):
    uptime = int((datetime.utcnow() - TRADING_STATE["start_time"]).total_seconds())
    
    last_signal = db.query(SignalModel).order_by(desc(SignalModel.created_at)).first()
    last_trade = db.query(TradeModel).order_by(desc(TradeModel.exit_time)).first()
    
    components = [
        ComponentStatus(name="Live Engine", status=SystemStatusEnum.ONLINE if TRADING_STATE["active"] else SystemStatusEnum.OFFLINE, uptime_seconds=uptime),
        ComponentStatus(name="Data Engine", status=SystemStatusEnum.ONLINE, uptime_seconds=uptime),
        ComponentStatus(name="Telegram Bot", status=SystemStatusEnum.ONLINE, uptime_seconds=uptime),
        ComponentStatus(name="Database", status=SystemStatusEnum.ONLINE, uptime_seconds=uptime),
    ]
    
    all_online = all(c.status == SystemStatusEnum.ONLINE for c in components)
    
    return ApiResponse(data=SystemStatusResponse(
        status=SystemStatusEnum.ONLINE if all_online else SystemStatusEnum.DEGRADED,
        trading_active=TRADING_STATE["active"], uptime_seconds=uptime, version=APP_VERSION,
        components=components, last_signal_time=last_signal.created_at if last_signal else None,
        last_trade_time=last_trade.exit_time if last_trade else None,
    ))


@router.get("/logs", response_model=ApiResponse[List[LogEntry]])
async def get_system_logs(level: Optional[str] = Query(None, pattern="^(DEBUG|INFO|WARNING|ERROR)$"), component: Optional[str] = Query(None), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    query = db.query(SystemLogModel)
    if level:
        query = query.filter(SystemLogModel.level == level)
    if component:
        query = query.filter(SystemLogModel.component == component)
    
    logs = query.order_by(desc(SystemLogModel.created_at)).limit(limit).all()
    return ApiResponse(data=[LogEntry(id=log.id, level=log.level, component=log.component, message=log.message, details=log.details, created_at=log.created_at) for log in logs])


@router.post("/pause", response_model=ApiResponse[dict])
async def pause_trading():
    TRADING_STATE["active"] = False
    return ApiResponse(data={"success": True, "trading_active": False}, message="Торговля приостановлена")


@router.post("/resume", response_model=ApiResponse[dict])
async def resume_trading():
    TRADING_STATE["active"] = True
    return ApiResponse(data={"success": True, "trading_active": True}, message="Торговля возобновлена")
