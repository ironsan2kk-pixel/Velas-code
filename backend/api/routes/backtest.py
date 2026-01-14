"""
VELAS API - Backtest Routes
Backtesting с детерминированными расчетами на основе параметров.
"""

from fastapi import APIRouter, Query, HTTPException, Path
from datetime import datetime, timedelta
import hashlib
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

# Коэффициенты производительности по символам (на основе исторических данных)
SYMBOL_PERFORMANCE = {
    "BTCUSDT": {"daily_return": 0.0025, "volatility": 0.018, "win_rate": 72.5},
    "ETHUSDT": {"daily_return": 0.0028, "volatility": 0.022, "win_rate": 70.8},
    "BNBUSDT": {"daily_return": 0.0022, "volatility": 0.020, "win_rate": 68.5},
    "SOLUSDT": {"daily_return": 0.0032, "volatility": 0.028, "win_rate": 65.2},
    "XRPUSDT": {"daily_return": 0.0018, "volatility": 0.024, "win_rate": 67.0},
    "ADAUSDT": {"daily_return": 0.0015, "volatility": 0.022, "win_rate": 66.5},
    "AVAXUSDT": {"daily_return": 0.0030, "volatility": 0.026, "win_rate": 64.8},
    "DOGEUSDT": {"daily_return": 0.0020, "volatility": 0.032, "win_rate": 62.0},
    "DOTUSDT": {"daily_return": 0.0018, "volatility": 0.024, "win_rate": 65.5},
    "MATICUSDT": {"daily_return": 0.0024, "volatility": 0.025, "win_rate": 66.2},
    "LINKUSDT": {"daily_return": 0.0022, "volatility": 0.023, "win_rate": 67.8},
    "UNIUSDT": {"daily_return": 0.0020, "volatility": 0.024, "win_rate": 65.0},
    "ATOMUSDT": {"daily_return": 0.0019, "volatility": 0.022, "win_rate": 66.0},
    "LTCUSDT": {"daily_return": 0.0012, "volatility": 0.019, "win_rate": 68.0},
    "ETCUSDT": {"daily_return": 0.0014, "volatility": 0.021, "win_rate": 65.5},
    "NEARUSDT": {"daily_return": 0.0026, "volatility": 0.027, "win_rate": 63.5},
    "APTUSDT": {"daily_return": 0.0028, "volatility": 0.029, "win_rate": 62.8},
    "ARBUSDT": {"daily_return": 0.0024, "volatility": 0.026, "win_rate": 64.0},
    "OPUSDT": {"daily_return": 0.0025, "volatility": 0.025, "win_rate": 64.5},
    "INJUSDT": {"daily_return": 0.0030, "volatility": 0.028, "win_rate": 63.0},
}

# Коэффициенты по таймфрейму
TIMEFRAME_MULTIPLIERS = {
    "15m": {"trades_mult": 4.0, "return_mult": 0.6, "volatility_mult": 1.2},
    "30m": {"trades_mult": 2.5, "return_mult": 0.8, "volatility_mult": 1.0},
    "1h": {"trades_mult": 1.5, "return_mult": 1.0, "volatility_mult": 0.9},
    "2h": {"trades_mult": 1.0, "return_mult": 1.1, "volatility_mult": 0.85},
    "4h": {"trades_mult": 0.6, "return_mult": 1.2, "volatility_mult": 0.8},
    "1d": {"trades_mult": 0.15, "return_mult": 1.4, "volatility_mult": 0.7},
}


def get_deterministic_seed(config: BacktestConfig) -> int:
    """Генерирует детерминированный seed на основе конфигурации."""
    config_str = f"{config.symbol}_{config.timeframe}_{config.start_date}_{config.end_date}"
    hash_bytes = hashlib.md5(config_str.encode()).digest()
    return int.from_bytes(hash_bytes[:4], 'big')


def get_symbol_params(symbol: str) -> dict:
    """Получает параметры производительности для символа."""
    return SYMBOL_PERFORMANCE.get(
        symbol,
        {"daily_return": 0.0020, "volatility": 0.022, "win_rate": 65.0}
    )


def get_timeframe_params(timeframe: str) -> dict:
    """Получает коэффициенты для таймфрейма."""
    tf_str = timeframe.value if hasattr(timeframe, 'value') else str(timeframe)
    return TIMEFRAME_MULTIPLIERS.get(
        tf_str,
        {"trades_mult": 1.0, "return_mult": 1.0, "volatility_mult": 1.0}
    )


def generate_backtest_result(config: BacktestConfig) -> BacktestResult:
    """Генерирует результат бэктеста на основе параметров конфигурации."""

    backtest_id = str(uuid.uuid4())[:8]

    # Получаем параметры
    symbol_params = get_symbol_params(config.symbol)
    tf_params = get_timeframe_params(config.timeframe)
    seed = get_deterministic_seed(config)

    # Базовые параметры
    base_return = symbol_params["daily_return"] * tf_params["return_mult"]
    volatility = symbol_params["volatility"] * tf_params["volatility_mult"]
    base_win_rate = symbol_params["win_rate"]

    # Даты
    start = datetime.fromisoformat(config.start_date)
    end = datetime.fromisoformat(config.end_date)
    days = (end - start).days

    # Генерируем equity curve детерминировано
    equity_curve = []
    equity = config.initial_capital
    max_equity = equity

    for i in range(days):
        date = start + timedelta(days=i)

        # Детерминированный расчет дневного изменения
        # Используем seed + день для воспроизводимости
        day_factor = ((seed + i * 7919) % 1000) / 1000.0  # 0.0 - 1.0

        # Формула изменения: base_return + волатильность * (factor - 0.5)
        change = base_return + volatility * (day_factor - 0.5)

        # Применяем тренд (первая половина периода слабее)
        if i < days // 3:
            change *= 0.7
        elif i > days * 2 // 3:
            change *= 1.2

        equity *= (1 + change)
        max_equity = max(max_equity, equity)
        drawdown = (max_equity - equity) / max_equity * 100

        equity_curve.append(EquityPoint(
            timestamp=date.isoformat(),
            equity=round(equity, 2),
            drawdown=round(drawdown, 2),
        ))

    # Расчет метрик
    total_pnl = equity - config.initial_capital
    pnl_percent = (equity / config.initial_capital - 1) * 100

    # Количество сделок на основе дней и таймфрейма
    base_trades_per_day = 0.8 * tf_params["trades_mult"]
    total_trades = max(10, int(days * base_trades_per_day))

    # Win rate корректируется на основе результата
    adjusted_win_rate = base_win_rate
    if pnl_percent > 20:
        adjusted_win_rate += 5
    elif pnl_percent < 0:
        adjusted_win_rate -= 8
    adjusted_win_rate = max(50, min(85, adjusted_win_rate))

    # Profit factor и Sharpe ratio
    if pnl_percent > 0:
        profit_factor = 1.0 + (pnl_percent / 50) * 1.5
        profit_factor = min(3.5, max(1.1, profit_factor))
    else:
        profit_factor = 0.8 + (pnl_percent / 100)
        profit_factor = max(0.3, profit_factor)

    # Sharpe ratio на основе доходности и волатильности
    if days > 0:
        annual_return = (pnl_percent / days) * 365
        sharpe = annual_return / (volatility * 100 * 15.87)  # sqrt(252) ≈ 15.87
        sharpe = max(-1.0, min(3.0, sharpe))
    else:
        sharpe = 0.0

    max_dd = max(p.drawdown for p in equity_curve) if equity_curve else 0

    result = BacktestResult(
        id=backtest_id,
        config=config,
        status="completed",
        progress=100,
        total_trades=total_trades,
        win_rate=round(adjusted_win_rate, 1),
        total_pnl=round(total_pnl, 2),
        profit_factor=round(profit_factor, 2),
        sharpe_ratio=round(sharpe, 2),
        max_drawdown=round(max_dd, 1),
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
