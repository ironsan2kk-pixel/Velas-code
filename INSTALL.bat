@echo off
cd /d "%~dp0"

echo ========================================================
echo           VELAS Desktop - INSTALL
echo ========================================================
echo.

echo [1/4] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found! Install from https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do echo OK: Node.js %%i

echo.
echo [2/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Install from https://python.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo OK: %%i

echo.
echo [3/4] Installing Node.js dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo ERROR: npm install failed
    cd ..
    pause
    exit /b 1
)
cd ..
echo OK: Node.js dependencies installed

echo.
echo [4/4] Installing Python dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: pip install failed
    pause
    exit /b 1
)
echo OK: Python dependencies installed

echo.
echo ========================================================
echo           INSTALL COMPLETE!
echo.
echo           Run START.bat to launch application
echo ========================================================
echo.
pause
