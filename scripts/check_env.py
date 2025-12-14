"""Проверка загрузки переменных окружения"""
from pathlib import Path
import os
from dotenv import load_dotenv

# Путь к .env
env_path = Path('.env').absolute()
print(f'📁 Путь к .env: {env_path}')
print(f'✅ Файл существует: {env_path.exists()}\n')

# Загружаем переменные
load_dotenv()

# Проверяем переменные
print('📋 Переменные окружения:')
print(f'  BOT_TOKEN: {"✅ установлен" if os.getenv("BOT_TOKEN") else "❌ НЕ установлен"}')
print(f'  DATABASE_URL: {"✅ установлен" if os.getenv("DATABASE_URL") else "❌ НЕ установлен"}')
print(f'  WAREHOUSEMAN_ID: {os.getenv("WAREHOUSEMAN_ID", "❌ НЕ установлен")}')
print(f'  MANAGER_ID: {os.getenv("MANAGER_ID", "❌ НЕ установлен")}')
print(f'  TIMEZONE: {os.getenv("TIMEZONE", "Europe/Moscow")}')
print(f'  LOG_LEVEL: {os.getenv("LOG_LEVEL", "INFO")}')

