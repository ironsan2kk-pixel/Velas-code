@echo off
cd /d "%~dp0"
title VELAS Trading System v1.0

:menu
cls
echo.
echo  ================================================================
echo                    VELAS TRADING SYSTEM v1.0
echo  ================================================================
echo.
echo   [1]  Start ALL (Backend + Frontend + Live Engine)
echo   [2]  Backend API only (port 8000)
echo   [3]  Frontend only (port 5173)
echo   [4]  Live Engine (trading + Telegram)
echo.
echo   [5]  Install dependencies (Python + Node)
echo   [6]  Download candle history
echo   [7]  Initialize database
echo.
echo   [8]  Run tests
echo   [9]  Check system status
echo.
echo   [0]  Exit
echo.
echo  ================================================================
echo.
set /p choice="  Select option: "

if "%choice%"=="1" goto start_all
if "%choice%"=="2" goto start_backend
if "%choice%"=="3" goto start_frontend
if "%choice%"=="4" goto start_live
if "%choice%"=="5" goto install_deps
if "%choice%"=="6" goto download_history
if "%choice%"=="7" goto init_db
if "%choice%"=="8" goto run_tests
if "%choice%"=="9" goto check_status
if "%choice%"=="0" goto exit_app

echo.
echo  [!] Invalid choice. Try again.
timeout /t 2 >nul
goto menu

:start_all
cls
echo.
echo  ================================================================
echo   STARTING ALL VELAS COMPONENTS
echo  ================================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo  [!] Python venv not found. Run option [5] first.
    pause
    goto menu
)

if not exist "frontend\node_modules" (
    echo  [!] Node modules not found. Run option [5] first.
    pause
    goto menu
)

echo  [1/3] Starting Backend API on port 8000...
start "VELAS Backend" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate.bat && python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 >nul

echo  [2/3] Starting Frontend on port 5173...
start "VELAS Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"
timeout /t 3 >nul

echo  [3/3] Starting Live Engine...
start "VELAS Live Engine" cmd /k "cd /d "%~dp0" && call venv\Scripts\activate.bat && python -m backend.live.engine"

echo.
echo  ================================================================
echo   ALL COMPONENTS STARTED!
echo  ================================================================
echo.
echo   Access:
echo     Dashboard: http://localhost:5173
echo     API Docs:  http://localhost:8000/api/docs
echo     Health:    http://localhost:8000/api/health
echo.
echo   To stop: close all windows or press Ctrl+C in each.
echo.
pause
goto menu

:start_backend
cls
echo.
echo  ================================================================
echo   STARTING BACKEND API
echo  ================================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo  [!] Python venv not found. Run option [5] first.
    pause
    goto menu
)

echo  Starting on port 8000...
echo.
call venv\Scripts\activate.bat
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
pause
goto menu

:start_frontend
cls
echo.
echo  ================================================================
echo   STARTING FRONTEND
echo  ================================================================
echo.

if not exist "frontend\node_modules" (
    echo  [!] Node modules not found. Run option [5] first.
    pause
    goto menu
)

cd /d "%~dp0frontend"
echo  Starting Vite dev server on port 5173...
echo.
npm run dev
pause
goto menu

:start_live
cls
echo.
echo  ================================================================
echo   STARTING LIVE ENGINE
echo  ================================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo  [!] Python venv not found. Run option [5] first.
    pause
    goto menu
)

if not exist "config\config.yaml" (
    echo  [!] config\config.yaml not found!
    echo      Copy config\config.example.yaml to config\config.yaml
    echo      and fill in Telegram token.
    pause
    goto menu
)

call venv\Scripts\activate.bat
echo  Starting Live Trading Engine...
echo  WARNING: System will send signals to Telegram!
echo.
python -m backend.live.engine
pause
goto menu

:install_deps
cls
echo.
echo  ================================================================
echo   INSTALLING DEPENDENCIES
echo  ================================================================
echo.

echo  [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  [X] Python not found! Install Python 3.11+ from python.org
    pause
    goto menu
)
python --version

echo.
echo  [2/4] Creating Python virtual environment...
if not exist "venv" (
    python -m venv venv
    echo  [OK] venv created
) else (
    echo  [OK] venv already exists
)

echo.
echo  [3/4] Installing Python packages...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul
pip install -r requirements.txt
echo  [OK] Python packages installed

echo.
echo  [4/4] Installing Node.js packages...
where npm >nul 2>&1
if errorlevel 1 (
    echo  [X] npm not found! Install Node.js 18+ from nodejs.org
    pause
    goto menu
)

cd /d "%~dp0frontend"
call npm install
echo  [OK] Node packages installed

cd /d "%~dp0"
echo.
echo  ================================================================
echo   ALL DEPENDENCIES INSTALLED!
echo  ================================================================
echo.
pause
goto menu

:download_history
cls
echo.
echo  ================================================================
echo   DOWNLOADING CANDLE HISTORY
echo  ================================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo  [!] Python venv not found. Run option [5] first.
    pause
    goto menu
)

call venv\Scripts\activate.bat
echo  Downloading data from Binance...
echo  (This may take 5-15 minutes)
echo.
python scripts\download_history.py
echo.
pause
goto menu

:init_db
cls
echo.
echo  ================================================================
echo   INITIALIZING DATABASE
echo  ================================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo  [!] Python venv not found. Run option [5] first.
    pause
    goto menu
)

call venv\Scripts\activate.bat
echo  Creating SQLite tables...
python scripts\init_database.py
echo.
echo  [OK] Database initialized: data\velas.db
echo.
pause
goto menu

:run_tests
cls
echo.
echo  ================================================================
echo   RUNNING TESTS
echo  ================================================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo  [!] Python venv not found. Run option [5] first.
    pause
    goto menu
)

call venv\Scripts\activate.bat
echo  Running pytest...
echo.
pytest tests\ -v --tb=short
echo.
pause
goto menu

:check_status
cls
echo.
echo  ================================================================
echo   CHECKING SYSTEM STATUS
echo  ================================================================
echo.

echo  Checking Backend API (port 8000)...
curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 (
    echo    [X] Backend API - NOT RUNNING
) else (
    echo    [OK] Backend API - RUNNING
    curl -s http://localhost:8000/api/health
    echo.
)

echo.
echo  Checking Frontend (port 5173)...
curl -s http://localhost:5173 >nul 2>&1
if errorlevel 1 (
    echo    [X] Frontend - NOT RUNNING
) else (
    echo    [OK] Frontend - RUNNING
)

echo.
echo  Checking database...
if exist "data\velas.db" (
    echo    [OK] SQLite DB exists: data\velas.db
) else (
    echo    [!] SQLite DB not found (run option [7])
)

echo.
echo  Checking config...
if exist "config\config.yaml" (
    echo    [OK] config.yaml found
) else (
    echo    [!] config.yaml not found
)

echo.
echo  Checking candle data...
if exist "data\candles\BTCUSDT_1h.parquet" (
    echo    [OK] Historical data exists
) else (
    echo    [!] Historical data not downloaded (run option [6])
)

echo.
echo  ================================================================
echo.
pause
goto menu

:exit_app
cls
echo.
echo  Goodbye! VELAS Trading System
echo.
timeout /t 2 >nul
exit /b 0
