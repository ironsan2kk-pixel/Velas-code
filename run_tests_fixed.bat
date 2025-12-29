@echo off
cd /d "%~dp0"

echo.
echo ========================================
echo    VELAS-07 Telegram Module Tests
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.11+
    pause
    exit /b 1
)

echo [INFO] Python found
python --version

:: Create venv if not exists
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

:: Activate venv
echo [INFO] Activating venv...
call venv\Scripts\activate.bat

:: Install dependencies
echo [INFO] Installing dependencies...
pip install --quiet --upgrade pip
pip install --quiet pytest pytest-asyncio python-telegram-bot

:: Run tests
echo.
echo [INFO] Running tests...
echo ----------------------------------------
echo.

python -m pytest tests/test_telegram.py -v --tb=short

:: Capture exit code
set EXITCODE=%ERRORLEVEL%

echo.
echo ----------------------------------------

if %EXITCODE% EQU 0 (
    echo [SUCCESS] All tests passed!
) else (
    echo [FAILED] Some tests failed!
)

echo.
pause
exit /b %EXITCODE%
