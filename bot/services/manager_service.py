"""Сервис для работы руководителя с заявками и жалобами"""
import logging
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from bot.database.models import Request, Complaint

logger = logging.getLogger(__name__)


class ManagerService:
    """Сервис для просмотра заявок и жалоб руководителем"""
    
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
    
    async def get_requests_in_work_over_days(
        self,
        session: AsyncSession,
        days: int
    ) -> list[Request]:
        """
        Получить заявки в работе более указанного количества дней
        
        Args:
            session: Сессия БД
            days: Количество дней (3 или 7)
            
        Returns:
            Список заявок в работе более указанного количества дней
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        result = await session.execute(
            select(Request)
            .where(
                and_(
                    Request.status == "in_progress",
                    Request.updated_at <= cutoff_date
                )
            )
            .options(selectinload(Request.user), selectinload(Request.photos))
            .order_by(Request.updated_at.asc())  # Сначала самые старые
        )
        return list(result.scalars().all())
    
    async def get_period_report(
        self,
        session: AsyncSession,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """
        Получить отчет за период
        
        Args:
            session: Сессия БД
            start_date: Начало периода
            end_date: Конец периода
            
        Returns:
            Словарь с статистикой:
            {
                'new': количество новых,
                'in_progress': количество в работе,
                'completed': количество выполненных,
                'rejected': количество отклоненных,
                'total': общее количество
            }
        """
        # Подсчет по статусам
        new_count = await session.execute(
            select(func.count(Request.id))
            .where(
                and_(
                    Request.status == "new",
                    Request.created_at >= start_date,
                    Request.created_at <= end_date
                )
            )
        )
        
        in_progress_count = await session.execute(
            select(func.count(Request.id))
            .where(
                and_(
                    Request.status == "in_progress",
                    Request.created_at >= start_date,
                    Request.created_at <= end_date
                )
            )
        )
        
        completed_count = await session.execute(
            select(func.count(Request.id))
            .where(
                and_(
                    Request.status == "completed",
                    Request.completed_at >= start_date,
                    Request.completed_at <= end_date
                )
            )
        )
        
        rejected_count = await session.execute(
            select(func.count(Request.id))
            .where(
                and_(
                    Request.status == "rejected",
                    Request.updated_at >= start_date,
                    Request.updated_at <= end_date
                )
            )
        )
        
        total_count = await session.execute(
            select(func.count(Request.id))
            .where(
                and_(
                    Request.created_at >= start_date,
                    Request.created_at <= end_date
                )
            )
        )
        
        return {
            'new': new_count.scalar() or 0,
            'in_progress': in_progress_count.scalar() or 0,
            'completed': completed_count.scalar() or 0,
            'rejected': rejected_count.scalar() or 0,
            'total': total_count.scalar() or 0
        }
    
    async def get_all_requests(self, session: AsyncSession, limit: Optional[int] = None) -> list[Request]:
        """
        Получить все заявки
        
        Args:
            session: Сессия БД
            limit: Максимальное количество заявок (опционально)
            
        Returns:
            Список всех заявок, отсортированный по дате создания (новые сначала)
        """
        query = (
            select(Request)
            .options(selectinload(Request.user), selectinload(Request.photos))
            .order_by(Request.created_at.desc())
        )
        
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def get_all_complaints(self, session: AsyncSession) -> list[Complaint]:
        """
        Получить все жалобы на завхоза
        
        Args:
            session: Сессия БД
            
        Returns:
            Список жалоб, отсортированный по дате создания (новые сначала)
        """
        logger.debug("Запрос всех жалоб из БД")
        result = await session.execute(
            select(Complaint)
            .options(selectinload(Complaint.user))
            .order_by(Complaint.created_at.desc())
        )
        complaints = list(result.scalars().all())
        logger.info(f"Найдено жалоб: {len(complaints)}")
        if complaints:
            logger.debug(f"ID жалоб: {[c.id for c in complaints]}")
        return complaints
    
    async def get_complaint_by_id(
        self,
        session: AsyncSession,
        complaint_id: int
    ) -> Optional[Complaint]:
        """
        Получить жалобу по ID
        
        Args:
            session: Сессия БД
            complaint_id: ID жалобы
            
        Returns:
            Жалоба или None
        """
        result = await session.execute(
            select(Complaint)
            .where(Complaint.id == complaint_id)
            .options(selectinload(Complaint.user))
        )
        return result.scalar_one_or_none()


# Глобальный экземпляр сервиса
manager_service = ManagerService()

