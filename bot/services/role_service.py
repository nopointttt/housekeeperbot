"""Сервис для работы с ролями пользователей"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.models import User
from bot.config import get_config


class RoleService:
    """Сервис для управления ролями пользователей"""
    
    def __init__(self):
        self.config = get_config()
    
    def get_role_by_id(self, user_id: int) -> str:
        """
        Определить роль пользователя по Telegram ID
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Роль: 'employee', 'warehouseman', или 'manager'
        """
        if user_id == self.config.warehouseman_id:
            return "warehouseman"
        elif user_id == self.config.manager_id:
            return "manager"
        else:
            return "employee"
    
    async def get_or_create_user(self, session: AsyncSession, user_id: int, username: Optional[str] = None) -> User:
        """
        Получить пользователя из БД или создать нового
        
        Args:
            session: Сессия БД
            user_id: Telegram ID пользователя
            username: Имя пользователя (опционально)
            
        Returns:
            Объект User
        """
        # Определяем роль
        role = self.get_role_by_id(user_id)
        
        # Ищем пользователя в БД
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user is None:
            # Создаем нового пользователя
            user = User(id=user_id, role=role)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        else:
            # Обновляем роль на случай, если ID изменился в конфиге
            if user.role != role:
                user.role = role
                await session.commit()
                await session.refresh(user)
        
        return user
    
    async def is_role(self, session: AsyncSession, user_id: int, role: str) -> bool:
        """
        Проверить, имеет ли пользователь указанную роль
        
        Args:
            session: Сессия БД
            user_id: Telegram ID пользователя
            role: Роль для проверки ('employee', 'warehouseman', 'manager')
            
        Returns:
            True если пользователь имеет указанную роль
        """
        user = await self.get_or_create_user(session, user_id)
        return user.role == role
    
    async def is_employee(self, session: AsyncSession, user_id: int) -> bool:
        """Проверить, является ли пользователь сотрудником"""
        return await self.is_role(session, user_id, "employee")
    
    async def is_warehouseman(self, session: AsyncSession, user_id: int) -> bool:
        """Проверить, является ли пользователь завхозом"""
        return await self.is_role(session, user_id, "warehouseman")
    
    async def is_manager(self, session: AsyncSession, user_id: int) -> bool:
        """Проверить, является ли пользователь руководителем"""
        return await self.is_role(session, user_id, "manager")


# Глобальный экземпляр сервиса
role_service = RoleService()

