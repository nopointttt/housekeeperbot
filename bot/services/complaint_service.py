"""Сервис для работы с жалобами"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from bot.database.models import Complaint, Request

logger = logging.getLogger(__name__)


class ComplaintService:
    """Сервис для управления жалобами"""
    
    async def create_complaint(
        self,
        session: AsyncSession,
        user_id: int,
        request_id: int,
        reason: str,
        text: str
    ) -> Complaint:
        """
        Создать жалобу
        
        Args:
            session: Сессия БД
            user_id: Telegram ID пользователя
            request_id: ID заявки
            reason: Причина жалобы
            text: Текст жалобы
            
        Returns:
            Созданная жалоба
        """
        complaint = Complaint(
            user_id=user_id,
            request_id=request_id,
            reason=reason,
            text=text
        )
        
        session.add(complaint)
        logger.debug(f"Жалоба добавлена в сессию: user_id={user_id}, request_id={request_id}")
        
        # Используем flush() вместо commit() - commit сделает middleware
        # flush() сохраняет изменения в БД, но не завершает транзакцию
        await session.flush()
        logger.debug(f"Жалоба отправлена в БД (flush), ID будет присвоен")
        
        # Получаем ID после flush
        await session.refresh(complaint)
        logger.info(f"Жалоба создана: ID={complaint.id}, user_id={user_id}, request_id={request_id}")
        
        return complaint
    
    async def get_complaint_by_id(
        self,
        session: AsyncSession,
        complaint_id: int
    ) -> Optional[Complaint]:
        """Получить жалобу по ID"""
        result = await session.execute(
            select(Complaint)
            .where(Complaint.id == complaint_id)
            .options(selectinload(Complaint.user), selectinload(Complaint.request))
        )
        return result.scalar_one_or_none()
    
    async def get_complaints_by_request(
        self,
        session: AsyncSession,
        request_id: int
    ) -> list[Complaint]:
        """Получить все жалобы по заявке"""
        result = await session.execute(
            select(Complaint)
            .where(Complaint.request_id == request_id)
            .options(selectinload(Complaint.user))
            .order_by(Complaint.created_at.desc())
        )
        return list(result.scalars().all())


# Глобальный экземпляр сервиса
complaint_service = ComplaintService()

