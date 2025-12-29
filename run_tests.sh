#!/bin/bash
# VELAS-03-BACKTEST Test Runner
# Run all tests for backtest engine

cd "$(dirname "$0")"

echo "========================================"
echo "VELAS-03-BACKTEST Test Suite"
echo "========================================"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Run tests
echo ""
echo "Running tests..."
echo "========================================"
python -m pytest tests/ -v --tb=short

# Capture exit code
EXITCODE=$?

echo ""
echo "========================================"
if [ $EXITCODE -eq 0 ]; then
    echo "All tests PASSED!"
else
    echo "Some tests FAILED!"
fi
echo "========================================"

deactivate
exit $EXITCODE
