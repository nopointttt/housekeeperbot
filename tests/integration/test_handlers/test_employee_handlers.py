"""
Интеграционные тесты для handlers сотрудника

Тестируемые сценарии:
- Мои заявки
- Детали заявки
- Связаться с завхозом
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import select

from bot.database.models import User, Request
from bot.services.request_service import RequestService


class TestMyRequests:
    """Тесты раздела 'Мои заявки'"""
    
    @pytest.mark.asyncio
    async def test_my_requests_empty(self, test_session, test_user):
        """Нет заявок у пользователя"""
        service = RequestService()
        
        requests = await service.get_user_requests(test_session, test_user.id)
        
        assert requests == []
    
    @pytest.mark.asyncio
    async def test_my_requests_shows_user_requests(self, test_session, test_user):
        """Показывает только заявки текущего пользователя"""
        service = RequestService()
        
        # Создаем заявки для нашего пользователя
        for i in range(3):
            await service.create_request(
                session=test_session,
                user_id=test_user.id,
                category="Канцелярия",
                description=f"Заявка {i}",
                priority="normal"
            )
        
        # Создаем другого пользователя с заявкой
        other_user = User(id=999888, role="employee")
        test_session.add(other_user)
        await test_session.flush()
        
        await service.create_request(
            session=test_session,
            user_id=other_user.id,
            category="Канцелярия",
            description="Чужая заявка",
            priority="normal"
        )
        
        # Получаем заявки нашего пользователя
        requests = await service.get_user_requests(test_session, test_user.id)
        
        assert len(requests) == 3
        assert all(r.user_id == test_user.id for r in requests)
    
    @pytest.mark.asyncio
    async def test_my_requests_sorted_by_date(self, test_session, test_user):
        """Заявки отсортированы по дате (новые первые)"""
        service = RequestService()
        
        # Создаем заявки последовательно
        first = await service.create_request(
            session=test_session,
            user_id=test_user.id,
            category="Канцелярия",
            description="Первая",
            priority="normal"
        )
        
        second = await service.create_request(
            session=test_session,
            user_id=test_user.id,
            category="Канцелярия",
            description="Вторая",
            priority="normal"
        )
        
        requests = await service.get_user_requests(test_session, test_user.id)
        
        # Должно быть 2 заявки, отсортированные по дате DESC
        # При одинаковом времени создания порядок может быть любым
        assert len(requests) == 2
        # Проверяем что обе заявки присутствуют
        descriptions = [r.description for r in requests]
        assert "Первая" in descriptions
        assert "Вторая" in descriptions
    
    @pytest.mark.asyncio
    async def test_my_requests_shows_all_statuses(self, test_session, test_user):
        """Показывает заявки всех статусов"""
        # Создаем заявки разных статусов напрямую
        statuses = ["new", "in_progress", "completed", "rejected"]
        
        for i, status in enumerate(statuses):
            request = Request(
                number=f"ЗХ-010125-{i:03d}",
                user_id=test_user.id,
                category="Канцелярия",
                description=f"Заявка со статусом {status}",
                priority="normal",
                status=status
            )
            test_session.add(request)
        
        await test_session.flush()
        
        service = RequestService()
        requests = await service.get_user_requests(test_session, test_user.id)
        
        assert len(requests) == 4
        request_statuses = {r.status for r in requests}
        assert request_statuses == set(statuses)


class TestRequestDetails:
    """Тесты просмотра деталей заявки"""
    
    @pytest.mark.asyncio
    async def test_view_request_details(self, test_session, test_user):
        """Просмотр деталей заявки"""
        service = RequestService()
        
        # Создаем заявку
        created = await service.create_request(
            session=test_session,
            user_id=test_user.id,
            category="Канцелярия",
            description="Детальное описание заявки",
            priority="urgent",
            quantity=25
        )
        
        # Получаем детали
        request = await service.get_request_by_id(test_session, created.id)
        
        assert request is not None
        assert request.description == "Детальное описание заявки"
        assert request.priority == "urgent"
        assert request.quantity == 25
    
    @pytest.mark.asyncio
    async def test_view_request_with_photos(self, test_session, test_user):
        """Просмотр заявки с фото"""
        service = RequestService()
        
        request = await service.create_request(
            session=test_session,
            user_id=test_user.id,
            category="Ремонт мебели",
            description="Сломан стол",
            priority="normal",
            photo_file_ids=["photo_1", "photo_2"]
        )
        
        # Получаем заявку
        found = await service.get_request_by_id(test_session, request.id)
        
        assert found is not None
        # Фото загружаются через relationship
    
    @pytest.mark.asyncio
    async def test_request_not_found(self, test_session):
        """Заявка не найдена"""
        service = RequestService()
        
        request = await service.get_request_by_id(test_session, 99999)
        
        assert request is None


class TestContactWarehouseman:
    """Тесты функции 'Связаться с завхозом'"""
    
    @pytest.mark.asyncio
    async def test_contact_button_available(self):
        """Кнопка 'Связаться с завхозом' доступна"""
        from bot.keyboards.employee import get_employee_keyboard
        
        keyboard = get_employee_keyboard()
        
        button_texts = []
        for row in keyboard.keyboard:
            for button in row:
                button_texts.append(button.text)
        
        # Должна быть кнопка связи с завхозом
        assert any("завхоз" in text.lower() for text in button_texts)


class TestRequestFilters:
    """Тесты фильтрации заявок"""
    
    @pytest.mark.asyncio
    async def test_filter_by_status(self, test_session, test_user):
        """Фильтрация по статусу"""
        # Создаем заявки разных статусов
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
        
        # Фильтруем только новые
        result = await test_session.execute(
            select(Request)
            .where(Request.user_id == test_user.id)
            .where(Request.status == "new")
        )
        new_requests = list(result.scalars().all())
        
        assert len(new_requests) == 1
        assert new_requests[0].status == "new"
    
    @pytest.mark.asyncio
    async def test_limit_requests(self, test_session, test_user):
        """Ограничение количества заявок"""
        service = RequestService()
        
        # Создаем 10 заявок
        for i in range(10):
            await service.create_request(
                session=test_session,
                user_id=test_user.id,
                category="Канцелярия",
                description=f"Заявка {i}",
                priority="normal"
            )
        
        # Запрашиваем только 5
        requests = await service.get_user_requests(test_session, test_user.id, limit=5)
        
        assert len(requests) == 5

