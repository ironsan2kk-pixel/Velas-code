"""VELAS API - Positions endpoints."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Path
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.models import PositionModel, TradeModel
from backend.api.models import ApiResponse, PositionResponse, PositionSummary, SideEnum, TimeframeEnum, PositionStatusEnum

router = APIRouter()


def position_to_response(pos: PositionModel) -> PositionResponse:
    return PositionResponse(
        id=pos.id, symbol=pos.symbol, side=SideEnum(pos.side), timeframe=TimeframeEnum(pos.timeframe),
        preset_id=pos.preset_id, entry_price=pos.entry_price, current_price=pos.current_price,
        close_price=pos.close_price, sl_price=pos.sl_price, current_sl=pos.current_sl or pos.sl_price,
        tp1_price=pos.tp1_price, tp2_price=pos.tp2_price, tp3_price=pos.tp3_price,
        tp4_price=pos.tp4_price, tp5_price=pos.tp5_price, tp6_price=pos.tp6_price,
        tp1_hit=pos.tp1_hit, tp2_hit=pos.tp2_hit, tp3_hit=pos.tp3_hit,
        tp4_hit=pos.tp4_hit, tp5_hit=pos.tp5_hit, tp6_hit=pos.tp6_hit,
        quantity=pos.quantity, notional_value=pos.notional_value, leverage=pos.leverage,
        position_remaining=pos.position_remaining, realized_pnl=pos.realized_pnl,
        unrealized_pnl=pos.unrealized_pnl, unrealized_pnl_percent=pos.unrealized_pnl_percent,
        status=PositionStatusEnum(pos.status), close_reason=pos.close_reason,
        entry_time=pos.entry_time, close_time=pos.close_time, created_at=pos.created_at,
    )


@router.get("", response_model=ApiResponse[List[PositionResponse]])
async def get_positions(status: Optional[str] = Query(None, pattern="^(open|closed|partial)$"), db: Session = Depends(get_db)):
    query = db.query(PositionModel)
    if status:
        query = query.filter(PositionModel.status == status)
    else:
        query = query.filter(PositionModel.status == "open")
    positions = query.order_by(PositionModel.entry_time.desc()).all()
    return ApiResponse(data=[position_to_response(p) for p in positions])


@router.get("/summary", response_model=ApiResponse[PositionSummary])
async def get_positions_summary(db: Session = Depends(get_db)):
    all_positions = db.query(PositionModel).all()
    open_positions = [p for p in all_positions if p.status == "open"]
    
    total_realized = sum(p.realized_pnl or 0 for p in all_positions)
    total_unrealized = sum(p.unrealized_pnl or 0 for p in open_positions)
    total_pnl = total_realized + total_unrealized
    
    closed = [p for p in all_positions if p.status == "closed"]
    winning = len([p for p in closed if (p.realized_pnl or 0) > 0])
    losing = len([p for p in closed if (p.realized_pnl or 0) < 0])
    
    portfolio_heat = 0.0
    for pos in open_positions:
        if pos.entry_price and pos.current_sl:
            if pos.side == "LONG":
                risk = (pos.entry_price - pos.current_sl) / pos.entry_price * 100
            else:
                risk = (pos.current_sl - pos.entry_price) / pos.entry_price * 100
            portfolio_heat += abs(risk) * (pos.position_remaining / 100)
    
    initial_balance = 10000.0
    total_pnl_percent = (total_pnl / initial_balance * 100) if initial_balance > 0 else 0
    
    return ApiResponse(data=PositionSummary(
        total_positions=len(all_positions), open_positions=len(open_positions),
        total_pnl=round(total_pnl, 2), total_pnl_percent=round(total_pnl_percent, 2),
        winning_positions=winning, losing_positions=losing,
        portfolio_heat=round(portfolio_heat, 2), max_heat=15.0,
    ))


@router.get("/{position_id}", response_model=ApiResponse[PositionResponse])
async def get_position(position_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    position = db.query(PositionModel).filter(PositionModel.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    return ApiResponse(data=position_to_response(position))


@router.post("/{position_id}/close", response_model=ApiResponse[PositionResponse])
async def close_position(position_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    position = db.query(PositionModel).filter(PositionModel.id == position_id).first()
    if not position:
        raise HTTPException(status_code=404, detail="Позиция не найдена")
    if position.status != "open":
        raise HTTPException(status_code=400, detail="Позиция уже закрыта")
    
    close_price = position.current_price or position.entry_price
    if position.side == "LONG":
        pnl_percent = (close_price - position.entry_price) / position.entry_price * 100
    else:
        pnl_percent = (position.entry_price - close_price) / position.entry_price * 100
    
    notional = position.notional_value or 1000.0
    pnl_usd = notional * (position.position_remaining / 100) * pnl_percent / 100
    
    position.status = "closed"
    position.close_price = close_price
    position.close_time = datetime.utcnow()
    position.close_reason = "Manual"
    position.realized_pnl = (position.realized_pnl or 0) + pnl_usd
    position.position_remaining = 0
    
    trade = TradeModel(
        position_id=position.id, symbol=position.symbol, side=position.side, timeframe=position.timeframe,
        entry_price=position.entry_price, exit_price=close_price, pnl_percent=pnl_percent, pnl_usd=pnl_usd,
        exit_reason="Manual", tp_hits=sum([position.tp1_hit, position.tp2_hit, position.tp3_hit, position.tp4_hit, position.tp5_hit, position.tp6_hit]),
        duration_minutes=int((datetime.utcnow() - position.entry_time).total_seconds() / 60) if position.entry_time else None,
        entry_time=position.entry_time, exit_time=datetime.utcnow(),
    )
    
    db.add(trade)
    db.commit()
    db.refresh(position)
    
    return ApiResponse(data=position_to_response(position), message="Позиция закрыта")
