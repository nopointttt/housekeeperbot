"""Сервис для работы завхоза с заявками"""
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from bot.database.models import Request


class WarehousemanService:
    """Сервис для управления заявками завхозом"""
    
    async def get_new_requests_count(self, session: AsyncSession) -> int:
        """
        Получить количество новых заявок
        
        Args:
            session: Сессия БД
            
        Returns:
            Количество новых заявок
        """
        result = await session.execute(
            select(func.count(Request.id))
            .where(Request.status == "new")
        )
        return result.scalar() or 0
    
    async def get_new_requests(self, session: AsyncSession) -> list[Request]:
        """
        Получить все новые заявки
        
        Args:
            session: Сессия БД
            
        Returns:
            Список новых заявок
        """
        result = await session.execute(
            select(Request)
            .where(Request.status == "new")
            .options(selectinload(Request.user), selectinload(Request.photos))
            .order_by(
                Request.priority.desc(),  # Сначала срочные
                Request.created_at.asc()  # Потом по дате создания
            )
        )
        return list(result.scalars().all())
    
    async def get_requests_today(self, session: AsyncSession) -> list[Request]:
        """
        Получить все заявки за сегодня
        
        Args:
            session: Сессия БД
            
        Returns:
            Список заявок за сегодня
        """
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        result = await session.execute(
            select(Request)
            .where(Request.created_at >= today_start)
            .options(selectinload(Request.user), selectinload(Request.photos))
            .order_by(Request.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_requests_week(self, session: AsyncSession) -> list[Request]:
        """
        Получить все заявки за неделю
        
        Args:
            session: Сессия БД
            
        Returns:
            Список заявок за неделю
        """
        week_start = datetime.now() - timedelta(days=7)
        
        result = await session.execute(
            select(Request)
            .where(Request.created_at >= week_start)
            .options(selectinload(Request.user), selectinload(Request.photos))
            .order_by(Request.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_all_requests(self, session: AsyncSession, limit: Optional[int] = None) -> list[Request]:
        """
        Получить все заявки
        
        Args:
            session: Сессия БД
            limit: Максимальное количество заявок (по умолчанию все)
            
        Returns:
            Список всех заявок, отсортированный по дате создания (новые сначала)
        """
        query = (
            select(Request)
            .options(selectinload(Request.user), selectinload(Request.photos))
            .order_by(
                Request.priority.desc(),  # Сначала срочные
                Request.created_at.desc()  # Потом новые
            )
        )
        
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def take_request_in_work(
        self,
        session: AsyncSession,
        request_id: int
    ) -> Optional[Request]:
        """
        Взять заявку в работу
        
        Args:
            session: Сессия БД
            request_id: ID заявки
            
        Returns:
            Обновленная заявка или None
        """
        request = await session.get(Request, request_id)
        
        if not request:
            return None
        
        if request.status != "new":
            return None  # Можно взять в работу только новые заявки
        
        request.status = "in_progress"
        request.updated_at = datetime.now()
        
        # Используем flush() вместо commit() - commit сделает middleware
        await session.flush()
        await session.refresh(request)
        
        return request
    
    async def complete_request(
        self,
        session: AsyncSession,
        request_id: int
    ) -> Optional[Request]:
        """
        Завершить заявку
        
        Args:
            session: Сессия БД
            request_id: ID заявки
            
        Returns:
            Обновленная заявка или None
        """
        request = await session.get(Request, request_id)
        
        if not request:
            return None
        
        if request.status not in ["new", "in_progress"]:
            return None  # Можно завершить только новые или в работе
        
        request.status = "completed"
        request.completed_at = datetime.now()
        request.updated_at = datetime.now()
        
        # Используем flush() вместо commit() - commit сделает middleware
        await session.flush()
        await session.refresh(request)
        
        return request
    
    async def reject_request(
        self,
        session: AsyncSession,
        request_id: int,
        reason: str
    ) -> Optional[Request]:
        """
        Отклонить заявку
        
        Args:
            session: Сессия БД
            request_id: ID заявки
            reason: Причина отклонения
            
        Returns:
            Обновленная заявка или None
        """
        request = await session.get(Request, request_id)
        
        if not request:
            return None
        
        if request.status not in ["new", "in_progress"]:
            return None  # Можно отклонить только новые или в работе
        
        request.status = "rejected"
        request.rejection_reason = reason
        request.updated_at = datetime.now()
        
        # Используем flush() вместо commit() - commit сделает middleware
        await session.flush()
        await session.refresh(request)
        
        return request


# Глобальный экземпляр сервиса
warehouseman_service = WarehousemanService()

