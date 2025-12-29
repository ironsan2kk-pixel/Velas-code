"""
VELAS API - Settings Routes
"""

from fastapi import APIRouter, HTTPException, Path
from datetime import datetime
import random

from ..models import (
    ApiResponse,
    AllSettings,
    TradingSettings,
    TelegramSettings,
    NotificationSettings,
    Preset,
    Timeframe,
    VolatilityRegime,
)

router = APIRouter()

# Default settings
_settings = AllSettings(
    trading=TradingSettings(
        enabled=True,
        max_positions=5,
        position_size_percent=2.0,
        max_portfolio_heat=15.0,
        use_correlation_filter=True,
        max_correlated_positions=2,
    ),
    notifications=NotificationSettings(
        telegram=TelegramSettings(
            enabled=True,
            send_signals=True,
            send_tp_hits=True,
            send_sl_hits=True,
            send_daily_summary=True,
            quiet_hours_start=None,
            quiet_hours_end=None,
        ),
        sound_enabled=True,
        push_enabled=True,
    ),
    theme="dark",
    language="ru",
)


# Sample presets
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT",
    "LINKUSDT", "UNIUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT",
    "NEARUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "INJUSDT",
]


def generate_presets() -> list[Preset]:
    """Generate sample presets."""
    
    presets = []
    
    for symbol in SYMBOLS:
        for tf in [Timeframe.M30, Timeframe.H1, Timeframe.H2]:
            for regime in [VolatilityRegime.LOW, VolatilityRegime.NORMAL, VolatilityRegime.HIGH]:
                preset_id = f"{symbol}_{tf.value}_{regime.value}"
                
                # Different TP/SL based on volatility
                if regime == VolatilityRegime.LOW:
                    tp_mult = 0.8
                    sl = 6.5
                elif regime == VolatilityRegime.HIGH:
                    tp_mult = 1.3
                    sl = 10.5
                else:
                    tp_mult = 1.0
                    sl = 8.5
                
                presets.append(Preset(
                    id=preset_id,
                    symbol=symbol,
                    timeframe=tf,
                    volatility_regime=regime,
                    i1=random.randint(10, 30),
                    i2=random.randint(20, 50),
                    i3=random.randint(5, 15),
                    i4=random.randint(10, 25),
                    i5=random.randint(8, 20),
                    tp1=round(1.0 * tp_mult, 1),
                    tp2=round(2.0 * tp_mult, 1),
                    tp3=round(3.0 * tp_mult, 1),
                    tp4=round(4.0 * tp_mult, 1),
                    tp5=round(7.5 * tp_mult, 1),
                    tp6=round(14.0 * tp_mult, 1),
                    sl=sl,
                    tp_distribution=[10.0, 10.0, 10.0, 20.0, 25.0, 25.0],
                    filters=["volume", "rsi", "adx", "mtf", "session"],
                    enabled=True,
                    last_updated=datetime.utcnow().isoformat(),
                ))
    
    return presets


_presets = generate_presets()


@router.get("")
async def get_settings() -> ApiResponse:
    """Get all settings."""
    return ApiResponse(data=_settings.model_dump())


@router.put("")
async def update_settings(settings: AllSettings) -> ApiResponse:
    """Update settings."""
    global _settings
    _settings = settings
    return ApiResponse(data=_settings.model_dump())


@router.get("/presets")
async def get_presets() -> ApiResponse:
    """Get all presets."""
    return ApiResponse(data=[p.model_dump() for p in _presets])


@router.get("/presets/{preset_id}")
async def get_preset(preset_id: str = Path(...)) -> ApiResponse:
    """Get single preset."""
    
    preset = next((p for p in _presets if p.id == preset_id), None)
    
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    return ApiResponse(data=preset.model_dump())


@router.put("/presets/{preset_id}")
async def update_preset(preset_id: str = Path(...), update: Preset) -> ApiResponse:
    """Update preset."""
    
    for i, preset in enumerate(_presets):
        if preset.id == preset_id:
            update.last_updated = datetime.utcnow().isoformat()
            _presets[i] = update
            return ApiResponse(data=update.model_dump())
    
    raise HTTPException(status_code=404, detail="Preset not found")
