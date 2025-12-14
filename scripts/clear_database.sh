#!/bin/bash
# Скрипт для очистки базы данных (Linux/Mac)

echo "Очистка базы данных..."
echo ""

# Активируем виртуальное окружение если оно есть
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

# Запускаем скрипт очистки
python scripts/clear_database.py

if [ $? -eq 0 ]; then
    echo ""
    echo "База данных успешно очищена!"
else
    echo ""
    echo "Ошибка при очистке базы данных!"
    exit 1
fi

