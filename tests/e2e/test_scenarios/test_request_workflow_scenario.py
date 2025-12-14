"""
E2E тест: Workflow заявки

Сценарии:
- Создание → В работе → Выполнено
- Создание → Отклонено
"""
import pytest
from datetime import datetime
from sqlalchemy import select

from bot.database.models import User, Request
from bot.services.request_service import RequestService
from bot.services.role_service import RoleService


class TestRequestWorkflowCompleted:
    """E2E тест: Создание → В работе → Выполнено"""
    
    @pytest.mark.asyncio
    async def test_workflow_new_to_completed(self, test_session, mock_config):
        """Полный цикл выполнения заявки"""
        
        # Подготовка
        role_service = RoleService()
        role_service.config = mock_config
        request_service = RequestService()
        
        employee = await role_service.get_or_create_user(test_session, 200001)
        
        # === Создание (new) ===
        request = await request_service.create_request(
            session=test_session,
            user_id=employee.id,
            category="Хозтовары и уборка",
            description="Нужна швабра и ведро для уборки кабинета",
            priority="normal",
            quantity=2
        )
        
        assert request.status == "new"
        assert request.completed_at is None
        
        # === В работе (in_progress) ===
        request.status = "in_progress"
        await test_session.flush()
        
        result = await test_session.execute(
            select(Request).where(Request.id == request.id)
        )
        in_progress = result.scalar_one()
        
        assert in_progress.status == "in_progress"
        
        # === Выполнено (completed) ===
        request.status = "completed"
        request.completed_at = datetime.now()
        await test_session.flush()
        
        result = await test_session.execute(
            select(Request).where(Request.id == request.id)
        )
        completed = result.scalar_one()
        
        assert completed.status == "completed"
        assert completed.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_workflow_tracks_time(self, test_session, mock_config):
        """Отслеживание времени выполнения"""
        
        role_service = RoleService()
        role_service.config = mock_config
        request_service = RequestService()
        
        employee = await role_service.get_or_create_user(test_session, 200002)
        
        # Создаем заявку
        request = await request_service.create_request(
            session=test_session,
            user_id=employee.id,
            category="Канцелярия",
            description="Тест времени",
            priority="normal"
        )
        
        created_at = request.created_at
        
        # Выполняем
        request.status = "completed"
        request.completed_at = datetime.now()
        await test_session.flush()
        
        # Проверяем что можно вычислить время выполнения
        duration = request.completed_at - created_at
        
        assert duration.total_seconds() >= 0


class TestRequestWorkflowRejected:
    """E2E тест: Создание → Отклонено"""
    
    @pytest.mark.asyncio
    async def test_workflow_new_to_rejected(self, test_session, mock_config):
        """Отклонение заявки"""
        
        role_service = RoleService()
        role_service.config = mock_config
        request_service = RequestService()
        
        employee = await role_service.get_or_create_user(test_session, 200003)
        
        # Создаем заявку
        request = await request_service.create_request(
            session=test_session,
            user_id=employee.id,
            category="ИТ-оборудование и расходники",
            description="Нужен новый сервер Dell PowerEdge",
            priority="normal"
        )
        
        assert request.status == "new"
        
        # Отклоняем
        request.status = "rejected"
        request.rejection_reason = "Требуется согласование с IT-отделом"
        await test_session.flush()
        
        result = await test_session.execute(
            select(Request).where(Request.id == request.id)
        )
        rejected = result.scalar_one()
        
        assert rejected.status == "rejected"
        assert rejected.rejection_reason is not None
    
    @pytest.mark.asyncio
    async def test_rejected_has_no_completed_at(self, test_session, mock_config):
        """Отклоненная заявка не имеет даты выполнения"""
        
        role_service = RoleService()
        role_service.config = mock_config
        request_service = RequestService()
        
        employee = await role_service.get_or_create_user(test_session, 200004)
        
        request = await request_service.create_request(
            session=test_session,
            user_id=employee.id,
            category="Другое",
            description="Тест отклонения",
            priority="normal"
        )
        
        request.status = "rejected"
        request.rejection_reason = "Тест"
        await test_session.flush()
        
        assert request.completed_at is None


class TestRequestWorkflowMultiple:
    """E2E тесты с несколькими заявками"""
    
    @pytest.mark.asyncio
    async def test_multiple_requests_different_statuses(self, test_session, mock_config):
        """Несколько заявок в разных статусах"""
        
        role_service = RoleService()
        role_service.config = mock_config
        request_service = RequestService()
        
        employee = await role_service.get_or_create_user(test_session, 200005)
        
        # Создаем заявки
        requests = []
        for i in range(4):
            r = await request_service.create_request(
                session=test_session,
                user_id=employee.id,
                category="Канцелярия",
                description=f"Заявка {i}",
                priority="normal"
            )
            requests.append(r)
        
        # Меняем статусы
        requests[0].status = "new"
        requests[1].status = "in_progress"
        requests[2].status = "completed"
        requests[2].completed_at = datetime.now()
        requests[3].status = "rejected"
        requests[3].rejection_reason = "Тест"
        
        await test_session.flush()
        
        # Проверяем распределение по статусам
        from sqlalchemy import func
        
        result = await test_session.execute(
            select(Request.status, func.count(Request.id))
            .where(Request.user_id == employee.id)
            .group_by(Request.status)
        )
        counts = {status: count for status, count in result.all()}
        
        assert counts.get("new") == 1
        assert counts.get("in_progress") == 1
        assert counts.get("completed") == 1
        assert counts.get("rejected") == 1
    
    @pytest.mark.asyncio
    async def test_requests_from_multiple_users(self, test_session, mock_config):
        """Заявки от разных пользователей"""
        
        role_service = RoleService()
        role_service.config = mock_config
        request_service = RequestService()
        
        # Создаем нескольких сотрудников
        users = []
        for i in range(3):
            user = await role_service.get_or_create_user(test_session, 300000 + i)
            users.append(user)
        
        # Каждый создает заявку
        for user in users:
            await request_service.create_request(
                session=test_session,
                user_id=user.id,
                category="Канцелярия",
                description=f"Заявка от пользователя {user.id}",
                priority="normal"
            )
        
        # Проверяем общее количество
        result = await test_session.execute(select(Request))
        all_requests = list(result.scalars().all())
        
        assert len(all_requests) >= 3
        
        # Проверяем что у каждого пользователя есть заявка
        for user in users:
            user_requests = [r for r in all_requests if r.user_id == user.id]
            assert len(user_requests) >= 1

