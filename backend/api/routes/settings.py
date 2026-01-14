"""
VELAS API - Settings Routes
Настройки системы с хранением в базе данных.
"""

from fastapi import APIRouter, HTTPException, Path, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from backend.db.database import get_db
from backend.db.models import SettingModel, PresetModel
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
DEFAULT_SETTINGS = AllSettings(
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

# 20 trading pairs
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT",
    "LINKUSDT", "UNIUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT",
    "NEARUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "INJUSDT",
]

# Optimized VELAS indicator parameters by asset class
PRESET_PARAMS = {
    # Major pairs - more stable
    "BTCUSDT": {"i1": 21, "i2": 34, "i3": 8, "i4": 13, "i5": 10},
    "ETHUSDT": {"i1": 20, "i2": 35, "i3": 9, "i4": 14, "i5": 11},
    # Layer 1
    "BNBUSDT": {"i1": 18, "i2": 32, "i3": 10, "i4": 15, "i5": 12},
    "SOLUSDT": {"i1": 16, "i2": 30, "i3": 11, "i4": 16, "i5": 13},
    "AVAXUSDT": {"i1": 17, "i2": 31, "i3": 10, "i4": 15, "i5": 12},
    "DOTUSDT": {"i1": 19, "i2": 33, "i3": 9, "i4": 14, "i5": 11},
    "ATOMUSDT": {"i1": 18, "i2": 32, "i3": 10, "i4": 15, "i5": 12},
    "NEARUSDT": {"i1": 17, "i2": 31, "i3": 10, "i4": 15, "i5": 12},
    "APTUSDT": {"i1": 16, "i2": 30, "i3": 11, "i4": 16, "i5": 13},
    "INJUSDT": {"i1": 15, "i2": 29, "i3": 12, "i4": 17, "i5": 14},
    # Legacy/Payment
    "XRPUSDT": {"i1": 22, "i2": 36, "i3": 8, "i4": 13, "i5": 10},
    "ADAUSDT": {"i1": 21, "i2": 35, "i3": 9, "i4": 14, "i5": 11},
    "LTCUSDT": {"i1": 23, "i2": 37, "i3": 7, "i4": 12, "i5": 9},
    "ETCUSDT": {"i1": 22, "i2": 36, "i3": 8, "i4": 13, "i5": 10},
    # Meme/Volatile
    "DOGEUSDT": {"i1": 14, "i2": 28, "i3": 13, "i4": 18, "i5": 15},
    "MATICUSDT": {"i1": 17, "i2": 31, "i3": 10, "i4": 15, "i5": 12},
    # DeFi
    "LINKUSDT": {"i1": 19, "i2": 33, "i3": 9, "i4": 14, "i5": 11},
    "UNIUSDT": {"i1": 18, "i2": 32, "i3": 10, "i4": 15, "i5": 12},
    # L2
    "ARBUSDT": {"i1": 15, "i2": 29, "i3": 12, "i4": 17, "i5": 14},
    "OPUSDT": {"i1": 16, "i2": 30, "i3": 11, "i4": 16, "i5": 13},
}


def get_preset_params(symbol: str) -> dict:
    """Get optimized parameters for symbol."""
    return PRESET_PARAMS.get(symbol, {"i1": 20, "i2": 35, "i3": 10, "i4": 15, "i5": 12})


def generate_presets() -> list[Preset]:
    """Generate presets with optimized parameters."""
    presets = []

    for symbol in SYMBOLS:
        params = get_preset_params(symbol)

        for tf in [Timeframe.M30, Timeframe.H1, Timeframe.H2]:
            for regime in [VolatilityRegime.LOW, VolatilityRegime.NORMAL, VolatilityRegime.HIGH]:
                preset_id = f"{symbol}_{tf.value}_{regime.value}"

                # TP/SL multipliers based on volatility regime
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
                    i1=params["i1"],
                    i2=params["i2"],
                    i3=params["i3"],
                    i4=params["i4"],
                    i5=params["i5"],
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


# Initialize presets once
_presets = generate_presets()


@router.get("")
async def get_settings(db: Session = Depends(get_db)) -> ApiResponse:
    """Get all settings from database."""
    setting = db.query(SettingModel).filter(SettingModel.key == "system_settings").first()

    if setting and setting.value:
        return ApiResponse(data=setting.value)

    return ApiResponse(data=DEFAULT_SETTINGS.model_dump())


@router.put("")
async def update_settings(settings: AllSettings, db: Session = Depends(get_db)) -> ApiResponse:
    """Update settings in database."""
    setting = db.query(SettingModel).filter(SettingModel.key == "system_settings").first()

    if setting:
        setting.value = settings.model_dump()
    else:
        setting = SettingModel(key="system_settings", value=settings.model_dump())
        db.add(setting)

    db.commit()
    return ApiResponse(data=settings.model_dump())


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
async def update_preset(update: Preset, preset_id: str = Path(...)) -> ApiResponse:
    """Update preset."""
    for i, preset in enumerate(_presets):
        if preset.id == preset_id:
            update.last_updated = datetime.utcnow().isoformat()
            _presets[i] = update
            return ApiResponse(data=update.model_dump())

    raise HTTPException(status_code=404, detail="Preset not found")
