@echo off
cd /d "%~dp0"

echo ========================================================
echo           VELAS Desktop - PRODUCTION
echo ========================================================
echo.

if not exist "dist" (
    echo Building production version...
    call npm run build
)

echo Starting VELAS Desktop (Production)...
call npm run start
