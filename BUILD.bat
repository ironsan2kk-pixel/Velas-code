@echo off
cd /d "%~dp0"

echo ========================================================
echo           VELAS Desktop - BUILD INSTALLER
echo ========================================================
echo.

if not exist "frontend\node_modules" (
    echo ERROR: Dependencies not installed!
    echo        Run INSTALL.bat first
    pause
    exit /b 1
)

echo [1/2] Building React app...
cd frontend
call npm run build
if errorlevel 1 (
    echo ERROR: React build failed
    cd ..
    pause
    exit /b 1
)
echo OK: React built

echo.
echo [2/2] Building Electron installer...
call npm run dist
if errorlevel 1 (
    echo ERROR: Electron build failed
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo ========================================================
echo           BUILD COMPLETE!
echo.
echo           Installer: dist\VELAS Setup 1.0.0.exe
echo ========================================================
echo.

explorer dist
pause
