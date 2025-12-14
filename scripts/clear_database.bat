@echo off
REM Скрипт для очистки базы данных (Windows)

echo Очистка базы данных...
echo.

REM Переходим в корневую директорию проекта
cd /d "%~dp0\.."

REM Активируем виртуальное окружение если оно есть
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Запускаем скрипт очистки
python scripts\clear_database.py

if %errorlevel% equ 0 (
    echo.
    echo База данных успешно очищена!
) else (
    echo.
    echo Ошибка при очистке базы данных!
    pause
    exit /b 1
)

pause

