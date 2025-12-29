"""
VELAS API - Pairs Routes
"""

from fastapi import APIRouter, Query, HTTPException, Path
from typing import Literal
from datetime import datetime, timedelta
import random

from ..models import (
    ApiResponse,
    Pair,
    PairDetail,
    OHLCV,
    Signal,
    Side,
    Timeframe,
    VolatilityRegime,
    SignalStatus,
)

router = APIRouter()


# 20 trading pairs
PAIRS_CONFIG = [
    {"symbol": "BTCUSDT", "name": "Bitcoin", "sector": "Major"},
    {"symbol": "ETHUSDT", "name": "Ethereum", "sector": "Major"},
    {"symbol": "BNBUSDT", "name": "BNB", "sector": "Exchange"},
    {"symbol": "SOLUSDT", "name": "Solana", "sector": "Layer1"},
    {"symbol": "XRPUSDT", "name": "XRP", "sector": "Legacy"},
    {"symbol": "ADAUSDT", "name": "Cardano", "sector": "Legacy"},
    {"symbol": "AVAXUSDT", "name": "Avalanche", "sector": "Layer1"},
    {"symbol": "DOGEUSDT", "name": "Dogecoin", "sector": "Meme"},
    {"symbol": "DOTUSDT", "name": "Polkadot", "sector": "Layer1"},
    {"symbol": "MATICUSDT", "name": "Polygon", "sector": "Layer2"},
    {"symbol": "LINKUSDT", "name": "Chainlink", "sector": "DeFi"},
    {"symbol": "UNIUSDT", "name": "Uniswap", "sector": "DeFi"},
    {"symbol": "ATOMUSDT", "name": "Cosmos", "sector": "Layer1"},
    {"symbol": "LTCUSDT", "name": "Litecoin", "sector": "Legacy"},
    {"symbol": "ETCUSDT", "name": "Ethereum Classic", "sector": "Legacy"},
    {"symbol": "NEARUSDT", "name": "NEAR Protocol", "sector": "Layer1"},
    {"symbol": "APTUSDT", "name": "Aptos", "sector": "Layer1"},
    {"symbol": "ARBUSDT", "name": "Arbitrum", "sector": "Layer2"},
    {"symbol": "OPUSDT", "name": "Optimism", "sector": "Layer2"},
    {"symbol": "INJUSDT", "name": "Injective", "sector": "DeFi"},
]

# Correlation groups
CORRELATION_GROUPS = {
    "Major": ["BTCUSDT", "ETHUSDT"],
    "Layer1": ["SOLUSDT", "AVAXUSDT", "DOTUSDT", "ATOMUSDT", "NEARUSDT", "APTUSDT"],
    "DeFi": ["LINKUSDT", "UNIUSDT", "ARBUSDT", "OPUSDT", "INJUSDT"],
    "Legacy": ["XRPUSDT", "ADAUSDT", "LTCUSDT", "ETCUSDT"],
}


def get_correlation_group(symbol: str) -> str:
    """Get correlation group for symbol."""
    for group, symbols in CORRELATION_GROUPS.items():
        if symbol in symbols:
            return group
    return "Other"


def generate_pairs() -> list[Pair]:
    """Generate pairs with current data."""
    
    pairs = []
    active_positions = {"BTCUSDT": Side.LONG, "ETHUSDT": Side.LONG, "SOLUSDT": Side.SHORT}
    
    for config in PAIRS_CONFIG:
        symbol = config["symbol"]
        
        # Generate realistic price
        base_prices = {
            "BTCUSDT": 96500, "ETHUSDT": 3450, "BNBUSDT": 710,
            "SOLUSDT": 98, "XRPUSDT": 2.35, "ADAUSDT": 0.95,
            "AVAXUSDT": 42, "DOGEUSDT": 0.32, "DOTUSDT": 7.5,
            "MATICUSDT": 0.98, "LINKUSDT": 23, "UNIUSDT": 14,
            "ATOMUSDT": 9.5, "LTCUSDT": 105, "ETCUSDT": 28,
            "NEARUSDT": 5.2, "APTUSDT": 9.8, "ARBUSDT": 0.85,
            "OPUSDT": 1.95, "INJUSDT": 24,
        }
        
        current_price = base_prices.get(symbol, 100) * random.uniform(0.98, 1.02)
        change_24h = random.uniform(-5, 8)
        
        pairs.append(Pair(
            symbol=symbol,
            name=config["name"],
            sector=config["sector"],
            current_price=round(current_price, 4),
            price_change_24h=round(current_price * change_24h / 100, 4),
            price_change_percent_24h=round(change_24h, 2),
            volume_24h=random.uniform(100_000_000, 5_000_000_000),
            high_24h=round(current_price * 1.03, 4),
            low_24h=round(current_price * 0.97, 4),
            volatility_regime=random.choice([VolatilityRegime.LOW, VolatilityRegime.NORMAL, VolatilityRegime.HIGH]),
            atr_ratio=random.uniform(0.5, 1.5),
            has_active_position=symbol in active_positions,
            active_position_side=active_positions.get(symbol),
            last_signal_time=datetime.utcnow().isoformat() if random.random() > 0.5 else None,
        ))
    
    return pairs


_pairs = generate_pairs()


@router.get("")
async def get_pairs() -> ApiResponse:
    """Get all trading pairs."""
    return ApiResponse(data=[p.model_dump() for p in _pairs])


@router.get("/{symbol}")
async def get_pair(symbol: str = Path(...)) -> ApiResponse:
    """Get pair details."""
    
    pair = next((p for p in _pairs if p.symbol == symbol.upper()), None)
    
    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")
    
    # Extended details
    detail = PairDetail(
        **pair.model_dump(),
        signals_count_24h=random.randint(0, 10),
        trades_count_24h=random.randint(0, 5),
        win_rate_30d=random.uniform(60, 85),
        total_pnl_30d=random.uniform(-500, 2000),
        avg_trade_duration=random.randint(60, 360),
        correlation_group=get_correlation_group(symbol.upper()),
        active_timeframes=[Timeframe.M30, Timeframe.H1, Timeframe.H2],
        preset_ids=[
            f"{symbol.upper()}_30m_normal",
            f"{symbol.upper()}_1h_normal",
            f"{symbol.upper()}_2h_normal",
        ],
    )
    
    return ApiResponse(data=detail.model_dump())


@router.get("/{symbol}/chart")
async def get_pair_chart(
    symbol: str = Path(...),
    timeframe: Literal["30m", "1h", "2h", "4h", "1d"] = Query(default="1h"),
    limit: int = Query(default=100, ge=10, le=500),
) -> ApiResponse:
    """Get OHLCV data for pair."""
    
    pair = next((p for p in _pairs if p.symbol == symbol.upper()), None)
    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")
    
    # Generate OHLCV data
    tf_minutes = {"30m": 30, "1h": 60, "2h": 120, "4h": 240, "1d": 1440}
    delta = timedelta(minutes=tf_minutes[timeframe])
    
    candles = []
    now = datetime.utcnow()
    price = pair.current_price
    
    for i in range(limit):
        timestamp = now - (limit - i - 1) * delta
        
        # Random OHLCV
        open_price = price * random.uniform(0.995, 1.005)
        close_price = open_price * random.uniform(0.99, 1.01)
        high_price = max(open_price, close_price) * random.uniform(1.0, 1.015)
        low_price = min(open_price, close_price) * random.uniform(0.985, 1.0)
        volume = random.uniform(1000, 100000)
        
        candles.append(OHLCV(
            timestamp=timestamp.isoformat(),
            open=round(open_price, 4),
            high=round(high_price, 4),
            low=round(low_price, 4),
            close=round(close_price, 4),
            volume=round(volume, 2),
        ))
        
        price = close_price
    
    return ApiResponse(data=[c.model_dump() for c in candles])


@router.get("/{symbol}/signals")
async def get_pair_signals(
    symbol: str = Path(...),
    limit: int = Query(default=10, ge=1, le=50),
) -> ApiResponse:
    """Get recent signals for pair."""
    
    pair = next((p for p in _pairs if p.symbol == symbol.upper()), None)
    if not pair:
        raise HTTPException(status_code=404, detail="Pair not found")
    
    # Generate sample signals
    signals = []
    now = datetime.utcnow()
    
    for i in range(min(limit, 5)):
        side = random.choice([Side.LONG, Side.SHORT])
        entry = pair.current_price * random.uniform(0.95, 1.05)
        
        signals.append(Signal(
            id=1000 + i,
            symbol=symbol.upper(),
            side=side,
            timeframe=random.choice([Timeframe.M30, Timeframe.H1, Timeframe.H2]),
            entry_price=round(entry, 4),
            current_price=pair.current_price,
            sl_price=round(entry * (0.915 if side == Side.LONG else 1.085), 4),
            tp1_price=round(entry * (1.01 if side == Side.LONG else 0.99), 4),
            tp2_price=round(entry * (1.02 if side == Side.LONG else 0.98), 4),
            tp3_price=round(entry * (1.03 if side == Side.LONG else 0.97), 4),
            tp4_price=round(entry * (1.04 if side == Side.LONG else 0.96), 4),
            tp5_price=round(entry * (1.075 if side == Side.LONG else 0.925), 4),
            tp6_price=round(entry * (1.14 if side == Side.LONG else 0.86), 4),
            status=random.choice([SignalStatus.FILLED, SignalStatus.ACTIVE, SignalStatus.CANCELLED]),
            preset_id=f"{symbol.upper()}_1h_normal",
            volatility_regime=VolatilityRegime.NORMAL,
            confidence=random.uniform(65, 90),
            filters_passed=["volume", "rsi", "adx"],
            filters_failed=[],
            telegram_sent=True,
            cornix_sent=True,
            created_at=(now - timedelta(hours=i * 12)).isoformat(),
        ))
    
    return ApiResponse(data=[s.model_dump() for s in signals])
