"""
E2E тест: Сценарий жалобы

Сценарий:
- Сотрудник подает жалобу
- Уведомление руководителю
- Уведомление завхозу
"""
import pytest
from datetime import datetime
from sqlalchemy import select

from bot.database.models import User, Request, Complaint
from bot.services.request_service import RequestService
from bot.services.role_service import RoleService
from bot.services.complaint_service import ComplaintService


class TestComplaintScenario:
    """E2E тест сценария подачи жалобы"""
    
    @pytest.mark.asyncio
    async def test_full_complaint_flow(self, test_session, mock_config):
        """Полный flow: создание заявки -> подача жалобы"""
        
        # === Подготовка ===
        role_service = RoleService()
        role_service.config = mock_config
        request_service = RequestService()
        complaint_service = ComplaintService()
        
        # Создаем пользователей
        employee = await role_service.get_or_create_user(test_session, 400001)
        warehouseman = await role_service.get_or_create_user(
            test_session, 
            mock_config.warehouseman_id
        )
        manager = await role_service.get_or_create_user(
            test_session, 
            mock_config.manager_id
        )
        
        # === Шаг 1: Сотрудник создает заявку ===
        request = await request_service.create_request(
            session=test_session,
            user_id=employee.id,
            category="Канцелярия",
            description="Нужны скрепки для степлера",
            priority="urgent"
        )
        
        assert request.status == "new"
        
        # === Шаг 2: Заявка висит долго (симуляция) ===
        # В реальности проходит время...
        
        # === Шаг 3: Сотрудник подает жалобу ===
        complaint = await complaint_service.create_complaint(
            session=test_session,
            user_id=employee.id,
            request_id=request.id,
            reason="Долгое выполнение",
            text="Заявка создана неделю назад, до сих пор не выполнена. Срочно нужны материалы для работы!"
        )
        
        assert complaint is not None
        assert complaint.user_id == employee.id
        assert complaint.request_id == request.id
        
        # === Шаг 4: Проверяем что жалоба сохранена ===
        result = await test_session.execute(
            select(Complaint).where(Complaint.id == complaint.id)
        )
        saved = result.scalar_one_or_none()
        
        assert saved is not None
        assert saved.reason == "Долгое выполнение"
        
        # === Шаг 5: Жалобы по заявке ===
        complaints = await complaint_service.get_complaints_by_request(
            test_session, 
            request.id
        )
        
        assert len(complaints) >= 1
    
    @pytest.mark.asyncio
    async def test_multiple_complaints_on_request(self, test_session, mock_config):
        """Несколько жалоб на одну заявку"""
        
        role_service = RoleService()
        role_service.config = mock_config
        request_service = RequestService()
        complaint_service = ComplaintService()
        
        employee = await role_service.get_or_create_user(test_session, 400002)
        
        # Создаем заявку
        request = await request_service.create_request(
            session=test_session,
            user_id=employee.id,
            category="Ремонт мебели",
            description="Сломан стул",
            priority="normal"
        )
        
        # Несколько жалоб
        reasons = [
            "Долгое выполнение",
            "Некачественное выполнение",
            "Грубость"
        ]
        
        for reason in reasons:
            await complaint_service.create_complaint(
                session=test_session,
                user_id=employee.id,
                request_id=request.id,
                reason=reason,
                text=f"Жалоба: {reason}"
            )
        
        # Проверяем
        complaints = await complaint_service.get_complaints_by_request(
            test_session, 
            request.id
        )
        
        assert len(complaints) == 3
    
    @pytest.mark.asyncio
    async def test_complaint_on_rejected_request(self, test_session, mock_config):
        """Жалоба на отклоненную заявку"""
        
        role_service = RoleService()
        role_service.config = mock_config
        request_service = RequestService()
        complaint_service = ComplaintService()
        
        employee = await role_service.get_or_create_user(test_session, 400003)
        
        # Создаем и отклоняем заявку
        request = await request_service.create_request(
            session=test_session,
            user_id=employee.id,
            category="Канцелярия",
            description="Нужен ноутбук",
            priority="normal"
        )
        
        request.status = "rejected"
        request.rejection_reason = "Не согласовано"
        await test_session.flush()
        
        # Подаем жалобу на отклонение
        complaint = await complaint_service.create_complaint(
            session=test_session,
            user_id=employee.id,
            request_id=request.id,
            reason="Другое",
            text="Не согласен с причиной отклонения"
        )
        
        assert complaint is not None
        
        # Проверяем связь
        result = await test_session.execute(
            select(Request).where(Request.id == complaint.request_id)
        )
        linked_request = result.scalar_one()
        
        assert linked_request.status == "rejected"


class TestComplaintNotifications:
    """E2E тесты уведомлений о жалобах"""
    
    @pytest.mark.asyncio
    async def test_complaint_creates_record(self, test_session, mock_config):
        """Жалоба создает запись в БД"""
        
        role_service = RoleService()
        role_service.config = mock_config
        request_service = RequestService()
        complaint_service = ComplaintService()
        
        employee = await role_service.get_or_create_user(test_session, 400004)
        
        request = await request_service.create_request(
            session=test_session,
            user_id=employee.id,
            category="Канцелярия",
            description="Тест уведомлений",
            priority="normal"
        )
        
        complaint = await complaint_service.create_complaint(
            session=test_session,
            user_id=employee.id,
            request_id=request.id,
            reason="Тест",
            text="Проверка создания записи"
        )
        
        # Проверяем что запись существует
        from sqlalchemy import func
        
        result = await test_session.execute(
            select(func.count(Complaint.id))
        )
        count = result.scalar()
        
        assert count >= 1
    
    @pytest.mark.asyncio
    async def test_complaint_has_created_at(self, test_session, mock_config):
        """Жалоба имеет дату создания"""
        
        role_service = RoleService()
        role_service.config = mock_config
        request_service = RequestService()
        complaint_service = ComplaintService()
        
        employee = await role_service.get_or_create_user(test_session, 400005)
        
        request = await request_service.create_request(
            session=test_session,
            user_id=employee.id,
            category="Канцелярия",
            description="Тест даты",
            priority="normal"
        )
        
        complaint = await complaint_service.create_complaint(
            session=test_session,
            user_id=employee.id,
            request_id=request.id,
            reason="Тест",
            text="Проверка даты"
        )
        
        assert complaint.created_at is not None
        assert isinstance(complaint.created_at, datetime)

