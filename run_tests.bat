@echo off
REM VELAS-03-BACKTEST Test Runner
REM Run all tests for backtest engine

cd /d "%~dp0"

echo ========================================
echo VELAS-03-BACKTEST Test Suite
echo ========================================

REM Create virtual environment if not exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv and install dependencies
echo Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip -q
pip install -r requirements.txt -q

REM Run tests
echo.
echo Running tests...
echo ========================================
python -m pytest tests/ -v --tb=short

REM Capture exit code
set EXITCODE=%ERRORLEVEL%

echo.
echo ========================================
if %EXITCODE% == 0 (
    echo All tests PASSED!
) else (
    echo Some tests FAILED!
)
echo ========================================

deactivate
exit /b %EXITCODE%
