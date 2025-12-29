"""
VELAS API - Backtest Routes
"""

from fastapi import APIRouter, Query, HTTPException, Path
from datetime import datetime, timedelta
import random
import uuid

from ..models import (
    ApiResponse,
    BacktestConfig,
    BacktestResult,
    EquityPoint,
    Timeframe,
)

router = APIRouter()

# In-memory storage for backtests
_backtests: dict[str, BacktestResult] = {}


def generate_backtest_result(config: BacktestConfig) -> BacktestResult:
    """Generate backtest result."""
    
    backtest_id = str(uuid.uuid4())[:8]
    
    # Generate equity curve
    start = datetime.fromisoformat(config.start_date)
    end = datetime.fromisoformat(config.end_date)
    days = (end - start).days
    
    equity_curve = []
    equity = config.initial_capital
    max_equity = equity
    
    for i in range(days):
        date = start + timedelta(days=i)
        
        change = random.gauss(0.002, 0.015)
        equity *= (1 + change)
        max_equity = max(max_equity, equity)
        drawdown = (max_equity - equity) / max_equity * 100
        
        equity_curve.append(EquityPoint(
            timestamp=date.isoformat(),
            equity=round(equity, 2),
            drawdown=round(drawdown, 2),
        ))
    
    # Calculate metrics
    total_trades = random.randint(30, 150)
    win_rate = random.uniform(60, 80)
    total_pnl = equity - config.initial_capital
    pnl_percent = (equity / config.initial_capital - 1) * 100
    
    result = BacktestResult(
        id=backtest_id,
        config=config,
        status="completed",
        progress=100,
        total_trades=total_trades,
        win_rate=round(win_rate, 1),
        total_pnl=round(total_pnl, 2),
        profit_factor=round(random.uniform(1.3, 2.8), 2),
        sharpe_ratio=round(random.uniform(0.8, 2.2), 2),
        max_drawdown=round(max(p.drawdown for p in equity_curve), 1),
        equity_curve=equity_curve,
        created_at=datetime.utcnow().isoformat(),
        completed_at=datetime.utcnow().isoformat(),
    )
    
    return result


@router.post("/run")
async def run_backtest(config: BacktestConfig) -> ApiResponse:
    """Start a backtest."""
    
    # Validate dates
    try:
        start = datetime.fromisoformat(config.start_date)
        end = datetime.fromisoformat(config.end_date)
        
        if end <= start:
            raise HTTPException(status_code=400, detail="End date must be after start date")
        
        if (end - start).days < 7:
            raise HTTPException(status_code=400, detail="Backtest period must be at least 7 days")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Run backtest (in real app this would be async)
    result = generate_backtest_result(config)
    _backtests[result.id] = result
    
    return ApiResponse(data={"id": result.id})


@router.get("/status/{backtest_id}")
async def get_backtest_status(backtest_id: str = Path(...)) -> ApiResponse:
    """Get backtest status."""
    
    if backtest_id not in _backtests:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    result = _backtests[backtest_id]
    return ApiResponse(data=result.model_dump())


@router.get("/results")
async def get_backtest_results() -> ApiResponse:
    """Get all backtest results."""
    
    results = list(_backtests.values())
    
    # Return without full equity curve for list view
    simplified = []
    for r in results:
        data = r.model_dump()
        data["equity_curve"] = []  # Don't include full curve in list
        simplified.append(data)
    
    return ApiResponse(data=simplified)


@router.get("/results/{backtest_id}")
async def get_backtest_result(backtest_id: str = Path(...)) -> ApiResponse:
    """Get single backtest result with full data."""
    
    if backtest_id not in _backtests:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    return ApiResponse(data=_backtests[backtest_id].model_dump())
