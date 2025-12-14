"""Скрипт для проверки готовности к запуску бота"""
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def check_setup():
    """Проверить готовность к запуску"""
    print("🔍 Проверка готовности к запуску бота...\n")
    
    errors = []
    warnings = []
    
    # 1. Проверка .env файла
    env_path = Path('.env')
    if not env_path.exists():
        errors.append("❌ Файл .env не найден! Создайте его на основе .env.example")
    else:
        print("✅ Файл .env найден")
        
        # Проверка переменных
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = {
            'BOT_TOKEN': 'Токен бота от @BotFather',
            'DATABASE_URL': 'Строка подключения к БД',
            'WAREHOUSEMAN_ID': 'ID завхоза',
            'MANAGER_ID': 'ID руководителя'
        }
        
        for var, desc in required_vars.items():
            value = os.getenv(var)
            if not value:
                errors.append(f"❌ {var} не установлен в .env ({desc})")
            else:
                print(f"✅ {var} установлен")
        
        # Проверка опциональных переменных
        allowed_employees = os.getenv('ALLOWED_EMPLOYEE_IDS', '')
        if not allowed_employees:
            warnings.append("⚠️ ALLOWED_EMPLOYEE_IDS не установлен - доступ будет проверяться через БД")
        else:
            print(f"✅ ALLOWED_EMPLOYEE_IDS установлен: {allowed_employees}")
    
    # 2. Проверка конфигурации
    try:
        from bot.config import get_config
        config = get_config()
        print("\n✅ Конфигурация загружена успешно")
        print(f"   Завхоз ID: {config.warehouseman_id}")
        print(f"   Руководитель ID: {config.manager_id}")
        print(f"   Сотрудников в конфиге: {len(config.allowed_employee_ids)}")
    except Exception as e:
        errors.append(f"❌ Ошибка загрузки конфигурации: {e}")
    
    # 3. Проверка миграций
    try:
        import subprocess
        result = subprocess.run(
            ['python', '-m', 'alembic', 'current'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("\n✅ Миграции проверены")
        else:
            warnings.append("⚠️ Не удалось проверить миграции - убедитесь что БД доступна")
    except Exception as e:
        warnings.append(f"⚠️ Не удалось проверить миграции: {e}")
    
    # Вывод результатов
    print("\n" + "="*50)
    
    if errors:
        print("\n❌ ОШИБКИ (нужно исправить):")
        for error in errors:
            print(f"  {error}")
        print("\nИсправьте ошибки перед запуском бота!")
        return False
    
    if warnings:
        print("\n⚠️ ПРЕДУПРЕЖДЕНИЯ:")
        for warning in warnings:
            print(f"  {warning}")
    
    print("\n✅ Всё готово к запуску!")
    print("\nДля запуска выполните:")
    print("  python main.py")
    
    return True

if __name__ == "__main__":
    success = check_setup()
    sys.exit(0 if success else 1)

