@echo off
REM VELAS Trading System - Test Runner (Windows)
REM Phase: VELAS-02 Data Layer

REM Switch to script directory (important!)
cd /d "%~dp0"

echo ============================================================
echo VELAS-02 Data Layer Tests
echo ============================================================
echo Working directory: %CD%
echo ============================================================

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found
    exit /b 1
)

REM Create virtual environment if not exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

REM Run tests
echo.
echo Running tests...
echo ============================================================

python -m pytest tests/test_data_layer.py -v --tb=short

REM Check result
if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo TESTS FAILED
    echo ============================================================
    exit /b 1
)

echo.
echo ============================================================
echo ALL TESTS PASSED
echo ============================================================

REM Deactivate
deactivate

exit /b 0
