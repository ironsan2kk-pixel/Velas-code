"""VELAS API - History endpoints."""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import math
import io
import csv

from backend.db.database import get_db
from backend.db.models import TradeModel
from backend.api.models import ApiResponse, PaginatedResponse, TradeHistoryResponse, HistoryStats, SideEnum, TimeframeEnum

router = APIRouter()


def trade_to_response(trade: TradeModel) -> TradeHistoryResponse:
    return TradeHistoryResponse(
        id=trade.id, position_id=trade.position_id, symbol=trade.symbol, side=SideEnum(trade.side),
        timeframe=TimeframeEnum(trade.timeframe), entry_price=trade.entry_price, exit_price=trade.exit_price,
        pnl_percent=trade.pnl_percent, pnl_usd=trade.pnl_usd, exit_reason=trade.exit_reason,
        tp_hits=trade.tp_hits, duration_minutes=trade.duration_minutes,
        entry_time=trade.entry_time, exit_time=trade.exit_time, created_at=trade.created_at,
    )


@router.get("", response_model=PaginatedResponse[TradeHistoryResponse])
async def get_history(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), symbol: Optional[str] = Query(None), side: Optional[str] = Query(None, pattern="^(LONG|SHORT)$"), db: Session = Depends(get_db)):
    query = db.query(TradeModel)
    if symbol:
        query = query.filter(TradeModel.symbol == symbol.upper())
    if side:
        query = query.filter(TradeModel.side == side)
    
    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    trades = query.order_by(TradeModel.exit_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(data=[trade_to_response(t) for t in trades], total=total, page=page, page_size=page_size, total_pages=total_pages)


@router.get("/stats", response_model=ApiResponse[HistoryStats])
async def get_history_stats(period: Optional[str] = Query(None, pattern="^(7d|30d|90d|all)$"), db: Session = Depends(get_db)):
    query = db.query(TradeModel)
    
    if period and period != "all":
        period_map = {"7d": timedelta(days=7), "30d": timedelta(days=30), "90d": timedelta(days=90)}
        start_date = datetime.utcnow() - period_map[period]
        query = query.filter(TradeModel.exit_time >= start_date)
    
    trades = query.all()
    
    if not trades:
        return ApiResponse(data=HistoryStats(total_trades=0, winning_trades=0, losing_trades=0, win_rate=0.0, total_pnl=0.0, avg_pnl=0.0, max_win=0.0, max_loss=0.0, profit_factor=0.0))
    
    winning_trades = [t for t in trades if t.pnl_usd > 0]
    losing_trades = [t for t in trades if t.pnl_usd < 0]
    
    total_pnl = sum(t.pnl_usd for t in trades)
    avg_pnl = total_pnl / len(trades)
    max_win = max((t.pnl_usd for t in trades), default=0)
    max_loss = min((t.pnl_usd for t in trades), default=0)
    
    total_wins = sum(t.pnl_usd for t in winning_trades)
    total_losses = abs(sum(t.pnl_usd for t in losing_trades))
    profit_factor = (total_wins / total_losses) if total_losses > 0 else total_wins
    
    durations = [t.duration_minutes for t in trades if t.duration_minutes]
    avg_duration = sum(durations) / len(durations) if durations else None
    
    return ApiResponse(data=HistoryStats(
        total_trades=len(trades), winning_trades=len(winning_trades), losing_trades=len(losing_trades),
        win_rate=round(len(winning_trades) / len(trades) * 100, 1), total_pnl=round(total_pnl, 2),
        avg_pnl=round(avg_pnl, 2), max_win=round(max_win, 2), max_loss=round(max_loss, 2),
        profit_factor=round(profit_factor, 2), avg_duration_minutes=round(avg_duration, 0) if avg_duration else None,
    ))


@router.get("/export")
async def export_history(format: str = Query("csv", pattern="^(csv)$"), db: Session = Depends(get_db)):
    trades = db.query(TradeModel).order_by(TradeModel.exit_time.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Symbol", "Side", "Timeframe", "Entry Price", "Exit Price", "PnL %", "PnL USD", "Exit Reason", "TP Hits", "Duration (min)", "Entry Time", "Exit Time"])
    
    for trade in trades:
        writer.writerow([trade.id, trade.symbol, trade.side, trade.timeframe, trade.entry_price, trade.exit_price, round(trade.pnl_percent, 2), round(trade.pnl_usd, 2), trade.exit_reason, trade.tp_hits, trade.duration_minutes, trade.entry_time.isoformat() if trade.entry_time else "", trade.exit_time.isoformat() if trade.exit_time else ""])
    
    output.seek(0)
    return StreamingResponse(io.BytesIO(output.getvalue().encode('utf-8')), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=velas_history.csv"})
