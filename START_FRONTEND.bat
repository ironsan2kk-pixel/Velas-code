@echo off
cd /d "%~dp0"

echo ========================================================
echo           VELAS - Frontend Only
echo ========================================================
echo.
echo Starting React on http://localhost:5173
echo.

cd frontend
call npm run dev
