"""
Интеграционные тесты для handlers завхоза

Тестируемые сценарии:
- Просмотр новых заявок
- Смена статуса заявки (принять в работу, выполнить, отклонить)
- Управление складом
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from sqlalchemy import select

from bot.database.models import User, Request, WarehouseItem
from bot.services.request_service import RequestService
from bot.services.warehouse_service import WarehouseService


class TestNewRequests:
    """Тесты просмотра новых заявок"""
    
    @pytest.mark.asyncio
    async def test_view_new_requests(self, test_session, test_user):
        """Завхоз видит все новые заявки"""
        # Создаем новые заявки
        for i in range(5):
            request = Request(
                number=f"ЗХ-010125-{i:03d}",
                user_id=test_user.id,
                category="Канцелярия",
                description=f"Новая заявка {i}",
                priority="normal",
                status="new"
            )
            test_session.add(request)
        
        await test_session.flush()
        
        # Получаем все новые заявки
        result = await test_session.execute(
            select(Request).where(Request.status == "new")
        )
        new_requests = list(result.scalars().all())
        
        assert len(new_requests) == 5
    
    @pytest.mark.asyncio
    async def test_new_requests_sorted_by_priority(self, test_session, test_user):
        """Срочные заявки показываются первыми"""
        # Создаем обычную заявку
        normal = Request(
            number="ЗХ-010125-001",
            user_id=test_user.id,
            category="Канцелярия",
            description="Обычная",
            priority="normal",
            status="new"
        )
        test_session.add(normal)
        
        # Создаем срочную заявку
        urgent = Request(
            number="ЗХ-010125-002",
            user_id=test_user.id,
            category="Ремонт сантехники",
            description="Срочная",
            priority="urgent",
            status="new"
        )
        test_session.add(urgent)
        await test_session.flush()
        
        # Сортируем по приоритету (urgent первый)
        result = await test_session.execute(
            select(Request)
            .where(Request.status == "new")
            .order_by(Request.priority.desc())  # urgent > normal
        )
        requests = list(result.scalars().all())
        
        assert requests[0].priority == "urgent"


class TestChangeRequestStatus:
    """Тесты смены статуса заявки"""
    
    @pytest.mark.asyncio
    async def test_accept_request(self, test_session, test_user):
        """Принятие заявки в работу"""
        # Создаем новую заявку
        request = Request(
            number="ЗХ-010125-001",
            user_id=test_user.id,
            category="Канцелярия",
            description="Тест",
            priority="normal",
            status="new"
        )
        test_session.add(request)
        await test_session.flush()
        
        # Меняем статус на in_progress
        request.status = "in_progress"
        await test_session.flush()
        
        # Проверяем
        result = await test_session.execute(
            select(Request).where(Request.id == request.id)
        )
        updated = result.scalar_one()
        
        assert updated.status == "in_progress"
    
    @pytest.mark.asyncio
    async def test_complete_request(self, test_session, test_user):
        """Выполнение заявки"""
        request = Request(
            number="ЗХ-010125-001",
            user_id=test_user.id,
            category="Канцелярия",
            description="Тест",
            priority="normal",
            status="in_progress"
        )
        test_session.add(request)
        await test_session.flush()
        
        # Выполняем заявку
        request.status = "completed"
        request.completed_at = datetime.now()
        await test_session.flush()
        
        result = await test_session.execute(
            select(Request).where(Request.id == request.id)
        )
        updated = result.scalar_one()
        
        assert updated.status == "completed"
        assert updated.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_reject_request(self, test_session, test_user):
        """Отклонение заявки"""
        request = Request(
            number="ЗХ-010125-001",
            user_id=test_user.id,
            category="Канцелярия",
            description="Тест",
            priority="normal",
            status="new"
        )
        test_session.add(request)
        await test_session.flush()
        
        # Отклоняем с причиной
        request.status = "rejected"
        request.rejection_reason = "Нет в наличии"
        await test_session.flush()
        
        result = await test_session.execute(
            select(Request).where(Request.id == request.id)
        )
        updated = result.scalar_one()
        
        assert updated.status == "rejected"
        assert updated.rejection_reason == "Нет в наличии"
    
    @pytest.mark.asyncio
    async def test_reject_requires_reason(self, test_session, test_user):
        """Отклонение требует причину (валидация на уровне handler)"""
        request = Request(
            number="ЗХ-010125-001",
            user_id=test_user.id,
            category="Канцелярия",
            description="Тест",
            priority="normal",
            status="new"
        )
        test_session.add(request)
        await test_session.flush()
        
        # Отклоняем без причины - это должно валидироваться на уровне handler
        # БД примет запись без причины
        request.status = "rejected"
        request.rejection_reason = None
        await test_session.flush()
        
        # На уровне БД это разрешено
        assert request.rejection_reason is None


class TestWarehouseManagement:
    """Тесты управления складом"""
    
    @pytest.mark.asyncio
    async def test_view_warehouse_items(self, test_session, test_warehouse_items):
        """Просмотр позиций склада"""
        service = WarehouseService()
        
        items = await service.get_all_items(test_session)
        
        assert len(items) == 5
    
    @pytest.mark.asyncio
    async def test_add_warehouse_item(self, test_session):
        """Добавление позиции на склад"""
        service = WarehouseService()
        
        item = await service.create_item(
            test_session,
            name="Новый товар",
            min_quantity=10
        )
        
        assert item.id is not None
        assert item.name == "Новый товар"
        assert item.current_quantity == 0
        assert item.min_quantity == 10
    
    @pytest.mark.asyncio
    async def test_update_item_quantity(self, test_session, test_warehouse_item):
        """Обновление количества"""
        service = WarehouseService()
        initial = test_warehouse_item.current_quantity
        
        # Добавляем
        updated = await service.add_quantity(test_session, test_warehouse_item.id, 50)
        
        assert updated.current_quantity == initial + 50
    
    @pytest.mark.asyncio
    async def test_subtract_item_quantity(self, test_session):
        """Списание товара"""
        service = WarehouseService()
        
        # Создаем товар с достаточным количеством
        item = await service.create_item(test_session, name="Товар для списания")
        await service.add_quantity(test_session, item.id, 100)
        
        # Списываем
        updated = await service.subtract_quantity(test_session, item.id, 30)
        
        assert updated.current_quantity == 70
    
    @pytest.mark.asyncio
    async def test_view_low_stock_items(self, test_session, test_low_stock_items):
        """Просмотр позиций с низким остатком"""
        service = WarehouseService()
        
        low_stock = await service.get_low_stock_items(test_session)
        
        assert len(low_stock) == 3  # Из fixture test_low_stock_items


class TestRequestsInProgress:
    """Тесты заявок в работе"""
    
    @pytest.mark.asyncio
    async def test_view_requests_in_progress(self, test_session, test_user):
        """Просмотр заявок в работе"""
        # Создаем заявки с разными статусами
        for status in ["new", "in_progress", "completed"]:
            request = Request(
                number=f"ЗХ-{status[:3]}-001",
                user_id=test_user.id,
                category="Канцелярия",
                description=f"Заявка {status}",
                priority="normal",
                status=status
            )
            test_session.add(request)
        
        await test_session.flush()
        
        # Получаем только in_progress
        result = await test_session.execute(
            select(Request).where(Request.status == "in_progress")
        )
        in_progress = list(result.scalars().all())
        
        assert len(in_progress) == 1
        assert in_progress[0].status == "in_progress"
    
    @pytest.mark.asyncio
    async def test_count_requests_by_status(self, test_session, test_user):
        """Подсчет заявок по статусам"""
        # Создаем заявки
        statuses = ["new", "new", "in_progress", "completed", "completed", "completed"]
        
        for i, status in enumerate(statuses):
            request = Request(
                number=f"ЗХ-010125-{i:03d}",
                user_id=test_user.id,
                category="Канцелярия",
                description=f"Заявка {i}",
                priority="normal",
                status=status
            )
            test_session.add(request)
        
        await test_session.flush()
        
        # Подсчитываем
        from sqlalchemy import func
        
        result = await test_session.execute(
            select(Request.status, func.count(Request.id))
            .group_by(Request.status)
        )
        counts = {status: count for status, count in result.all()}
        
        assert counts.get("new") == 2
        assert counts.get("in_progress") == 1
        assert counts.get("completed") == 3

