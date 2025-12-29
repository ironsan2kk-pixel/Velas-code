#!/bin/bash
# VELAS Trading System - Test Runner (Unix/Linux/Mac)
# Phase: VELAS-02 Data Layer

set -e

# Switch to script directory (important!)
cd "$(dirname "$0")"

echo "============================================================"
echo "VELAS-02 Data Layer Tests"
echo "============================================================"
echo "Working directory: $(pwd)"
echo "============================================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 not found"
    exit 1
fi

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Run tests
echo ""
echo "Running tests..."
echo "============================================================"

python -m pytest tests/test_data_layer.py -v --tb=short

# Check result
if [ $? -ne 0 ]; then
    echo ""
    echo "============================================================"
    echo "TESTS FAILED"
    echo "============================================================"
    deactivate
    exit 1
fi

echo ""
echo "============================================================"
echo "ALL TESTS PASSED"
echo "============================================================"

# Deactivate
deactivate

exit 0
