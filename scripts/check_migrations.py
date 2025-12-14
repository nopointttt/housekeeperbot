"""Проверка состояния миграций и таблиц БД"""
import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot.database.engine import async_session_maker
from sqlalchemy import text, inspect


async def check_migrations():
    """Проверить состояние миграций и таблиц"""
    async with async_session_maker() as session:
        print("🔍 Проверка миграций и таблиц БД...\n")
        
        # Проверяем таблицу allowed_users
        try:
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'allowed_users'
                );
            """))
            exists = result.scalar()
            
            if exists:
                print("✅ Таблица 'allowed_users' существует")
                
                # Проверяем структуру таблицы
                result = await session.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'allowed_users'
                    ORDER BY ordinal_position;
                """))
                columns = result.fetchall()
                
                print("\n📋 Структура таблицы 'allowed_users':")
                for col_name, col_type in columns:
                    print(f"  - {col_name}: {col_type}")
                
                # Проверяем количество записей
                result = await session.execute(text("SELECT COUNT(*) FROM allowed_users"))
                count = result.scalar()
                print(f"\n📊 Записей в таблице: {count}")
                
            else:
                print("❌ Таблица 'allowed_users' НЕ существует!")
                print("   Нужно применить миграции: python -m alembic upgrade head")
                
        except Exception as e:
            print(f"❌ Ошибка при проверке таблицы: {e}")
            print("   Возможно, БД недоступна или миграции не применены")
        
        # Проверяем другие ключевые таблицы
        print("\n🔍 Проверка других таблиц:")
        tables_to_check = ['users', 'requests', 'complaints', 'request_photos']
        
        for table in tables_to_check:
            try:
                result = await session.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    );
                """))
                exists = result.scalar()
                status = "✅" if exists else "❌"
                print(f"  {status} {table}")
            except:
                print(f"  ❌ {table} (ошибка проверки)")


if __name__ == "__main__":
    try:
        asyncio.run(check_migrations())
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

