"""
VELAS API - Analytics Routes
"""

from fastapi import APIRouter, Query
from typing import Literal
from datetime import datetime, timedelta
import random

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


def generate_equity_curve(period: str) -> list[EquityPoint]:
    """Generate equity curve data."""
    
    periods_map = {
        "1w": (7, timedelta(days=1)),
        "1m": (30, timedelta(days=1)),
        "3m": (90, timedelta(days=1)),
        "6m": (180, timedelta(days=1)),
        "1y": (365, timedelta(days=1)),
    }
    
    count, delta = periods_map.get(period, (30, timedelta(days=1)))
    
    points = []
    equity = 10000.0
    max_equity = equity
    
    now = datetime.utcnow()
    
    for i in range(count):
        timestamp = now - (count - i - 1) * delta
        
        # Random walk with slight upward bias
        change = random.gauss(0.003, 0.02)
        equity *= (1 + change)
        max_equity = max(max_equity, equity)
        drawdown = (max_equity - equity) / max_equity * 100
        
        points.append(EquityPoint(
            timestamp=timestamp.isoformat(),
            equity=round(equity, 2),
            drawdown=round(drawdown, 2),
        ))
    
    return points


@router.get("/equity")
async def get_equity_curve(
    period: Literal["1w", "1m", "3m", "6m", "1y"] = Query(default="1m")
) -> ApiResponse:
    """Get equity curve data."""
    
    curve = generate_equity_curve(period)
    return ApiResponse(data=[p.model_dump() for p in curve])


@router.get("/drawdown")
async def get_drawdown_chart(
    period: Literal["1w", "1m", "3m", "6m", "1y"] = Query(default="1m")
) -> ApiResponse:
    """Get drawdown chart data."""
    
    curve = generate_equity_curve(period)
    # Extract only drawdown data
    drawdown_data = [
        {"timestamp": p.timestamp, "drawdown": p.drawdown}
        for p in curve
    ]
    return ApiResponse(data=drawdown_data)


@router.get("/monthly")
async def get_monthly_stats() -> ApiResponse:
    """Get monthly statistics."""
    
    stats = []
    now = datetime.utcnow()
    
    for i in range(12):
        date = now - timedelta(days=30 * i)
        
        trades = random.randint(20, 60)
        win_rate = random.uniform(60, 80)
        pnl = random.uniform(-500, 2000)
        
        stats.append(MonthlyStats(
            month=date.strftime("%B"),
            year=date.year,
            trades=trades,
            win_rate=round(win_rate, 1),
            pnl=round(pnl, 2),
            pnl_percent=round(pnl / 100, 2),  # Simplified
            best_day=round(random.uniform(100, 500), 2),
            worst_day=round(random.uniform(-300, -50), 2),
            max_drawdown=round(random.uniform(3, 12), 1),
        ))
    
    return ApiResponse(data=[s.model_dump() for s in stats])


@router.get("/pairs")
async def get_pair_analytics() -> ApiResponse:
    """Get per-pair analytics."""
    
    stats = []
    
    for symbol in SYMBOLS:
        trades = random.randint(10, 50)
        win_rate = random.uniform(55, 85)
        pnl = random.uniform(-200, 1500)
        
        stats.append(PairStats(
            symbol=symbol,
            trades=trades,
            win_rate=round(win_rate, 1),
            pnl=round(pnl, 2),
            avg_pnl=round(pnl / trades, 2),
            profit_factor=round(random.uniform(1.2, 3.0), 2),
            sharpe=round(random.uniform(0.8, 2.5), 2),
            max_drawdown=round(random.uniform(3, 15), 1),
        ))
    
    # Sort by PnL
    stats.sort(key=lambda x: x.pnl, reverse=True)
    
    return ApiResponse(data=[s.model_dump() for s in stats])


@router.get("/correlation")
async def get_correlation_matrix() -> ApiResponse:
    """Get correlation matrix for all pairs."""
    
    n = len(SYMBOLS)
    matrix = []
    
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(1.0)
            elif j < i:
                row.append(matrix[j][i])  # Symmetric
            else:
                # Generate realistic correlations
                # Same sector = higher correlation
                corr = random.uniform(0.3, 0.95)
                row.append(round(corr, 2))
        matrix.append(row)
    
    result = CorrelationMatrix(
        symbols=SYMBOLS,
        matrix=matrix,
    )
    
    return ApiResponse(data=result.model_dump())
