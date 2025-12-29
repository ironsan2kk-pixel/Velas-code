# VELAS Trading System - Desktop Version

Complete desktop application with Electron + React + Python backend.

## Requirements

- **Node.js 18+** - https://nodejs.org/
- **Python 3.11+** - https://python.org/

## Quick Start

```
1. Run INSTALL.bat (first time only)
2. Run START.bat
```

## Files

| File | Description |
|------|-------------|
| INSTALL.bat | Install all dependencies |
| START.bat | Start desktop app |
| START_BACKEND.bat | Start only Python API |
| START_FRONTEND.bat | Start only React |
| BUILD.bat | Build installer (.exe) |

## Structure

```
velas-desktop/
├── electron/          # Electron main process
├── frontend/          # React frontend (10 pages)
├── backend/           # Python FastAPI backend
├── scripts/           # Helper scripts
├── tests/             # Python tests
└── config/            # Configuration
```

## Pages

1. Dashboard - Main panel
2. Positions - Open positions
3. History - Trade history
4. Signals - Trading signals
5. Pairs - Trading pairs
6. Analytics - Analytics
7. Backtest - Backtesting
8. Settings - Settings
9. Alerts - Notifications
10. System - System status

## API Endpoints

- http://localhost:8000/api/dashboard/*
- http://localhost:8000/api/positions/*
- http://localhost:8000/api/signals/*
- http://localhost:8000/api/history/*
- http://localhost:8000/api/pairs/*
- http://localhost:8000/api/analytics/*
- http://localhost:8000/api/backtest/*
- http://localhost:8000/api/settings/*
- http://localhost:8000/api/alerts/*
- http://localhost:8000/api/system/*

## Build Installer

```bash
BUILD.bat
```

Output: `dist/VELAS Setup 1.0.0.exe`
