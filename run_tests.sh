#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo " VELAS-04 Optimizer Tests"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found!"
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
pip install --quiet -r requirements.txt

# Run tests
echo ""
echo "[INFO] Running tests..."
echo "========================================"
python -m pytest tests/ -v --tb=short

# Deactivate
deactivate

echo ""
echo "========================================"
echo " Tests Complete!"
echo "========================================"
