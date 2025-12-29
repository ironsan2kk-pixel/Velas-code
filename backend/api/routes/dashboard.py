"""VELAS API - Dashboard endpoints."""

from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import PositionModel, SignalModel, TradeModel
from backend.api.models import ApiResponse, DashboardSummary, DashboardMetrics, EquityPoint, SystemStatusEnum

router = APIRouter()


@router.get("/summary", response_model=ApiResponse[DashboardSummary])
async def get_dashboard_summary(db: Session = Depends(get_db)):
    open_positions = db.query(PositionModel).filter(PositionModel.status == "open").count()
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    signals_today = db.query(SignalModel).filter(SignalModel.created_at >= today_start).count()
    
    trades = db.query(TradeModel).all()
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t.pnl_percent > 0])
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    total_pnl = sum(t.pnl_usd for t in trades)
    
    initial_balance = 10000.0
    total_pnl_percent = (total_pnl / initial_balance * 100) if initial_balance > 0 else 0
    
    open_pos = db.query(PositionModel).filter(PositionModel.status == "open").all()
    portfolio_heat = 0.0
    for pos in open_pos:
        if pos.entry_price and pos.current_sl:
            if pos.side == "LONG":
                risk = (pos.entry_price - pos.current_sl) / pos.entry_price * 100
            else:
                risk = (pos.current_sl - pos.entry_price) / pos.entry_price * 100
            portfolio_heat += abs(risk) * (pos.position_remaining / 100)
    
    return ApiResponse(data=DashboardSummary(
        status=SystemStatusEnum.ONLINE,
        balance=initial_balance + total_pnl,
        total_pnl=round(total_pnl, 2),
        total_pnl_percent=round(total_pnl_percent, 2),
        open_positions=open_positions,
        max_positions=5,
        signals_today=signals_today,
        win_rate=round(win_rate, 1),
        portfolio_heat=round(portfolio_heat, 2),
        max_heat=15.0,
    ))


@router.get("/metrics", response_model=ApiResponse[DashboardMetrics])
async def get_dashboard_metrics(db: Session = Depends(get_db)):
    trades = db.query(TradeModel).all()
    
    if not trades:
        return ApiResponse(data=DashboardMetrics(profit_factor=0.0, sharpe_ratio=0.0, max_drawdown=0.0, total_trades=0))
    
    wins = [t.pnl_usd for t in trades if t.pnl_usd > 0]
    losses = [abs(t.pnl_usd) for t in trades if t.pnl_usd < 0]
    
    total_wins = sum(wins) if wins else 0
    total_losses = sum(losses) if losses else 0
    profit_factor = (total_wins / total_losses) if total_losses > 0 else total_wins
    
    returns = [t.pnl_percent for t in trades]
    avg_return = sum(returns) / len(returns) if returns else 0
    if len(returns) > 1:
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = variance ** 0.5
        sharpe = (avg_return / std_dev) if std_dev > 0 else 0
    else:
        sharpe = 0
    
    equity = 10000.0
    peak = equity
    max_dd = 0.0
    for trade in sorted(trades, key=lambda t: t.exit_time or t.created_at):
        equity += trade.pnl_usd
        peak = max(peak, equity)
        dd = (peak - equity) / peak * 100 if peak > 0 else 0
        max_dd = max(max_dd, dd)
    
    durations = [t.duration_minutes for t in trades if t.duration_minutes]
    avg_duration = sum(durations) / len(durations) if durations else None
    
    pair_pnl = {}
    for trade in trades:
        if trade.symbol not in pair_pnl:
            pair_pnl[trade.symbol] = 0
        pair_pnl[trade.symbol] += trade.pnl_usd
    
    best_pair = max(pair_pnl, key=pair_pnl.get) if pair_pnl else None
    worst_pair = min(pair_pnl, key=pair_pnl.get) if pair_pnl else None
    
    return ApiResponse(data=DashboardMetrics(
        profit_factor=round(profit_factor, 2),
        sharpe_ratio=round(sharpe, 2),
        max_drawdown=round(max_dd, 2),
        total_trades=len(trades),
        avg_trade_duration=round(avg_duration, 0) if avg_duration else None,
        best_pair=best_pair,
        worst_pair=worst_pair,
    ))


@router.get("/chart", response_model=ApiResponse[List[EquityPoint]])
async def get_dashboard_chart(period: str = Query("1w", pattern="^(1d|1w|1m|3m)$"), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    period_map = {"1d": timedelta(days=1), "1w": timedelta(weeks=1), "1m": timedelta(days=30), "3m": timedelta(days=90)}
    start_date = now - period_map.get(period, timedelta(weeks=1))
    
    trades = db.query(TradeModel).filter(TradeModel.exit_time >= start_date).order_by(TradeModel.exit_time).all()
    
    points = []
    equity = 10000.0
    peak = equity
    
    points.append(EquityPoint(timestamp=start_date, equity=equity, drawdown=0.0))
    
    for trade in trades:
        equity += trade.pnl_usd
        peak = max(peak, equity)
        drawdown = ((peak - equity) / peak * 100) if peak > 0 else 0
        points.append(EquityPoint(timestamp=trade.exit_time or trade.created_at, equity=round(equity, 2), drawdown=round(drawdown, 2)))
    
    if trades:
        points.append(EquityPoint(timestamp=now, equity=round(equity, 2), drawdown=round(((peak - equity) / peak * 100) if peak > 0 else 0, 2)))
    
    return ApiResponse(data=points)
