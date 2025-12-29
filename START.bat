@echo off
cd /d "%~dp0"

echo ========================================================
echo           VELAS Desktop - START
echo ========================================================
echo.

if not exist "frontend\node_modules" (
    echo ERROR: Dependencies not installed!
    echo        Run INSTALL.bat first
    pause
    exit /b 1
)

echo Starting VELAS Desktop...
echo.
echo    Backend: http://localhost:8000
echo    Frontend: http://localhost:5173
echo.
echo    Press Ctrl+C to stop
echo.

cd frontend
call npm run electron:dev
