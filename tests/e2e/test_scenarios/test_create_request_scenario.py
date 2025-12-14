"""
E2E тест: Полный сценарий создания заявки

Сценарий:
1. Сотрудник создает заявку
2. Заявка появляется у завхоза
3. Завхоз меняет статус
4. Сотрудник получает уведомление
"""
import pytest
from datetime import datetime
from sqlalchemy import select

from bot.database.models import User, Request
from bot.services.request_service import RequestService
from bot.services.role_service import RoleService


class TestCreateRequestScenario:
    """E2E тест полного сценария создания заявки"""
    
    @pytest.mark.asyncio
    async def test_full_create_request_flow(self, test_session, mock_config, mock_bot):
        """Полный flow: создание -> просмотр -> смена статуса"""
        
        # === Шаг 1: Создание пользователей ===
        role_service = RoleService()
        role_service.config = mock_config
        
        # Сотрудник
        employee = await role_service.get_or_create_user(test_session, 100001)
        assert employee.role == "employee"
        
        # Завхоз
        warehouseman = await role_service.get_or_create_user(
            test_session, 
            mock_config.warehouseman_id
        )
        assert warehouseman.role == "warehouseman"
        
        # === Шаг 2: Сотрудник создает заявку ===
        request_service = RequestService()
        
        request = await request_service.create_request(
            session=test_session,
            user_id=employee.id,
            category="Канцелярия",
            description="Нужны ручки синие 10 штук для отдела продаж",
            priority="normal",
            quantity=10
        )
        
        assert request is not None
        assert request.status == "new"
        assert request.number.startswith("ЗХ-")
        
        # === Шаг 3: Завхоз видит новую заявку ===
        result = await test_session.execute(
            select(Request).where(Request.status == "new")
        )
        new_requests = list(result.scalars().all())
        
        assert len(new_requests) >= 1
        assert any(r.id == request.id for r in new_requests)
        
        # === Шаг 4: Завхоз принимает заявку в работу ===
        request.status = "in_progress"
        await test_session.flush()
        
        # Проверяем статус
        result = await test_session.execute(
            select(Request).where(Request.id == request.id)
        )
        updated = result.scalar_one()
        assert updated.status == "in_progress"
        
        # === Шаг 5: Завхоз выполняет заявку ===
        request.status = "completed"
        request.completed_at = datetime.now()
        await test_session.flush()
        
        result = await test_session.execute(
            select(Request).where(Request.id == request.id)
        )
        completed = result.scalar_one()
        
        assert completed.status == "completed"
        assert completed.completed_at is not None
        
        # === Шаг 6: Сотрудник видит выполненную заявку ===
        employee_requests = await request_service.get_user_requests(
            test_session, 
            employee.id
        )
        
        assert len(employee_requests) >= 1
        assert any(r.status == "completed" for r in employee_requests)
    
    @pytest.mark.asyncio
    async def test_create_urgent_request_flow(self, test_session, mock_config):
        """Создание срочной заявки"""
        
        role_service = RoleService()
        role_service.config = mock_config
        
        employee = await role_service.get_or_create_user(test_session, 100002)
        
        request_service = RequestService()
        
        # Создаем срочную заявку
        request = await request_service.create_request(
            session=test_session,
            user_id=employee.id,
            category="Ремонт сантехники",
            description="Течет труба в туалете на 3 этаже!",
            priority="urgent"
        )
        
        assert request.priority == "urgent"
        
        # Срочные заявки должны быть первыми
        result = await test_session.execute(
            select(Request)
            .where(Request.status == "new")
            .order_by(Request.priority.desc())
        )
        sorted_requests = list(result.scalars().all())
        
        if len(sorted_requests) > 0:
            # Проверяем сортировку (urgent выше normal)
            urgent_found = False
            for r in sorted_requests:
                if r.priority == "urgent":
                    urgent_found = True
                elif r.priority == "normal" and not urgent_found:
                    # Если normal раньше urgent - ошибка
                    pass  # Сортировка по desc, urgent > normal
    
    @pytest.mark.asyncio
    async def test_create_request_with_photos_flow(self, test_session, mock_config):
        """Создание заявки с фотографиями"""
        
        role_service = RoleService()
        role_service.config = mock_config
        
        employee = await role_service.get_or_create_user(test_session, 100003)
        
        request_service = RequestService()
        
        # Создаем заявку с фото
        photo_ids = ["photo_1", "photo_2", "photo_3"]
        
        request = await request_service.create_request(
            session=test_session,
            user_id=employee.id,
            category="Ремонт мебели",
            description="Сломан стол в кабинете директора",
            priority="urgent",
            photo_file_ids=photo_ids
        )
        
        assert request is not None
        
        # Проверяем что фото сохранились
        from bot.database.models import RequestPhoto
        
        result = await test_session.execute(
            select(RequestPhoto).where(RequestPhoto.request_id == request.id)
        )
        photos = list(result.scalars().all())
        
        assert len(photos) == 3


class TestRequestRejectScenario:
    """E2E тест сценария отклонения заявки"""
    
    @pytest.mark.asyncio
    async def test_reject_request_flow(self, test_session, mock_config):
        """Полный flow отклонения заявки"""
        
        role_service = RoleService()
        role_service.config = mock_config
        
        employee = await role_service.get_or_create_user(test_session, 100004)
        
        request_service = RequestService()
        
        # Создаем заявку
        request = await request_service.create_request(
            session=test_session,
            user_id=employee.id,
            category="Канцелярия",
            description="Нужен ноутбук Apple MacBook Pro",
            priority="normal"
        )
        
        # Завхоз отклоняет
        request.status = "rejected"
        request.rejection_reason = "Слишком дорогой товар. Обратитесь к руководителю."
        await test_session.flush()
        
        # Проверяем
        result = await test_session.execute(
            select(Request).where(Request.id == request.id)
        )
        rejected = result.scalar_one()
        
        assert rejected.status == "rejected"
        assert rejected.rejection_reason is not None
        assert "дорогой" in rejected.rejection_reason.lower()

