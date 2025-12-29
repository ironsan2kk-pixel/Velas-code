@echo off
cd /d "%~dp0"

echo ============================================
echo   VELAS Tests Runner - Windows
echo ============================================
echo.

REM Создаём виртуальное окружение если нет
if not exist "venv" (
    echo Создание виртуального окружения...
    python -m venv venv
)

REM Активируем venv
call venv\Scripts\activate.bat

REM Устанавливаем зависимости
echo Установка зависимостей...
pip install -q pytest pandas numpy pyyaml

REM Запускаем тесты
echo.
echo Запуск тестов...
echo ============================================
python -m pytest tests/ -v --tb=short

REM Код возврата
set EXITCODE=%ERRORLEVEL%

echo.
echo ============================================
if %EXITCODE% == 0 (
    echo   ✅ Все тесты прошли успешно!
) else (
    echo   ❌ Некоторые тесты не прошли
)
echo ============================================
pause
deactivate

exit /b %EXITCODE%
