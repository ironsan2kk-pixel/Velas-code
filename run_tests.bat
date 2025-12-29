@echo off
cd /d "%~dp0"
chcp 65001 >nul
title VELAS-04 Tests

echo ========================================
echo  VELAS-04 Optimizer Tests
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    exit /b 1
)

:: Create venv if not exists
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

:: Activate venv
call venv\Scripts\activate.bat

:: Install dependencies
echo [INFO] Installing dependencies...
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

:: Run tests
echo.
echo [INFO] Running tests...
echo ========================================
python -m pytest tests/ -v --tb=short
pause
:: Deactivate
deactivate
pause
echo.
echo ========================================
echo  Tests Complete!
echo ========================================
pause
