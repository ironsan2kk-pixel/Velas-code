"""
VELAS API - Pairs Routes

Возвращает информацию о торговых парах.
В будущем будет интегрирован с Binance API для реальных цен.
"""

from fastapi import APIRouter, Query, HTTPException, Path, Depends
from typing import Literal, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import PositionModel, SignalModel, TradeModel
from ..models import (
    ApiResponse,
    Pair,
    PairDetail,
    OHLCV,
    Signal,
    SideEnum,
    TimeframeEnum,
    VolatilityRegimeEnum,
    SignalStatusEnum,
)

router = APIRouter()


# 20 торговых пар
PAIRS_CONFIG = [
    {"symbol": "BTCUSDT", "name": "Bitcoin", "sector": "Major", "base_price": 96500},
    {"symbol": "ETHUSDT", "name": "Ethereum", "sector": "Major", "base_price": 3450},
    {"symbol": "BNBUSDT", "name": "BNB", "sector": "Exchange", "base_price": 710},
    {"symbol": "SOLUSDT", "name": "Solana", "sector": "Layer1", "base_price": 198},
    {"symbol": "XRPUSDT", "name": "XRP", "sector": "Legacy", "base_price": 2.35},
    {"symbol": "ADAUSDT", "name": "Cardano", "sector": "Legacy", "base_price": 0.95},
    {"symbol": "AVAXUSDT", "name": "Avalanche", "sector": "Layer1", "base_price": 42},
    {"symbol": "DOGEUSDT", "name": "Dogecoin", "sector": "Meme", "base_price": 0.32},
    {"symbol": "DOTUSDT", "name": "Polkadot", "sector": "Layer1", "base_price": 7.5},
    {"symbol": "MATICUSDT", "name": "Polygon", "sector": "Layer2", "base_price": 0.98},
    {"symbol": "LINKUSDT", "name": "Chainlink", "sector": "DeFi", "base_price": 23},
    {"symbol": "UNIUSDT", "name": "Uniswap", "sector": "DeFi", "base_price": 14},
    {"symbol": "ATOMUSDT", "name": "Cosmos", "sector": "Layer1", "base_price": 9.5},
    {"symbol": "LTCUSDT", "name": "Litecoin", "sector": "Legacy", "base_price": 105},
    {"symbol": "ETCUSDT", "name": "Ethereum Classic", "sector": "Legacy", "base_price": 28},
    {"symbol": "NEARUSDT", "name": "NEAR Protocol", "sector": "Layer1", "base_price": 5.2},
    {"symbol": "APTUSDT", "name": "Aptos", "sector": "Layer1", "base_price": 9.8},
    {"symbol": "ARBUSDT", "name": "Arbitrum", "sector": "Layer2", "base_price": 0.85},
    {"symbol": "OPUSDT", "name": "Optimism", "sector": "Layer2", "base_price": 1.95},
    {"symbol": "INJUSDT", "name": "Injective", "sector": "DeFi", "base_price": 24},
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


def get_pair_stats_from_db(symbol: str, db: Session) -> dict:
    """Получить статистику пары из БД."""
    # Открытые позиции по символу
    open_position = db.query(PositionModel).filter(
        PositionModel.symbol == symbol,
        PositionModel.status == "open"
    ).first()
    
    # Сигналы за 24 часа
    yesterday = datetime.utcnow() - timedelta(hours=24)
    signals_24h = db.query(SignalModel).filter(
        SignalModel.symbol == symbol,
        SignalModel.created_at >= yesterday
    ).count()
    
    # Сделки за 24 часа
    trades_24h = db.query(TradeModel).filter(
        TradeModel.symbol == symbol,
        TradeModel.created_at >= yesterday
    ).count()
    
    # Статистика за 30 дней
    month_ago = datetime.utcnow() - timedelta(days=30)
    trades_30d = db.query(TradeModel).filter(
        TradeModel.symbol == symbol,
        TradeModel.created_at >= month_ago
    ).all()
    
    total_pnl_30d = sum(t.pnl_usd for t in trades_30d) if trades_30d else 0
    win_rate_30d = 0.0
    if trades_30d:
        winners = len([t for t in trades_30d if t.pnl_usd > 0])
        win_rate_30d = (winners / len(trades_30d)) * 100
    
    avg_duration = None
    if trades_30d:
        durations = [t.duration_minutes for t in trades_30d if t.duration_minutes]
        avg_duration = sum(durations) / len(durations) if durations else None
    
    return {
        "has_position": open_position is not None,
        "position_side": SideEnum(open_position.side) if open_position else None,
        "signals_24h": signals_24h,
        "trades_24h": trades_24h,
        "total_pnl_30d": total_pnl_30d,
        "win_rate_30d": win_rate_30d,
        "avg_duration": int(avg_duration) if avg_duration else 0,
    }


@router.get("")
async def get_pairs(db: Session = Depends(get_db)) -> ApiResponse:
    """Get all trading pairs."""
    
    pairs = []
    
    for config in PAIRS_CONFIG:
        symbol = config["symbol"]
        base_price = config["base_price"]
        
        # Получаем статистику из БД
        stats = get_pair_stats_from_db(symbol, db)
        
        # Последний сигнал
        last_signal = db.query(SignalModel).filter(
            SignalModel.symbol == symbol
        ).order_by(SignalModel.created_at.desc()).first()
        
        pairs.append(Pair(
            symbol=symbol,
            name=config["name"],
            sector=config["sector"],
            current_price=base_price,  # TODO: Заменить на реальную цену с Binance
            price_change_24h=0.0,  # TODO: Заменить на реальные данные
            price_change_percent_24h=0.0,  # TODO: Заменить на реальные данные
            volume_24h=0.0,  # TODO: Заменить на реальные данные
            high_24h=base_price * 1.02,  # TODO: Заменить на реальные данные
            low_24h=base_price * 0.98,  # TODO: Заменить на реальные данные
            volatility_regime=VolatilityRegimeEnum.NORMAL,
            atr_ratio=1.0,
            has_active_position=stats["has_position"],
            active_position_side=stats["position_side"],
            last_signal_time=last_signal.created_at.isoformat() if last_signal else None,
        ))
    
    return ApiResponse(data=[p.model_dump() for p in pairs])


@router.get("/{symbol}")
async def get_pair(
    symbol: str = Path(...),
    db: Session = Depends(get_db)
) -> ApiResponse:
    """Get pair details."""
    
    symbol = symbol.upper()
    config = next((p for p in PAIRS_CONFIG if p["symbol"] == symbol), None)
    
    if not config:
        raise HTTPException(status_code=404, detail="Пара не найдена")
    
    # Получаем статистику из БД
    stats = get_pair_stats_from_db(symbol, db)
    
    # Последний сигнал
    last_signal = db.query(SignalModel).filter(
        SignalModel.symbol == symbol
    ).order_by(SignalModel.created_at.desc()).first()
    
    base_price = config["base_price"]
    
    detail = PairDetail(
        symbol=symbol,
        name=config["name"],
        sector=config["sector"],
        current_price=base_price,  # TODO: Binance API
        price_change_24h=0.0,
        price_change_percent_24h=0.0,
        volume_24h=0.0,
        high_24h=base_price * 1.02,
        low_24h=base_price * 0.98,
        volatility_regime=VolatilityRegimeEnum.NORMAL,
        atr_ratio=1.0,
        has_active_position=stats["has_position"],
        active_position_side=stats["position_side"],
        last_signal_time=last_signal.created_at.isoformat() if last_signal else None,
        signals_count_24h=stats["signals_24h"],
        trades_count_24h=stats["trades_24h"],
        win_rate_30d=stats["win_rate_30d"],
        total_pnl_30d=stats["total_pnl_30d"],
        avg_trade_duration=stats["avg_duration"],
        correlation_group=get_correlation_group(symbol),
        active_timeframes=[TimeframeEnum.M30, TimeframeEnum.H1, TimeframeEnum.H2],
        preset_ids=[
            f"{symbol}_30m_normal",
            f"{symbol}_1h_normal",
            f"{symbol}_2h_normal",
        ],
    )
    
    return ApiResponse(data=detail.model_dump())


@router.get("/{symbol}/chart")
async def get_pair_chart(
    symbol: str = Path(...),
    timeframe: Literal["30m", "1h", "2h", "4h", "1d"] = Query(default="1h"),
    limit: int = Query(default=100, ge=10, le=500),
    db: Session = Depends(get_db)
) -> ApiResponse:
    """Get OHLCV data for pair.
    
    TODO: Интегрировать с Binance REST API для реальных данных.
    """
    
    symbol = symbol.upper()
    config = next((p for p in PAIRS_CONFIG if p["symbol"] == symbol), None)
    
    if not config:
        raise HTTPException(status_code=404, detail="Пара не найдена")
    
    # TODO: Заменить на реальные данные с Binance
    # from backend.data.binance_rest import BinanceRestClient
    # client = BinanceRestClient()
    # candles = await client.get_klines(symbol, timeframe, limit)
    
    # Временная заглушка - пустой массив
    # Фронтенд покажет "Нет данных"
    candles = []
    
    return ApiResponse(data=candles)


@router.get("/{symbol}/signals")
async def get_pair_signals(
    symbol: str = Path(...),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
) -> ApiResponse:
    """Get recent signals for pair."""
    
    symbol = symbol.upper()
    config = next((p for p in PAIRS_CONFIG if p["symbol"] == symbol), None)
    
    if not config:
        raise HTTPException(status_code=404, detail="Пара не найдена")
    
    # Получаем реальные сигналы из БД
    signals_db = db.query(SignalModel).filter(
        SignalModel.symbol == symbol
    ).order_by(SignalModel.created_at.desc()).limit(limit).all()
    
    signals = []
    for sig in signals_db:
        signals.append(Signal(
            id=sig.id,
            symbol=sig.symbol,
            side=SideEnum(sig.side),
            timeframe=TimeframeEnum(sig.timeframe),
            entry_price=sig.entry_price,
            current_price=None,  # TODO: текущая цена
            sl_price=sig.sl_price,
            tp1_price=sig.tp1_price,
            tp2_price=sig.tp2_price,
            tp3_price=sig.tp3_price,
            tp4_price=sig.tp4_price,
            tp5_price=sig.tp5_price,
            tp6_price=sig.tp6_price,
            status=SignalStatusEnum(sig.status),
            preset_id=sig.preset_id,
            volatility_regime=VolatilityRegimeEnum(sig.volatility_regime) if sig.volatility_regime else VolatilityRegimeEnum.NORMAL,
            confidence=sig.confidence,
            filters_passed=[],  # TODO
            filters_failed=[],
            telegram_sent=sig.telegram_sent,
            cornix_sent=sig.telegram_sent,  # Cornix через Telegram
            created_at=sig.created_at.isoformat() if sig.created_at else None,
        ))
    
    return ApiResponse(data=[s.model_dump() for s in signals])
