"""
VELAS API - Alerts Routes
"""

from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from typing import Optional
import random

from ..models import (
    ApiResponse,
    PaginatedResponse,
)

router = APIRouter()


# Mock alert settings
MOCK_ALERT_SETTINGS = {
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


def generate_mock_alerts(page: int = 1, page_size: int = 20):
    """Generate mock alert history."""
    alert_templates = [
        {
            "type": "warning",
            "category": "trading",
            "title": "3 убыточных сделки подряд",
            "message": "SOLUSDT — рассмотрите паузу",
        },
        {
            "type": "success",
            "category": "trading",
            "title": "Позиция закрыта с прибылью",
            "message": "BTCUSDT LONG закрыта с +8.5%",
        },
        {
            "type": "info",
            "category": "system",
            "title": "Алгоритм обновлён",
            "message": "Новые параметры для ETHUSDT",
        },
        {
            "type": "error",
            "category": "system",
            "title": "Ошибка подключения к Binance",
            "message": "Переподключение через 30 секунд",
        },
        {
            "type": "warning",
            "category": "portfolio",
            "title": "Высокая корреляция портфеля",
            "message": "3 позиции в группе Layer1",
        },
        {
            "type": "success",
            "category": "performance",
            "title": "Win Rate выше целевого",
            "message": "Текущий WR: 72.5% (цель: 70%)",
        },
        {
            "type": "warning",
            "category": "performance",
            "title": "Приближение к лимиту просадки",
            "message": "Текущая DD: 12.8% (лимит: 15%)",
        },
        {
            "type": "info",
            "category": "trading",
            "title": "Новый сигнал",
            "message": "ARBUSDT SHORT — confidence 85%",
        },
    ]
    
    total_alerts = 50
    alerts = []
    
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_alerts)
    
    for i in range(start_idx, end_idx):
        template = alert_templates[i % len(alert_templates)]
        timestamp = datetime.utcnow() - timedelta(hours=i * 2, minutes=random.randint(0, 59))
        
        alerts.append({
            "id": f"alert_{i+1}",
            "type": template["type"],
            "category": template["category"],
            "title": template["title"],
            "message": template["message"],
            "created_at": timestamp.isoformat(),
            "read": i < 10,  # Первые 10 прочитаны
            "acknowledged": i < 5,  # Первые 5 подтверждены
        })
    
    return {
        "data": alerts,
        "total": total_alerts,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_alerts + page_size - 1) // page_size,
    }


@router.get("/settings")
async def get_alert_settings():
    """Get current alert settings."""
    return ApiResponse(success=True, data=MOCK_ALERT_SETTINGS, timestamp=datetime.utcnow().isoformat())


@router.put("/settings")
async def update_alert_settings(settings: dict):
    """Update alert settings."""
    # В реальной системе здесь будет сохранение в БД
    return ApiResponse(success=True, data={**MOCK_ALERT_SETTINGS, **settings}, timestamp=datetime.utcnow().isoformat())


@router.get("/history")
async def get_alert_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Get alert history with pagination."""
    data = generate_mock_alerts(page, page_size)
    return ApiResponse(success=True, data=data, timestamp=datetime.utcnow().isoformat())
