@echo off
cd /d "%~dp0"

echo ========================================
echo   VELAS API - Starting
echo ========================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] venv not found!
    echo Run first: python -m venv venv
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo [1/2] Installing dependencies...
pip install uvicorn fastapi sqlalchemy aiohttp pydantic --quiet 2>nul

if not exist "data" mkdir data

if not exist "data\velas.db" (
    echo [INFO] Initializing database...
    python -c "from backend.db.database import init_db; init_db()" 2>nul
)

echo [2/2] Starting API server...
echo.
echo ========================================
echo   API: http://localhost:8000
echo   Docs: http://localhost:8000/docs
echo   Stop: Ctrl+C
echo ========================================
echo.

python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload

pause
