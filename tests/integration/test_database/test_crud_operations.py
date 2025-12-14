"""
Тесты CRUD операций базы данных

Тестируемые операции:
- Create, Read, Update, Delete для всех моделей
"""
import pytest
from datetime import datetime
from sqlalchemy import select, update, delete

from bot.database.models import User, Request, RequestPhoto, WarehouseItem, Complaint


class TestUserCRUD:
    """CRUD операции для User"""
    
    @pytest.mark.asyncio
    async def test_create_user(self, test_session):
        """Создание пользователя"""
        user = User(id=12345, role="employee")
        test_session.add(user)
        await test_session.flush()
        
        result = await test_session.execute(
            select(User).where(User.id == 12345)
        )
        found = result.scalar_one_or_none()
        
        assert found is not None
        assert found.id == 12345
        assert found.role == "employee"
    
    @pytest.mark.asyncio
    async def test_read_user(self, test_session, test_user):
        """Чтение пользователя"""
        result = await test_session.execute(
            select(User).where(User.id == test_user.id)
        )
        found = result.scalar_one_or_none()
        
        assert found is not None
        assert found.id == test_user.id
    
    @pytest.mark.asyncio
    async def test_update_user(self, test_session, test_user):
        """Обновление пользователя"""
        test_user.role = "warehouseman"
        await test_session.flush()
        
        result = await test_session.execute(
            select(User).where(User.id == test_user.id)
        )
        updated = result.scalar_one()
        
        assert updated.role == "warehouseman"
    
    @pytest.mark.asyncio
    async def test_delete_user(self, test_session):
        """Удаление пользователя"""
        user = User(id=99999, role="employee")
        test_session.add(user)
        await test_session.flush()
        
        await test_session.execute(
            delete(User).where(User.id == 99999)
        )
        await test_session.flush()
        
        result = await test_session.execute(
            select(User).where(User.id == 99999)
        )
        deleted = result.scalar_one_or_none()
        
        assert deleted is None


class TestRequestCRUD:
    """CRUD операции для Request"""
    
    @pytest.mark.asyncio
    async def test_create_request(self, test_session, test_user):
        """Создание заявки"""
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
        
        result = await test_session.execute(
            select(Request).where(Request.number == "ЗХ-010125-001")
        )
        found = result.scalar_one_or_none()
        
        assert found is not None
        assert found.category == "Канцелярия"
    
    @pytest.mark.asyncio
    async def test_read_request(self, test_session, test_request):
        """Чтение заявки"""
        result = await test_session.execute(
            select(Request).where(Request.id == test_request.id)
        )
        found = result.scalar_one_or_none()
        
        assert found is not None
    
    @pytest.mark.asyncio
    async def test_update_request_status(self, test_session, test_request):
        """Обновление статуса заявки"""
        test_request.status = "in_progress"
        await test_session.flush()
        
        result = await test_session.execute(
            select(Request).where(Request.id == test_request.id)
        )
        updated = result.scalar_one()
        
        assert updated.status == "in_progress"
    
    @pytest.mark.asyncio
    async def test_delete_request(self, test_session, test_user):
        """Удаление заявки"""
        request = Request(
            number="ЗХ-DELETE-001",
            user_id=test_user.id,
            category="Тест",
            description="Для удаления",
            priority="normal",
            status="new"
        )
        test_session.add(request)
        await test_session.flush()
        
        request_id = request.id
        
        await test_session.execute(
            delete(Request).where(Request.id == request_id)
        )
        await test_session.flush()
        
        result = await test_session.execute(
            select(Request).where(Request.id == request_id)
        )
        deleted = result.scalar_one_or_none()
        
        assert deleted is None


class TestWarehouseItemCRUD:
    """CRUD операции для WarehouseItem"""
    
    @pytest.mark.asyncio
    async def test_create_warehouse_item(self, test_session):
        """Создание позиции склада"""
        item = WarehouseItem(
            name="Новый товар",
            current_quantity=100,
            min_quantity=10
        )
        test_session.add(item)
        await test_session.flush()
        
        result = await test_session.execute(
            select(WarehouseItem).where(WarehouseItem.name == "Новый товар")
        )
        found = result.scalar_one_or_none()
        
        assert found is not None
        assert found.current_quantity == 100
    
    @pytest.mark.asyncio
    async def test_update_warehouse_quantity(self, test_session, test_warehouse_item):
        """Обновление количества на складе"""
        test_warehouse_item.current_quantity = 200
        await test_session.flush()
        
        result = await test_session.execute(
            select(WarehouseItem).where(WarehouseItem.id == test_warehouse_item.id)
        )
        updated = result.scalar_one()
        
        assert updated.current_quantity == 200


class TestComplaintCRUD:
    """CRUD операции для Complaint"""
    
    @pytest.mark.asyncio
    async def test_create_complaint(self, test_session, test_user, test_request):
        """Создание жалобы"""
        complaint = Complaint(
            user_id=test_user.id,
            request_id=test_request.id,
            reason="Тест",
            text="Тестовая жалоба"
        )
        test_session.add(complaint)
        await test_session.flush()
        
        result = await test_session.execute(
            select(Complaint).where(Complaint.id == complaint.id)
        )
        found = result.scalar_one_or_none()
        
        assert found is not None
        assert found.reason == "Тест"
    
    @pytest.mark.asyncio
    async def test_read_complaint(self, test_session, test_complaint):
        """Чтение жалобы"""
        result = await test_session.execute(
            select(Complaint).where(Complaint.id == test_complaint.id)
        )
        found = result.scalar_one_or_none()
        
        assert found is not None


class TestRequestPhotoCRUD:
    """CRUD операции для RequestPhoto"""
    
    @pytest.mark.asyncio
    async def test_create_request_photo(self, test_session, test_request):
        """Создание фото заявки"""
        photo = RequestPhoto(
            request_id=test_request.id,
            file_id="test_file_id"
        )
        test_session.add(photo)
        await test_session.flush()
        
        result = await test_session.execute(
            select(RequestPhoto).where(RequestPhoto.file_id == "test_file_id")
        )
        found = result.scalar_one_or_none()
        
        assert found is not None
        assert found.request_id == test_request.id
    
    @pytest.mark.asyncio
    async def test_delete_photo_with_request(self, test_session, test_user):
        """Удаление фото при удалении заявки (cascade)"""
        # Создаем заявку с фото
        request = Request(
            number="ЗХ-PHOTO-001",
            user_id=test_user.id,
            category="Тест",
            description="С фото",
            priority="normal",
            status="new"
        )
        test_session.add(request)
        await test_session.flush()
        
        photo = RequestPhoto(
            request_id=request.id,
            file_id="cascade_test"
        )
        test_session.add(photo)
        await test_session.flush()
        
        photo_id = photo.id
        
        # Удаляем заявку
        await test_session.delete(request)
        await test_session.flush()
        
        # Проверяем что фото тоже удалено
        result = await test_session.execute(
            select(RequestPhoto).where(RequestPhoto.id == photo_id)
        )
        deleted_photo = result.scalar_one_or_none()
        
        assert deleted_photo is None

