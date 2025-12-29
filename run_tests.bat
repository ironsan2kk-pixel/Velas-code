@echo off
cd /d "%~dp0"
setlocal EnableDelayedExpansion

echo ============================================
echo VELAS v2 - Test Runner (Windows)
echo ============================================
echo.

REM Проверяем Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.11+
    exit /b 1
)

REM Проверяем версию Python
for /f "tokens=2 delims= " %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [INFO] Python version: %PYVER%

REM Создаём/активируем venv
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create venv
        exit /b 1
    )
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Обновляем pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip -q

REM Устанавливаем зависимости
echo [INFO] Installing dependencies...
pip install -q pytest pytest-asyncio pandas numpy

REM Проверяем наличие backend/requirements.txt
if exist "backend\requirements.txt" (
    pip install -q -r backend\requirements.txt
)

echo.
echo ============================================
echo Running Tests
echo ============================================
echo.

REM Запускаем тесты
python -m pytest tests/ -v --tb=short

set TEST_RESULT=%ERRORLEVEL%

echo.
echo ============================================
if %TEST_RESULT% equ 0 (
    echo [SUCCESS] All tests passed!
) else (
    echo [FAILED] Some tests failed. Exit code: %TEST_RESULT%
)
echo ============================================
pause
REM Деактивируем venv
deactivate

exit /b %TEST_RESULT%
