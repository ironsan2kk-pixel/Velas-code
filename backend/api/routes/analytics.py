"""
VELAS API - Analytics Routes

Реальная аналитика из базы данных.
"""

from fastapi import APIRouter, Query, Depends
from typing import Literal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.db.database import get_db
from backend.db.models import TradeModel, PositionModel

from ..models import (
    ApiResponse,
    EquityPoint,
    MonthlyStats,
    PairStats,
    CorrelationMatrix,
)

router = APIRouter()


SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT",
    "LINKUSDT", "UNIUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT",
    "NEARUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "INJUSDT",
]


def get_period_start(period: str) -> datetime:
    """Получить начало периода."""
    now = datetime.utcnow()
    periods_map = {
        "1w": timedelta(days=7),
        "1m": timedelta(days=30),
        "3m": timedelta(days=90),
        "6m": timedelta(days=180),
        "1y": timedelta(days=365),
    }
    delta = periods_map.get(period, timedelta(days=30))
    return now - delta


@router.get("/equity")
async def get_equity_curve(
    period: Literal["1w", "1m", "3m", "6m", "1y"] = Query(default="1m"),
    db: Session = Depends(get_db)
) -> ApiResponse:
    """Get equity curve data from real trades."""
    
    period_start = get_period_start(period)
    
    # Получаем все сделки за период
    trades = db.query(TradeModel).filter(
        TradeModel.created_at >= period_start
    ).order_by(TradeModel.created_at.asc()).all()
    
    if not trades:
        # Если нет данных - возвращаем пустую кривую
        return ApiResponse(data=[])
    
    # Строим equity curve
    points = []
    initial_balance = 10000.0
    equity = initial_balance
    max_equity = equity
    
    for trade in trades:
        equity += trade.pnl_usd
        max_equity = max(max_equity, equity)
        drawdown = ((max_equity - equity) / max_equity * 100) if max_equity > 0 else 0
        
        points.append(EquityPoint(
            timestamp=trade.created_at.isoformat() if trade.created_at else datetime.utcnow().isoformat(),
            equity=round(equity, 2),
            drawdown=round(drawdown, 2),
        ))
    
    return ApiResponse(data=[p.model_dump() for p in points])


@router.get("/drawdown")
async def get_drawdown_chart(
    period: Literal["1w", "1m", "3m", "6m", "1y"] = Query(default="1m"),
    db: Session = Depends(get_db)
) -> ApiResponse:
    """Get drawdown chart data."""
    
    period_start = get_period_start(period)
    
    trades = db.query(TradeModel).filter(
        TradeModel.created_at >= period_start
    ).order_by(TradeModel.created_at.asc()).all()
    
    if not trades:
        return ApiResponse(data=[])
    
    # Строим drawdown curve
    points = []
    equity = 10000.0
    max_equity = equity
    
    for trade in trades:
        equity += trade.pnl_usd
        max_equity = max(max_equity, equity)
        drawdown = ((max_equity - equity) / max_equity * 100) if max_equity > 0 else 0
        
        points.append({
            "timestamp": trade.created_at.isoformat() if trade.created_at else datetime.utcnow().isoformat(),
            "drawdown": round(drawdown, 2),
        })
    
    return ApiResponse(data=points)


@router.get("/monthly")
async def get_monthly_stats(db: Session = Depends(get_db)) -> ApiResponse:
    """Get monthly statistics from real trades."""
    
    stats = []
    now = datetime.utcnow()
    
    for i in range(12):
        # Определяем месяц
        month_date = now - timedelta(days=30 * i)
        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if month_date.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        
        # Получаем сделки за месяц
        trades = db.query(TradeModel).filter(
            TradeModel.created_at >= month_start,
            TradeModel.created_at < month_end
        ).all()
        
        if not trades:
            continue
        
        total_trades = len(trades)
        winners = [t for t in trades if t.pnl_usd > 0]
        win_rate = (len(winners) / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = sum(t.pnl_usd for t in trades)
        pnls = [t.pnl_usd for t in trades]
        
        best_day = max(pnls) if pnls else 0
        worst_day = min(pnls) if pnls else 0
        
        # Max drawdown за месяц
        equity = 10000.0
        max_equity = equity
        max_dd = 0
        for t in sorted(trades, key=lambda x: x.created_at or datetime.min):
            equity += t.pnl_usd
            max_equity = max(max_equity, equity)
            dd = ((max_equity - equity) / max_equity * 100) if max_equity > 0 else 0
            max_dd = max(max_dd, dd)
        
        stats.append(MonthlyStats(
            month=month_start.strftime("%B"),
            year=month_start.year,
            trades=total_trades,
            win_rate=round(win_rate, 1),
            pnl=round(total_pnl, 2),
            pnl_percent=round(total_pnl / 100, 2),  # От начального баланса
            best_day=round(best_day, 2),
            worst_day=round(worst_day, 2),
            max_drawdown=round(max_dd, 1),
        ))
    
    # Сортируем по дате (новые первые)
    stats.reverse()
    
    return ApiResponse(data=[s.model_dump() for s in stats])


@router.get("/pairs")
async def get_pair_analytics(db: Session = Depends(get_db)) -> ApiResponse:
    """Get per-pair analytics from real trades."""
    
    stats = []
    
    for symbol in SYMBOLS:
        trades = db.query(TradeModel).filter(
            TradeModel.symbol == symbol
        ).all()
        
        if not trades:
            stats.append(PairStats(
                symbol=symbol,
                trades=0,
                win_rate=0.0,
                pnl=0.0,
                avg_pnl=0.0,
                profit_factor=0.0,
                sharpe=0.0,
                max_drawdown=0.0,
            ))
            continue
        
        total_trades = len(trades)
        winners = [t for t in trades if t.pnl_usd > 0]
        losers = [t for t in trades if t.pnl_usd < 0]
        
        win_rate = (len(winners) / total_trades * 100) if total_trades > 0 else 0
        total_pnl = sum(t.pnl_usd for t in trades)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        # Profit Factor
        total_wins = sum(t.pnl_usd for t in winners) if winners else 0
        total_losses = abs(sum(t.pnl_usd for t in losers)) if losers else 0
        profit_factor = (total_wins / total_losses) if total_losses > 0 else total_wins
        
        # Sharpe Ratio (упрощённый)
        returns = [t.pnl_percent for t in trades if t.pnl_percent is not None]
        if len(returns) > 1:
            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
            std_dev = variance ** 0.5
            sharpe = (avg_return / std_dev) if std_dev > 0 else 0
        else:
            sharpe = 0
        
        # Max Drawdown
        equity = 10000.0
        max_equity = equity
        max_dd = 0
        for t in sorted(trades, key=lambda x: x.created_at or datetime.min):
            equity += t.pnl_usd
            max_equity = max(max_equity, equity)
            dd = ((max_equity - equity) / max_equity * 100) if max_equity > 0 else 0
            max_dd = max(max_dd, dd)
        
        stats.append(PairStats(
            symbol=symbol,
            trades=total_trades,
            win_rate=round(win_rate, 1),
            pnl=round(total_pnl, 2),
            avg_pnl=round(avg_pnl, 2),
            profit_factor=round(profit_factor, 2),
            sharpe=round(sharpe, 2),
            max_drawdown=round(max_dd, 1),
        ))
    
    # Сортируем по PnL (лучшие первые)
    stats.sort(key=lambda x: x.pnl, reverse=True)
    
    return ApiResponse(data=[s.model_dump() for s in stats])


@router.get("/correlation")
async def get_correlation_matrix(db: Session = Depends(get_db)) -> ApiResponse:
    """Get correlation matrix for all pairs.
    
    Корреляция рассчитывается на основе дневных P&L.
    """
    
    # Получаем все сделки за последние 90 дней
    period_start = datetime.utcnow() - timedelta(days=90)
    
    trades = db.query(TradeModel).filter(
        TradeModel.created_at >= period_start
    ).all()
    
    if not trades:
        # Возвращаем единичную матрицу
        n = len(SYMBOLS)
        matrix = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        return ApiResponse(data=CorrelationMatrix(symbols=SYMBOLS, matrix=matrix).model_dump())
    
    # Группируем PnL по символам и датам
    from collections import defaultdict
    
    daily_pnl = defaultdict(lambda: defaultdict(float))
    
    for trade in trades:
        if trade.created_at:
            date_key = trade.created_at.strftime("%Y-%m-%d")
            daily_pnl[trade.symbol][date_key] += trade.pnl_usd
    
    # Получаем все уникальные даты
    all_dates = set()
    for symbol_data in daily_pnl.values():
        all_dates.update(symbol_data.keys())
    all_dates = sorted(all_dates)
    
    # Строим матрицу корреляций
    n = len(SYMBOLS)
    matrix = [[0.0] * n for _ in range(n)]
    
    for i, sym1 in enumerate(SYMBOLS):
        for j, sym2 in enumerate(SYMBOLS):
            if i == j:
                matrix[i][j] = 1.0
            elif j < i:
                matrix[i][j] = matrix[j][i]  # Симметричная
            else:
                # Вычисляем корреляцию Пирсона
                pnl1 = [daily_pnl[sym1].get(d, 0) for d in all_dates]
                pnl2 = [daily_pnl[sym2].get(d, 0) for d in all_dates]
                
                if len(all_dates) < 2:
                    corr = 0.0
                else:
                    mean1 = sum(pnl1) / len(pnl1)
                    mean2 = sum(pnl2) / len(pnl2)
                    
                    numerator = sum((a - mean1) * (b - mean2) for a, b in zip(pnl1, pnl2))
                    denom1 = sum((a - mean1) ** 2 for a in pnl1) ** 0.5
                    denom2 = sum((b - mean2) ** 2 for b in pnl2) ** 0.5
                    
                    if denom1 > 0 and denom2 > 0:
                        corr = numerator / (denom1 * denom2)
                    else:
                        corr = 0.0
                
                matrix[i][j] = round(corr, 2)
    
    return ApiResponse(data=CorrelationMatrix(symbols=SYMBOLS, matrix=matrix).model_dump())
