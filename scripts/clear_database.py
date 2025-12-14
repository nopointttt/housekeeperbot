"""
Скрипт для полной очистки базы данных
Удаляет все данные из всех таблиц
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bot.database.engine import engine
from sqlalchemy import text


async def clear_database():
    """Очистить всю базу данных"""
    print("🔄 Начинаю очистку базы данных...")
    
    async with engine.begin() as conn:
        # Удаляем данные в правильном порядке (с учетом внешних ключей)
        print("  📤 Удаляю фотографии заявок...")
        await conn.execute(text("DELETE FROM request_photos"))
        
        print("  📤 Удаляю жалобы...")
        await conn.execute(text("DELETE FROM complaints"))
        
        print("  📤 Удаляю заявки...")
        await conn.execute(text("DELETE FROM requests"))
        
        print("  📤 Удаляю товары склада...")
        await conn.execute(text("DELETE FROM warehouse_items"))
        
        print("  📤 Удаляю пользователей...")
        await conn.execute(text("DELETE FROM users"))
        
        # Сбрасываем счетчики автоинкремента (для PostgreSQL)
        print("  🔄 Сбрасываю счетчики автоинкремента...")
        await conn.execute(text("ALTER SEQUENCE IF EXISTS requests_id_seq RESTART WITH 1"))
        await conn.execute(text("ALTER SEQUENCE IF EXISTS request_photos_id_seq RESTART WITH 1"))
        await conn.execute(text("ALTER SEQUENCE IF EXISTS warehouse_items_id_seq RESTART WITH 1"))
        await conn.execute(text("ALTER SEQUENCE IF EXISTS complaints_id_seq RESTART WITH 1"))
    
    print("✅ База данных успешно очищена!")


async def main():
    """Главная функция"""
    try:
        await clear_database()
    except Exception as e:
        print(f"❌ Ошибка при очистке базы данных: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

