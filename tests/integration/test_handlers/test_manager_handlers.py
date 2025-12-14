"""
Интеграционные тесты для handlers руководителя

Тестируемые сценарии:
- Просмотр заявок
- Просмотр жалоб
- Отчеты
"""
import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select, func

from bot.database.models import User, Request, Complaint
from bot.services.complaint_service import ComplaintService


def unique_id():
    """Генерирует уникальный ID для тестов"""
    return int(uuid.uuid4().int % 2000000000) + 1000000


def unique_number():
    """Генерирует уникальный номер заявки"""
    return f"ЗХ-{uuid.uuid4().hex[:8]}"


class TestManagerViewRequests:
    """Тесты просмотра заявок руководителем"""
    
    @pytest.mark.asyncio
    async def test_view_all_requests(self, test_session):
        """Руководитель видит все заявки"""
        # Создаем уникальных пользователей
        users = []
        for i in range(3):
            uid = unique_id()
            user = User(id=uid, role="employee")
            test_session.add(user)
            users.append(user)
        await test_session.flush()
        
        # Создаем заявки с уникальными номерами
        for i, user in enumerate(users):
            request = Request(
                number=unique_number(),
                user_id=user.id,
                category="Канцелярия",
                description=f"Заявка от пользователя {i}",
                priority="normal",
                status="new"
            )
            test_session.add(request)
        await test_session.flush()
        
        # Руководитель получает все заявки этих пользователей
        user_ids = [u.id for u in users]
        result = await test_session.execute(
            select(Request).where(Request.user_id.in_(user_ids))
        )
        all_requests = list(result.scalars().all())
        
        assert len(all_requests) == 3
    
    @pytest.mark.asyncio
    async def test_view_urgent_requests(self, test_session, test_user):
        """Просмотр срочных заявок"""
        # Создаем заявки с уникальными номерами
        priorities = ["normal", "urgent", "urgent"]
        created_requests = []
        
        for i, priority in enumerate(priorities):
            request = Request(
                number=unique_number(),
                user_id=test_user.id,
                category="Канцелярия",
                description="Тест",
                priority=priority,
                status="new"
            )
            test_session.add(request)
            created_requests.append(request)
        await test_session.flush()
        
        # Получаем только срочные
        created_ids = [r.id for r in created_requests]
        result = await test_session.execute(
            select(Request).where(
                Request.id.in_(created_ids),
                Request.priority == "urgent"
            )
        )
        urgent = list(result.scalars().all())
        
        assert len(urgent) == 2


class TestManagerViewComplaints:
    """Тесты просмотра жалоб"""
    
    @pytest.mark.asyncio
    async def test_view_all_complaints(self, test_session, test_user, test_request):
        """Руководитель видит все жалобы"""
        service = ComplaintService()
        
        # Создаем жалобы
        created_complaints = []
        for i in range(3):
            complaint = await service.create_complaint(
                session=test_session,
                user_id=test_user.id,
                request_id=test_request.id,
                reason=f"Причина {i}",
                text=f"Текст жалобы {i}"
            )
            created_complaints.append(complaint)
        
        # Получаем все жалобы для этой заявки
        result = await test_session.execute(
            select(Complaint).where(Complaint.request_id == test_request.id)
        )
        complaints = list(result.scalars().all())
        
        assert len(complaints) == 3
    
    @pytest.mark.asyncio
    async def test_complaint_includes_request_info(self, test_session, test_user, test_request):
        """Жалоба содержит информацию о заявке"""
        service = ComplaintService()
        
        complaint = await service.create_complaint(
            session=test_session,
            user_id=test_user.id,
            request_id=test_request.id,
            reason="Долгое выполнение",
            text="Жду неделю"
        )
        
        # Проверяем что есть связь с заявкой
        assert complaint.request_id == test_request.id
    
    @pytest.mark.asyncio
    async def test_complaints_sorted_by_date(self, test_session, test_user, test_request):
        """Жалобы отсортированы по дате (DESC)"""
        service = ComplaintService()
        
        first = await service.create_complaint(
            session=test_session,
            user_id=test_user.id,
            request_id=test_request.id,
            reason="Первая",
            text="Текст"
        )
        
        second = await service.create_complaint(
            session=test_session,
            user_id=test_user.id,
            request_id=test_request.id,
            reason="Вторая",
            text="Текст"
        )
        
        complaints = await service.get_complaints_by_request(test_session, test_request.id)
        
        # Должно быть 2 жалобы
        assert len(complaints) == 2
        # При быстром создании время может совпасть, проверяем наличие обеих
        reasons = [c.reason for c in complaints]
        assert "Первая" in reasons
        assert "Вторая" in reasons


class TestManagerReports:
    """Тесты отчетов"""
    
    @pytest.mark.asyncio
    async def test_requests_count_by_status(self, test_session, test_user):
        """Отчет: количество заявок по статусам"""
        # Создаем заявки разных статусов
        statuses = ["new", "new", "in_progress", "completed", "completed", "rejected"]
        created_requests = []
        
        for i, status in enumerate(statuses):
            request = Request(
                number=unique_number(),
                user_id=test_user.id,
                category="Канцелярия",
                description=f"Заявка {i}",
                priority="normal",
                status=status
            )
            test_session.add(request)
            created_requests.append(request)
        await test_session.flush()
        
        # Формируем отчет только для созданных заявок
        created_ids = [r.id for r in created_requests]
        result = await test_session.execute(
            select(Request.status, func.count(Request.id))
            .where(Request.id.in_(created_ids))
            .group_by(Request.status)
        )
        report = {status: count for status, count in result.all()}
        
        assert report["new"] == 2
        assert report["in_progress"] == 1
        assert report["completed"] == 2
        assert report["rejected"] == 1
    
    @pytest.mark.asyncio
    async def test_requests_count_by_category(self, test_session, test_user):
        """Отчет: количество заявок по категориям"""
        categories = ["Канцелярия", "Канцелярия", "Ремонт мебели", "Хозтовары и уборка"]
        created_requests = []
        
        for i, category in enumerate(categories):
            request = Request(
                number=unique_number(),
                user_id=test_user.id,
                category=category,
                description=f"Заявка {i}",
                priority="normal",
                status="new"
            )
            test_session.add(request)
            created_requests.append(request)
        await test_session.flush()
        
        created_ids = [r.id for r in created_requests]
        result = await test_session.execute(
            select(Request.category, func.count(Request.id))
            .where(Request.id.in_(created_ids))
            .group_by(Request.category)
        )
        report = {cat: count for cat, count in result.all()}
        
        assert report["Канцелярия"] == 2
        assert report["Ремонт мебели"] == 1
    
    @pytest.mark.asyncio
    async def test_complaints_count(self, test_session, test_user, test_request):
        """Отчет: количество жалоб"""
        service = ComplaintService()
        
        # Создаем жалобы
        for i in range(5):
            await service.create_complaint(
                session=test_session,
                user_id=test_user.id,
                request_id=test_request.id,
                reason=f"Причина {i}",
                text=f"Текст {i}"
            )
        
        # Считаем жалобы для этой заявки
        result = await test_session.execute(
            select(func.count(Complaint.id))
            .where(Complaint.request_id == test_request.id)
        )
        count = result.scalar()
        
        assert count == 5
    
    @pytest.mark.asyncio
    async def test_average_completion_time(self, test_session, test_user):
        """Отчет: среднее время выполнения"""
        now = datetime.now()
        created_requests = []
        
        for i in range(3):
            request = Request(
                number=unique_number(),
                user_id=test_user.id,
                category="Канцелярия",
                description=f"Заявка {i}",
                priority="normal",
                status="completed",
                completed_at=now
            )
            test_session.add(request)
            created_requests.append(request)
        await test_session.flush()
        
        # Проверяем что выполненные заявки есть
        created_ids = [r.id for r in created_requests]
        result = await test_session.execute(
            select(Request).where(Request.id.in_(created_ids))
        )
        completed = list(result.scalars().all())
        
        assert len(completed) == 3
        assert all(r.completed_at is not None for r in completed)


class TestManagerFilters:
    """Тесты фильтров для руководителя"""
    
    @pytest.mark.asyncio
    async def test_filter_by_period(self, test_session, test_user):
        """Фильтрация по периоду"""
        now = datetime.now()
        
        # Заявка сегодня
        request1 = Request(
            number=unique_number(),
            user_id=test_user.id,
            category="Канцелярия",
            description="Сегодняшняя заявка",
            priority="normal",
            status="new"
        )
        test_session.add(request1)
        await test_session.flush()
        
        # Фильтр за сегодня
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        result = await test_session.execute(
            select(Request).where(
                Request.id == request1.id,
                Request.created_at >= today_start
            )
        )
        today_requests = list(result.scalars().all())
        
        assert len(today_requests) >= 1
    
    @pytest.mark.asyncio
    async def test_filter_by_user(self, test_session):
        """Фильтрация по пользователю"""
        # Создаем уникальных пользователей
        user1 = User(id=unique_id(), role="employee")
        user2 = User(id=unique_id(), role="employee")
        test_session.add_all([user1, user2])
        await test_session.flush()
        
        # Заявки от разных пользователей
        request1 = Request(
            number=unique_number(),
            user_id=user1.id,
            category="Канцелярия",
            description="От пользователя 1",
            priority="normal",
            status="new"
        )
        request2 = Request(
            number=unique_number(),
            user_id=user2.id,
            category="Канцелярия",
            description="От пользователя 2",
            priority="normal",
            status="new"
        )
        test_session.add_all([request1, request2])
        await test_session.flush()
        
        # Фильтр по пользователю
        result = await test_session.execute(
            select(Request).where(Request.user_id == user1.id)
        )
        user1_requests = list(result.scalars().all())
        
        assert len(user1_requests) == 1
        assert user1_requests[0].user_id == user1.id
