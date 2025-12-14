@echo off
REM Скрипт для запуска миграций Alembic (Windows)

echo Запуск миграций базы данных...

REM Проверяем наличие .env файла
if not exist .env (
    echo Ошибка: файл .env не найден!
    echo Скопируйте .env.example в .env и заполните необходимые переменные.
    exit /b 1
)

REM Запускаем миграции
python -m alembic upgrade head

if %errorlevel% equ 0 (
    echo Миграции успешно применены!
) else (
    echo Ошибка при применении миграций!
    exit /b 1
)

