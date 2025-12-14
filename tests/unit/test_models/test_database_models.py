"""
Unit тесты для моделей базы данных

Тестируемые модели:
- User
- Request
- RequestPhoto
- WarehouseItem
- Complaint
"""
import pytest
from datetime import datetime
from sqlalchemy import select

from bot.database.models import User, Request, RequestPhoto, WarehouseItem, Complaint


class TestUserModel:
    """Тесты модели User"""
    
    @pytest.mark.asyncio
    async def test_create_user(self, test_session):
        """Создание пользователя"""
        user = User(id=12345, role="employee")
        test_session.add(user)
        await test_session.flush()
        
        assert user.id == 12345
        assert user.role == "employee"
        assert user.created_at is not None
    
    @pytest.mark.asyncio
    async def test_user_roles(self, test_session):
        """Разные роли пользователей"""
        roles = ["employee", "warehouseman", "manager"]
        
        for i, role in enumerate(roles, 1):
            user = User(id=i, role=role)
            test_session.add(user)
        
        await test_session.flush()
        
        result = await test_session.execute(select(User))
        users = list(result.scalars().all())
        
        assert len(users) == 3
        user_roles = {u.role for u in users}
        assert user_roles == set(roles)


class TestRequestModel:
    """Тесты модели Request"""
    
    @pytest.mark.asyncio
    async def test_create_request(self, test_session, test_user):
        """Создание заявки"""
        request = Request(
            number="ЗХ-010125-001",
            user_id=test_user.id,
            category="Канцелярия",
            description="Нужны ручки",
            quantity=10,
            priority="normal",
            status="new"
        )
        test_session.add(request)
        await test_session.flush()
        
        assert request.id is not None
        assert request.number == "ЗХ-010125-001"
        assert request.status == "new"
        assert request.created_at is not None
    
    @pytest.mark.asyncio
    async def test_request_statuses(self, test_session, test_user):
        """Разные статусы заявок"""
        statuses = ["new", "in_progress", "completed", "rejected"]
        
        for i, status in enumerate(statuses, 1):
            request = Request(
                number=f"ЗХ-010125-{i:03d}",
                user_id=test_user.id,
                category="Канцелярия",
                description="Тест",
                priority="normal",
                status=status
            )
            test_session.add(request)
        
        await test_session.flush()
        
        result = await test_session.execute(select(Request))
        requests = list(result.scalars().all())
        
        assert len(requests) == 4
    
    @pytest.mark.asyncio
    async def test_request_priorities(self, test_session, test_user):
        """Приоритеты заявок"""
        priorities = ["normal", "urgent"]
        
        for i, priority in enumerate(priorities, 1):
            request = Request(
                number=f"ЗХ-010125-{i:03d}",
                user_id=test_user.id,
                category="Канцелярия",
                description="Тест",
                priority=priority,
                status="new"
            )
            test_session.add(request)
        
        await test_session.flush()
        
        result = await test_session.execute(select(Request))
        requests = list(result.scalars().all())
        
        assert len(requests) == 2
    
    @pytest.mark.asyncio
    async def test_request_with_rejection_reason(self, test_session, test_user):
        """Заявка с причиной отклонения"""
        request = Request(
            number="ЗХ-010125-001",
            user_id=test_user.id,
            category="Канцелярия",
            description="Тест",
            priority="normal",
            status="rejected",
            rejection_reason="Нет в наличии"
        )
        test_session.add(request)
        await test_session.flush()
        
        assert request.rejection_reason == "Нет в наличии"


class TestRequestPhotoModel:
    """Тесты модели RequestPhoto"""
    
    @pytest.mark.asyncio
    async def test_create_request_photo(self, test_session, test_request):
        """Создание фото заявки"""
        photo = RequestPhoto(
            request_id=test_request.id,
            file_id="test_file_id_123"
        )
        test_session.add(photo)
        await test_session.flush()
        
        assert photo.id is not None
        assert photo.request_id == test_request.id
        assert photo.file_id == "test_file_id_123"
        assert photo.created_at is not None
    
    @pytest.mark.asyncio
    async def test_multiple_photos_per_request(self, test_session, test_request):
        """Несколько фото на одну заявку"""
        for i in range(5):
            photo = RequestPhoto(
                request_id=test_request.id,
                file_id=f"file_id_{i}"
            )
            test_session.add(photo)
        
        await test_session.flush()
        
        result = await test_session.execute(
            select(RequestPhoto).where(RequestPhoto.request_id == test_request.id)
        )
        photos = list(result.scalars().all())
        
        assert len(photos) == 5


class TestWarehouseItemModel:
    """Тесты модели WarehouseItem"""
    
    @pytest.mark.asyncio
    async def test_create_warehouse_item(self, test_session):
        """Создание позиции на складе"""
        item = WarehouseItem(
            name="Бумага А4",
            current_quantity=100,
            min_quantity=20
        )
        test_session.add(item)
        await test_session.flush()
        
        assert item.id is not None
        assert item.name == "Бумага А4"
        assert item.current_quantity == 100
        assert item.min_quantity == 20
    
    @pytest.mark.asyncio
    async def test_warehouse_item_default_quantities(self, test_session):
        """Значения по умолчанию для количеств"""
        item = WarehouseItem(name="Новый товар")
        test_session.add(item)
        await test_session.flush()
        
        # По умолчанию current_quantity=0, min_quantity=0
        assert item.current_quantity == 0
        assert item.min_quantity == 0
    
    @pytest.mark.asyncio
    async def test_warehouse_item_unique_name(self, test_session):
        """Уникальность названия"""
        item1 = WarehouseItem(name="Уникальный товар", current_quantity=10)
        test_session.add(item1)
        await test_session.flush()
        
        # Попытка создать товар с таким же именем должна вызвать ошибку
        item2 = WarehouseItem(name="Уникальный товар", current_quantity=20)
        test_session.add(item2)
        
        with pytest.raises(Exception):  # IntegrityError
            await test_session.flush()


class TestComplaintModel:
    """Тесты модели Complaint"""
    
    @pytest.mark.asyncio
    async def test_create_complaint(self, test_session, test_user, test_request):
        """Создание жалобы"""
        complaint = Complaint(
            user_id=test_user.id,
            request_id=test_request.id,
            reason="Долгое выполнение",
            text="Жду уже неделю"
        )
        test_session.add(complaint)
        await test_session.flush()
        
        assert complaint.id is not None
        assert complaint.user_id == test_user.id
        assert complaint.request_id == test_request.id
        assert complaint.reason == "Долгое выполнение"
        assert complaint.created_at is not None
    
    @pytest.mark.asyncio
    async def test_complaint_with_long_text(self, test_session, test_user, test_request):
        """Жалоба с длинным текстом"""
        long_text = "А" * 2000
        
        complaint = Complaint(
            user_id=test_user.id,
            request_id=test_request.id,
            reason="Другое",
            text=long_text
        )
        test_session.add(complaint)
        await test_session.flush()
        
        assert len(complaint.text) == 2000


class TestModelRelationships:
    """Тесты связей между моделями"""
    
    @pytest.mark.asyncio
    async def test_user_has_requests(self, test_session, test_user):
        """User имеет связь с Request"""
        # Создаем заявки для пользователя
        for i in range(3):
            request = Request(
                number=f"ЗХ-010125-{i:03d}",
                user_id=test_user.id,
                category="Канцелярия",
                description=f"Заявка {i}",
                priority="normal",
                status="new"
            )
            test_session.add(request)
        
        await test_session.flush()
        
        # Проверяем связь через select
        result = await test_session.execute(
            select(Request).where(Request.user_id == test_user.id)
        )
        requests = list(result.scalars().all())
        
        assert len(requests) == 3
    
    @pytest.mark.asyncio
    async def test_request_has_photos(self, test_session, test_user):
        """Request имеет связь с RequestPhoto"""
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
        
        # Добавляем фото
        for i in range(2):
            photo = RequestPhoto(
                request_id=request.id,
                file_id=f"file_{i}"
            )
            test_session.add(photo)
        
        await test_session.flush()
        
        # Проверяем связь
        result = await test_session.execute(
            select(RequestPhoto).where(RequestPhoto.request_id == request.id)
        )
        photos = list(result.scalars().all())
        
        assert len(photos) == 2

