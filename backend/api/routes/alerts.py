"""
VELAS API - Alerts Routes
Работа с уведомлениями через базу данных.
"""

from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from backend.db.database import get_db
from backend.db.models import AlertModel, SettingModel
from ..models import ApiResponse

router = APIRouter()

# Default alert settings (stored in DB on first use)
DEFAULT_ALERT_SETTINGS = {
    "enabled": True,
    "telegram_enabled": True,
    "desktop_enabled": True,
    "sound_enabled": True,
    "trading_alerts": {
        "new_signal": True,
        "position_opened": True,
        "tp_hit": True,
        "sl_hit": True,
        "position_closed": True,
    },
    "portfolio_alerts": {
        "max_positions_reached": True,
        "high_correlation_warning": True,
        "portfolio_heat_limit": True,
        "drawdown_limit": True,
    },
    "system_alerts": {
        "component_offline": True,
        "api_error": True,
        "data_error": False,
        "backtest_completed": True,
    },
    "performance_alerts": {
        "loss_streak": True,
        "low_win_rate": True,
        "high_drawdown": True,
    },
    "loss_streak_threshold": 3,
    "win_rate_threshold": 50.0,
    "drawdown_threshold": 15.0,
}


@router.get("/settings")
async def get_alert_settings(db: Session = Depends(get_db)):
    """Get current alert settings from database."""
    setting = db.query(SettingModel).filter(SettingModel.key == "alert_settings").first()

    if setting and setting.value:
        return ApiResponse(success=True, data=setting.value)

    return ApiResponse(success=True, data=DEFAULT_ALERT_SETTINGS)


@router.put("/settings")
async def update_alert_settings(settings: dict, db: Session = Depends(get_db)):
    """Update alert settings in database."""
    setting = db.query(SettingModel).filter(SettingModel.key == "alert_settings").first()

    if setting:
        setting.value = settings
    else:
        setting = SettingModel(key="alert_settings", value=settings)
        db.add(setting)

    db.commit()
    return ApiResponse(success=True, data=settings)


@router.get("/history")
async def get_alert_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get alert history from database with pagination."""
    total = db.query(AlertModel).count()
    offset = (page - 1) * page_size

    alerts = (
        db.query(AlertModel)
        .order_by(AlertModel.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    alert_list = [
        {
            "id": str(alert.id),
            "type": alert.type,
            "category": alert.category,
            "title": alert.title,
            "message": alert.message,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            "read": alert.read,
            "acknowledged": alert.acknowledged,
        }
        for alert in alerts
    ]

    return ApiResponse(
        success=True,
        data={
            "data": alert_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
        },
    )


@router.post("")
async def create_alert(
    alert_type: str,
    category: str,
    title: str,
    message: str = None,
    db: Session = Depends(get_db),
):
    """Create a new alert."""
    alert = AlertModel(
        type=alert_type,
        category=category,
        title=title,
        message=message,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    return ApiResponse(success=True, data={"id": alert.id})


@router.put("/{alert_id}/read")
async def mark_alert_read(alert_id: int, db: Session = Depends(get_db)):
    """Mark alert as read."""
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if alert:
        alert.read = True
        db.commit()
    return ApiResponse(success=True, data={"id": alert_id, "read": True})


@router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Acknowledge alert."""
    alert = db.query(AlertModel).filter(AlertModel.id == alert_id).first()
    if alert:
        alert.acknowledged = True
        alert.read = True
        db.commit()
    return ApiResponse(success=True, data={"id": alert_id, "acknowledged": True})
