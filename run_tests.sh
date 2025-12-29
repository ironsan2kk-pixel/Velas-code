#!/bin/bash

# Change to script directory
cd "$(dirname "$0")"

echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║    VELAS-07 Telegram Module Tests         ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found!"
    echo "Please install Python 3.11+"
    exit 1
fi

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "[INFO] Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet pytest pytest-asyncio python-telegram-bot>=20.7

# Run tests
echo ""
echo "[INFO] Running tests..."
echo "─────────────────────────────────────────────"
echo ""

python -m pytest tests/test_telegram.py -v --tb=short

# Capture exit code
EXITCODE=$?

echo ""
echo "─────────────────────────────────────────────"

if [ $EXITCODE -eq 0 ]; then
    echo "[SUCCESS] All tests passed!"
else
    echo "[FAILED] Some tests failed!"
fi

echo ""
exit $EXITCODE
