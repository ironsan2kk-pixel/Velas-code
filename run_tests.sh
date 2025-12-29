#!/bin/bash
cd "$(dirname "$0")"

echo "============================================"
echo "VELAS v2 - Test Runner (Unix)"
echo "============================================"
echo

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found. Please install Python 3.11+"
    exit 1
fi

# Версия Python
PYVER=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "[INFO] Python version: $PYVER"

# Создаём/активируем venv
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create venv"
        exit 1
    fi
fi

echo "[INFO] Activating virtual environment..."
source venv/bin/activate

# Обновляем pip
echo "[INFO] Upgrading pip..."
python -m pip install --upgrade pip -q

# Устанавливаем зависимости
echo "[INFO] Installing dependencies..."
pip install -q pytest pytest-asyncio pandas numpy

# Проверяем наличие backend/requirements.txt
if [ -f "backend/requirements.txt" ]; then
    pip install -q -r backend/requirements.txt
fi

echo
echo "============================================"
echo "Running Tests"
echo "============================================"
echo

# Запускаем тесты
python -m pytest tests/ -v --tb=short

TEST_RESULT=$?

echo
echo "============================================"
if [ $TEST_RESULT -eq 0 ]; then
    echo "[SUCCESS] All tests passed!"
else
    echo "[FAILED] Some tests failed. Exit code: $TEST_RESULT"
fi
echo "============================================"

# Деактивируем venv
deactivate

exit $TEST_RESULT
