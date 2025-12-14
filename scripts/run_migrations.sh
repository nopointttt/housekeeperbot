#!/bin/bash
# Скрипт для запуска миграций Alembic

echo "Запуск миграций базы данных..."

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "Ошибка: файл .env не найден!"
    echo "Скопируйте .env.example в .env и заполните необходимые переменные."
    exit 1
fi

# Загружаем переменные окружения
export $(cat .env | grep -v '^#' | xargs)

# Запускаем миграции
python -m alembic upgrade head

if [ $? -eq 0 ]; then
    echo "Миграции успешно применены!"
else
    echo "Ошибка при применении миграций!"
    exit 1
fi

