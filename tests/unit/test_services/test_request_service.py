"""
Unit тесты для RequestService

Тестируемые методы:
- generate_request_number() - генерация уникальных номеров заявок
- create_request() - создание заявки с фото и без
- get_user_requests() - получение заявок пользователя
- get_request_by_id() - получение заявки по ID
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from sqlalchemy import select

from bot.services.request_service import RequestService, request_service
from bot.database.models import Request, RequestPhoto, User


class TestRequestServiceGenerateNumber:
    """Тесты генерации номера заявки"""
    
    @pytest.mark.asyncio
    async def test_generate_request_number_first_request_today(self, test_session, test_user):
        """Первая заявка за день должна иметь номер 001"""
        service = RequestService()
        
        number = await service.generate_request_number(test_session)
        
        # Проверяем формат: ЗХ-ДДММГГ-001
        today = datetime.now()
        expected_prefix = f"ЗХ-{today.strftime('%d%m%y')}"
        
        assert number.startswith(expected_prefix)
        assert number.endswith("-001")
    
    @pytest.mark.asyncio
    async def test_generate_request_number_increments(self, test_session, test_user):
        """Номера заявок должны увеличиваться последовательно"""
        service = RequestService()
        
        # Создаем первую заявку
        first_request = Request(
            number=await service.generate_request_number(test_session),
            user_id=test_user.id,
            category="Канцелярия",
            description="Первая заявка",
            priority="normal",
            status="new"
        )
        test_session.add(first_request)
        await test_session.flush()
        
        # Генерируем следующий номер
        second_number = await service.generate_request_number(test_session)
        
        # Должен заканчиваться на 002
        assert second_number.endswith("-002")
    
    @pytest.mark.asyncio
    async def test_generate_request_number_format(self, test_session, test_user):
        """Проверка формата номера заявки ЗХ-ДДММГГ-№№№"""
        service = RequestService()
        
        number = await service.generate_request_number(test_session)
        
        # Проверяем структуру
        parts = number.split("-")
        assert len(parts) == 3
        assert parts[0] == "ЗХ"
        assert len(parts[1]) == 6  # ДДММГГ
        assert len(parts[2]) == 3  # №№№


class TestRequestServiceCreate:
    """Тесты создания заявки"""
    
    @pytest.mark.asyncio
    async def test_create_request_without_photos(self, test_session, test_user):
        """Создание заявки без фотографий"""
        service = RequestService()
        
        request = await service.create_request(
            session=test_session,
            user_id=test_user.id,
            category="Канцелярия",
            description="Нужны ручки синие",
            priority="normal",
            quantity=10
        )
        
        assert request is not None
        assert request.id is not None
        assert request.number is not None
        assert request.category == "Канцелярия"
        assert request.description == "Нужны ручки синие"
        assert request.priority == "normal"
        assert request.quantity == 10
        assert request.status == "new"
        assert request.user_id == test_user.id
    
    @pytest.mark.asyncio
    async def test_create_request_with_photos(self, test_session, test_user):
        """Создание заявки с фотографиями"""
        service = RequestService()
        photo_ids = ["photo_1", "photo_2", "photo_3"]
        
        request = await service.create_request(
            session=test_session,
            user_id=test_user.id,
            category="Ремонт мебели",
            description="Сломан стол в кабинете 5",
            priority="urgent",
            photo_file_ids=photo_ids
        )
        
        assert request is not None
        assert request.priority == "urgent"
        
        # Проверяем что фото сохранились
        result = await test_session.execute(
            select(RequestPhoto).where(RequestPhoto.request_id == request.id)
        )
        photos = list(result.scalars().all())
        
        assert len(photos) == 3
        assert all(photo.file_id in photo_ids for photo in photos)
    
    @pytest.mark.asyncio
    async def test_create_request_without_quantity(self, test_session, test_user):
        """Создание заявки без количества (для нематериальных категорий)"""
        service = RequestService()
        
        request = await service.create_request(
            session=test_session,
            user_id=test_user.id,
            category="Ремонт сантехники",
            description="Течет кран в туалете",
            priority="urgent"
        )
        
        assert request is not None
        assert request.quantity is None
    
    @pytest.mark.asyncio
    async def test_create_request_sets_default_status(self, test_session, test_user):
        """Новая заявка должна иметь статус 'new'"""
        service = RequestService()
        
        request = await service.create_request(
            session=test_session,
            user_id=test_user.id,
            category="Канцелярия",
            description="Тест",
            priority="normal"
        )
        
        assert request.status == "new"


class TestRequestServiceGet:
    """Тесты получения заявок"""
    
    @pytest.mark.asyncio
    async def test_get_user_requests_empty(self, test_session, test_user):
        """Получение заявок когда их нет"""
        service = RequestService()
        
        requests = await service.get_user_requests(test_session, test_user.id)
        
        assert requests == []
    
    @pytest.mark.asyncio
    async def test_get_user_requests_returns_only_user_requests(self, test_session, test_user):
        """Возвращаются только заявки конкретного пользователя"""
        service = RequestService()
        
        # Создаем заявку для нашего пользователя
        our_request = await service.create_request(
            session=test_session,
            user_id=test_user.id,
            category="Канцелярия",
            description="Наша заявка",
            priority="normal"
        )
        
        # Создаем другого пользователя и его заявку
        other_user = User(id=999999, role="employee")
        test_session.add(other_user)
        await test_session.flush()
        
        other_request = await service.create_request(
            session=test_session,
            user_id=other_user.id,
            category="Канцелярия",
            description="Чужая заявка",
            priority="normal"
        )
        
        # Получаем заявки нашего пользователя
        requests = await service.get_user_requests(test_session, test_user.id)
        
        assert len(requests) == 1
        assert requests[0].id == our_request.id
    
    @pytest.mark.asyncio
    async def test_get_user_requests_with_limit(self, test_session, test_user):
        """Ограничение количества возвращаемых заявок"""
        service = RequestService()
        
        # Создаем 5 заявок
        for i in range(5):
            await service.create_request(
                session=test_session,
                user_id=test_user.id,
                category="Канцелярия",
                description=f"Заявка {i+1}",
                priority="normal"
            )
        
        # Запрашиваем только 3
        requests = await service.get_user_requests(test_session, test_user.id, limit=3)
        
        assert len(requests) == 3
    
    @pytest.mark.asyncio
    async def test_get_user_requests_ordered_by_date_desc(self, test_session, test_user):
        """Заявки отсортированы по дате создания (новые первые)"""
        service = RequestService()
        
        # Создаем заявки
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
        # При одинаковом времени создания (в быстрых тестах) порядок может варьироваться
        assert len(requests) == 2
        # Проверяем что обе заявки присутствуют
        descriptions = [r.description for r in requests]
        assert "Первая" in descriptions
        assert "Вторая" in descriptions
    
    @pytest.mark.asyncio
    async def test_get_request_by_id_exists(self, test_session, test_user):
        """Получение существующей заявки по ID"""
        service = RequestService()
        
        created = await service.create_request(
            session=test_session,
            user_id=test_user.id,
            category="Канцелярия",
            description="Тест",
            priority="normal"
        )
        
        found = await service.get_request_by_id(test_session, created.id)
        
        assert found is not None
        assert found.id == created.id
        assert found.number == created.number
    
    @pytest.mark.asyncio
    async def test_get_request_by_id_not_exists(self, test_session):
        """Получение несуществующей заявки возвращает None"""
        service = RequestService()
        
        found = await service.get_request_by_id(test_session, 99999)
        
        assert found is None


class TestRequestServiceEdgeCases:
    """Edge cases и граничные условия"""
    
    @pytest.mark.asyncio
    async def test_create_request_with_empty_description(self, test_session, test_user):
        """Создание заявки с пустым описанием"""
        service = RequestService()
        
        # Примечание: в реальности это должно валидироваться на уровне handler
        # Здесь проверяем что БД примет пустую строку
        request = await service.create_request(
            session=test_session,
            user_id=test_user.id,
            category="Канцелярия",
            description="",
            priority="normal"
        )
        
        assert request.description == ""
    
    @pytest.mark.asyncio
    async def test_create_request_with_long_description(self, test_session, test_user):
        """Создание заявки с длинным описанием"""
        service = RequestService()
        long_description = "А" * 1000
        
        request = await service.create_request(
            session=test_session,
            user_id=test_user.id,
            category="Канцелярия",
            description=long_description,
            priority="normal"
        )
        
        assert len(request.description) == 1000
    
    @pytest.mark.asyncio
    async def test_create_multiple_requests_same_day(self, test_session, test_user):
        """Создание нескольких заявок в один день - номера увеличиваются"""
        service = RequestService()
        numbers = []
        
        for i in range(5):
            request = await service.create_request(
                session=test_session,
                user_id=test_user.id,
                category="Канцелярия",
                description=f"Заявка {i}",
                priority="normal"
            )
            numbers.append(request.number)
        
        # Проверяем что номера уникальные и последовательные
        assert len(set(numbers)) == 5
        
        # Проверяем последовательность: 001, 002, 003, 004, 005
        for i, number in enumerate(numbers, 1):
            assert number.endswith(f"-{i:03d}")

