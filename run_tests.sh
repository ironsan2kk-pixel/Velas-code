#!/bin/bash

# Переходим в директорию скрипта
cd "$(dirname "$0")"

echo "============================================"
echo "  VELAS Tests Runner - Unix"
echo "============================================"
echo ""

# Создаём виртуальное окружение если нет
if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активируем venv
source venv/bin/activate

# Устанавливаем зависимости
echo "Установка зависимостей..."
pip install -q pytest pandas numpy pyyaml

# Запускаем тесты
echo ""
echo "Запуск тестов..."
echo "============================================"
python -m pytest tests/ -v --tb=short

# Код возврата
EXITCODE=$?

echo ""
echo "============================================"
if [ $EXITCODE -eq 0 ]; then
    echo "  ✅ Все тесты прошли успешно!"
else
    echo "  ❌ Некоторые тесты не прошли"
fi
echo "============================================"

deactivate

exit $EXITCODE
