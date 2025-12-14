"""
E2E тесты полных пользовательских сценариев

Комплексные тесты, объединяющие несколько модулей
"""
import pytest
from datetime import datetime
from sqlalchemy import select, func

from bot.database.models import User, Request, Complaint, WarehouseItem
from bot.services.request_service import RequestService
from bot.services.role_service import RoleService
from bot.services.complaint_service import ComplaintService
from bot.services.warehouse_service import WarehouseService


class TestFullUserJourney:
    """E2E тест полного пути пользователя"""
    
    @pytest.mark.asyncio
    async def test_employee_journey(self, test_session, mock_config):
        """Полный путь сотрудника: регистрация -> заявка -> отслеживание"""
        
        role_service = RoleService()
        role_service.config = mock_config
        request_service = RequestService()
        
        # 1. Новый пользователь приходит в бот
        employee = await role_service.get_or_create_user(test_session, 500001)
        assert employee.role == "employee"
        
        # 2. Создает первую заявку
        request1 = await request_service.create_request(
            session=test_session,
            user_id=employee.id,
            category="Канцелярия",
            description="Первая заявка",
            priority="normal"
        )
        
        # 3. Создает вторую заявку
        request2 = await request_service.create_request(
            session=test_session,
            user_id=employee.id,
            category="Хозтовары и уборка",
            description="Вторая заявка",
            priority="urgent"
        )
        
        # 4. Проверяет список своих заявок
        my_requests = await request_service.get_user_requests(
            test_session, 
            employee.id
        )
        assert len(my_requests) == 2
        
        # 5. Заявки выполняются
        request1.status = "completed"
        request1.completed_at = datetime.now()
        await test_session.flush()
        
        # 6. Проверяет статусы
        my_requests = await request_service.get_user_requests(
            test_session, 
            employee.id
        )
        statuses = {r.status for r in my_requests}
        assert "completed" in statuses
        assert "new" in statuses
    
    @pytest.mark.asyncio
    async def test_warehouseman_journey(self, test_session, mock_config):
        """Полный путь завхоза: обработка заявок"""
        
        role_service = RoleService()
        role_service.config = mock_config
        request_service = RequestService()
        warehouse_service = WarehouseService()
        
        # Завхоз входит в систему
        warehouseman = await role_service.get_or_create_user(
            test_session, 
            mock_config.warehouseman_id
        )
        assert warehouseman.role == "warehouseman"
        
        # Создаем заявки от сотрудников
        employee1 = await role_service.get_or_create_user(test_session, 500002)
        employee2 = await role_service.get_or_create_user(test_session, 500003)
        
        r1 = await request_service.create_request(
            session=test_session,
            user_id=employee1.id,
            category="Канцелярия",
            description="Заявка 1",
            priority="normal"
        )
        
        r2 = await request_service.create_request(
            session=test_session,
            user_id=employee2.id,
            category="Канцелярия",
            description="Заявка 2 (срочная)",
            priority="urgent"
        )
        
        # Завхоз видит новые заявки
        result = await test_session.execute(
            select(Request).where(Request.status == "new")
        )
        new_requests = list(result.scalars().all())
        assert len(new_requests) >= 2
        
        # Обрабатывает срочную первой
        r2.status = "in_progress"
        await test_session.flush()
        
        # Выполняет
        r2.status = "completed"
        r2.completed_at = datetime.now()
        await test_session.flush()
        
        # Управляет складом
        item = await warehouse_service.create_item(
            test_session,
            name="Бумага А4",
            min_quantity=20
        )
        
        await warehouse_service.add_quantity(test_session, item.id, 100)
        
        # Проверяет остатки
        items = await warehouse_service.get_all_items(test_session)
        assert len(items) >= 1


class TestComplexScenarios:
    """Сложные сценарии взаимодействия"""
    
    @pytest.mark.asyncio
    async def test_request_with_complaint_flow(self, test_session, mock_config):
        """Заявка с жалобой"""
        
        role_service = RoleService()
        role_service.config = mock_config
        request_service = RequestService()
        complaint_service = ComplaintService()
        
        employee = await role_service.get_or_create_user(test_session, 600001)
        
        # Создаем заявку
        request = await request_service.create_request(
            session=test_session,
            user_id=employee.id,
            category="Канцелярия",
            description="Заявка для жалобы",
            priority="urgent"
        )
        
        # Заявка не обрабатывается долго...
        
        # Сотрудник жалуется
        complaint = await complaint_service.create_complaint(
            session=test_session,
            user_id=employee.id,
            request_id=request.id,
            reason="Долгое выполнение",
            text="Жду уже неделю!"
        )
        
        # Проверяем что жалоба связана с заявкой
        complaints = await complaint_service.get_complaints_by_request(
            test_session,
            request.id
        )
        assert len(complaints) == 1
        
        # После жалобы заявка выполняется
        request.status = "completed"
        request.completed_at = datetime.now()
        await test_session.flush()
        
        # Финальная проверка
        result = await test_session.execute(
            select(Request).where(Request.id == request.id)
        )
        final = result.scalar_one()
        assert final.status == "completed"
    
    @pytest.mark.asyncio
    async def test_warehouse_low_stock_scenario(self, test_session, mock_config):
        """Сценарий низкого остатка на складе"""
        
        warehouse_service = WarehouseService()
        
        # Создаем товар
        item = await warehouse_service.create_item(
            test_session,
            name="Тестовый товар",
            min_quantity=50
        )
        
        # Добавляем небольшое количество
        await warehouse_service.add_quantity(test_session, item.id, 30)
        
        # Проверяем что товар в списке с низким остатком
        low_stock = await warehouse_service.get_low_stock_items(test_session)
        
        assert any(i.id == item.id for i in low_stock)
        
        # Пополняем склад
        await warehouse_service.add_quantity(test_session, item.id, 100)
        
        # Теперь не должен быть в списке
        low_stock = await warehouse_service.get_low_stock_items(test_session)
        
        assert not any(i.id == item.id for i in low_stock)
    
    @pytest.mark.asyncio
    async def test_daily_report_data(self, test_session, mock_config):
        """Данные для ежедневного отчета"""
        
        role_service = RoleService()
        role_service.config = mock_config
        request_service = RequestService()
        
        # Создаем данные за день
        employee = await role_service.get_or_create_user(test_session, 700001)
        
        # Несколько заявок разных статусов
        statuses = ["new", "in_progress", "completed", "rejected"]
        
        for i, status in enumerate(statuses):
            r = await request_service.create_request(
                session=test_session,
                user_id=employee.id,
                category="Канцелярия",
                description=f"Заявка {i}",
                priority="normal" if i % 2 == 0 else "urgent"
            )
            
            if status != "new":
                r.status = status
                if status == "completed":
                    r.completed_at = datetime.now()
                elif status == "rejected":
                    r.rejection_reason = "Тест"
        
        await test_session.flush()
        
        # Формируем данные для отчета
        result = await test_session.execute(
            select(Request.status, func.count(Request.id))
            .group_by(Request.status)
        )
        report = {status: count for status, count in result.all()}
        
        # Проверяем наличие данных
        assert len(report) >= 1

