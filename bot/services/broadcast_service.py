"""Сервис для рассылок"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.models import User


class BroadcastService:
    """Сервис для рассылок сообщений"""
    
    async def get_all_employees(self, session: AsyncSession) -> List[User]:
        """
        Получить всех пользователей (роль employee), исключая техника и руководителя
        
        Args:
            session: Сессия БД
            
        Returns:
            Список пользователей
        """
        from bot.config import get_config
        config = get_config()
        
        result = await session.execute(
            select(User)
            .where(User.role == "employee")
            .where(User.id != config.warehouseman_id)
            .where(User.id != config.manager_id)
        )
        return list(result.scalars().all())
    
    async def get_all_users(self, session: AsyncSession) -> List[User]:
        """
        Получить всех пользователей бота
        
        Args:
            session: Сессия БД
            
        Returns:
            Список всех пользователей
        """
        result = await session.execute(select(User))
        return list(result.scalars().all())


# Глобальный экземпляр сервиса
broadcast_service = BroadcastService()

