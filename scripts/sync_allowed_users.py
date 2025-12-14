"""Скрипт для синхронизации ID сотрудников из конфига в БД"""
import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot.config import get_config
from bot.database.engine import async_session_maker
from bot.database.models import AllowedUser
from sqlalchemy import select


async def sync_allowed_users():
    """Синхронизировать ID сотрудников из конфига в БД"""
    config = get_config()
    
    print(f"📋 ID из конфига:")
    print(f"  Руководитель: {config.manager_id}")
    print(f"  Завхоз: {config.warehouseman_id}")
    print(f"  Сотрудники: {config.allowed_employee_ids}")
    print()
    
    async with async_session_maker() as session:
        # Получаем всех пользователей из БД
        result = await session.execute(select(AllowedUser))
        db_users = {user.id: user for user in result.scalars().all()}
        
        added_count = 0
        updated_count = 0
        
        # Добавляем/обновляем пользователей из конфига
        for emp_id in config.allowed_employee_ids:
            if emp_id in db_users:
                # Пользователь уже есть в БД
                db_user = db_users[emp_id]
                print(f"✅ ID {emp_id} уже в БД: {db_user.full_name}")
            else:
                # Добавляем нового пользователя
                new_user = AllowedUser(
                    id=emp_id,
                    full_name=f"Сотрудник {emp_id}"  # Можно будет обновить позже
                )
                session.add(new_user)
                added_count += 1
                print(f"➕ Добавлен ID {emp_id} в БД")
        
        if added_count > 0:
            await session.commit()
            print(f"\n✅ Синхронизация завершена: добавлено {added_count} пользователей")
        else:
            print(f"\n✅ Все пользователи уже в БД, синхронизация не требуется")


if __name__ == "__main__":
    try:
        asyncio.run(sync_allowed_users())
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

