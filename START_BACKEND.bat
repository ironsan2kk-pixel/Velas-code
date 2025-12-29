@echo off
cd /d "%~dp0"

echo ========================================================
echo           VELAS - Backend Only
echo ========================================================
echo.
echo Starting Python Backend on http://localhost:8000
echo.

cd backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
