@echo off
cd /d "%~dp0"
cd /d "%~dp0frontend"

echo ========================================
echo   VELAS Frontend - Starting
echo ========================================
echo.

if not exist "node_modules" (
    echo [INFO] Installing npm dependencies...
    call npm install
)

echo [INFO] Starting dev server...
echo.
echo ========================================
echo   Frontend: http://localhost:5173
echo   Stop: Ctrl+C
echo ========================================
echo.

call npm run dev

pause
