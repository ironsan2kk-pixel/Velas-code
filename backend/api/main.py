"""
VELAS API - FastAPI точка входа.

Запуск:
    uvicorn backend.api.main:app --reload --port 8000
"""

import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .routes import (
    dashboard,
    positions,
    signals,
    history,
    pairs,
    analytics,
    backtest,
    settings,
    alerts,
    system,
    websocket,
)
from backend.db.database import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

APP_VERSION = "1.0.0"
APP_BUILD = "2024-12-29"
START_TIME = datetime.utcnow()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting VELAS API...")
    init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down VELAS API...")


app = FastAPI(
    title="VELAS Trading System API",
    description="API для криптотрейдинговой системы VELAS",
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "version": APP_VERSION}


@app.get("/api/version")
async def get_version():
    uptime = (datetime.utcnow() - START_TIME).total_seconds()
    return {"version": APP_VERSION, "build": APP_BUILD, "uptime_seconds": int(uptime)}


# Include all routers
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(positions.router, prefix="/api/positions", tags=["Positions"])
app.include_router(signals.router, prefix="/api/signals", tags=["Signals"])
app.include_router(history.router, prefix="/api/history", tags=["History"])
app.include_router(pairs.router, prefix="/api/pairs", tags=["Pairs"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["Backtest"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(system.router, prefix="/api/system", tags=["System"])

# WebSocket - подключаем без prefix чтобы был доступен на /ws
app.include_router(websocket.router, tags=["WebSocket"])


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error", "detail": str(exc), "timestamp": datetime.utcnow().isoformat()}
    )


@app.get("/")
async def root():
    return {"message": "VELAS API", "docs": "/api/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
