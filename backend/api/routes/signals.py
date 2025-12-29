"""VELAS API - Signals endpoints."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session
import math

from backend.db.database import get_db
from backend.db.models import SignalModel
from backend.api.models import ApiResponse, PaginatedResponse, SignalResponse, SideEnum, TimeframeEnum, SignalStatusEnum, VolatilityRegimeEnum

router = APIRouter()


def signal_to_response(sig: SignalModel) -> SignalResponse:
    return SignalResponse(
        id=sig.id, symbol=sig.symbol, side=SideEnum(sig.side), timeframe=TimeframeEnum(sig.timeframe),
        entry_price=sig.entry_price, sl_price=sig.sl_price,
        tp1_price=sig.tp1_price, tp2_price=sig.tp2_price, tp3_price=sig.tp3_price,
        tp4_price=sig.tp4_price, tp5_price=sig.tp5_price, tp6_price=sig.tp6_price,
        preset_id=sig.preset_id, volatility_regime=VolatilityRegimeEnum(sig.volatility_regime) if sig.volatility_regime else VolatilityRegimeEnum.NORMAL,
        confidence=sig.confidence, status=SignalStatusEnum(sig.status), position_id=sig.position_id,
        telegram_sent=sig.telegram_sent, filter_passed=sig.filter_passed, filter_reason=sig.filter_reason,
        created_at=sig.created_at,
    )


@router.get("", response_model=PaginatedResponse[SignalResponse])
async def get_signals(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), status: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(SignalModel)
    if status:
        query = query.filter(SignalModel.status == status)
    
    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    
    signals = query.order_by(SignalModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return PaginatedResponse(data=[signal_to_response(s) for s in signals], total=total, page=page, page_size=page_size, total_pages=total_pages)


@router.get("/pending", response_model=ApiResponse[List[SignalResponse]])
async def get_pending_signals(db: Session = Depends(get_db)):
    signals = db.query(SignalModel).filter(SignalModel.status.in_(["pending", "active"])).order_by(SignalModel.created_at.desc()).all()
    return ApiResponse(data=[signal_to_response(s) for s in signals])


@router.get("/{signal_id}", response_model=ApiResponse[SignalResponse])
async def get_signal(signal_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    signal = db.query(SignalModel).filter(SignalModel.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail="Сигнал не найден")
    return ApiResponse(data=signal_to_response(signal))
