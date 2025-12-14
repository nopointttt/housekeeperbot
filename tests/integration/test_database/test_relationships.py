"""
Тесты связей между моделями базы данных

Тестируемые связи:
- User -> Request (one-to-many)
- Request -> RequestPhoto (one-to-many)
- User -> Complaint (one-to-many)
- Request -> Complaint (one-to-many через request_id)
"""
import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.database.models import User, Request, RequestPhoto, Complaint


class TestUserRequestRelationship:
    """Тесты связи User -> Request"""
    
    @pytest.mark.asyncio
    async def test_user_has_many_requests(self, test_session, test_user):
        """Пользователь может иметь много заявок"""
        # Создаем несколько заявок
        for i in range(5):
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
        
        # Получаем заявки пользователя
        result = await test_session.execute(
            select(Request).where(Request.user_id == test_user.id)
        )
        requests = list(result.scalars().all())
        
        assert len(requests) == 5
    
    @pytest.mark.asyncio
    async def test_request_belongs_to_user(self, test_session, test_user):
        """Заявка принадлежит пользователю"""
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
        
        # Получаем заявку с пользователем
        result = await test_session.execute(
            select(Request)
            .where(Request.id == request.id)
            .options(selectinload(Request.user))
        )
        loaded = result.scalar_one()
        
        assert loaded.user_id == test_user.id


class TestRequestPhotoRelationship:
    """Тесты связи Request -> RequestPhoto"""
    
    @pytest.mark.asyncio
    async def test_request_has_many_photos(self, test_session, test_user):
        """Заявка может иметь много фото"""
        request = Request(
            number="ЗХ-010125-001",
            user_id=test_user.id,
            category="Ремонт",
            description="С фото",
            priority="normal",
            status="new"
        )
        test_session.add(request)
        await test_session.flush()
        
        # Добавляем фото
        for i in range(3):
            photo = RequestPhoto(
                request_id=request.id,
                file_id=f"photo_{i}"
            )
            test_session.add(photo)
        await test_session.flush()
        
        # Получаем фото заявки
        result = await test_session.execute(
            select(RequestPhoto).where(RequestPhoto.request_id == request.id)
        )
        photos = list(result.scalars().all())
        
        assert len(photos) == 3
    
    @pytest.mark.asyncio
    async def test_photo_belongs_to_request(self, test_session, test_request):
        """Фото принадлежит заявке"""
        photo = RequestPhoto(
            request_id=test_request.id,
            file_id="test_photo"
        )
        test_session.add(photo)
        await test_session.flush()
        
        # Получаем фото с заявкой
        result = await test_session.execute(
            select(RequestPhoto)
            .where(RequestPhoto.id == photo.id)
            .options(selectinload(RequestPhoto.request))
        )
        loaded = result.scalar_one()
        
        assert loaded.request_id == test_request.id
    
    @pytest.mark.asyncio
    async def test_cascade_delete_photos(self, test_session, test_user):
        """Фото удаляются вместе с заявкой"""
        request = Request(
            number="ЗХ-CASCADE-001",
            user_id=test_user.id,
            category="Тест",
            description="Тест каскада",
            priority="normal",
            status="new"
        )
        test_session.add(request)
        await test_session.flush()
        
        photo = RequestPhoto(
            request_id=request.id,
            file_id="cascade_photo"
        )
        test_session.add(photo)
        await test_session.flush()
        
        photo_id = photo.id
        
        # Удаляем заявку
        await test_session.delete(request)
        await test_session.flush()
        
        # Проверяем что фото удалено
        result = await test_session.execute(
            select(RequestPhoto).where(RequestPhoto.id == photo_id)
        )
        deleted = result.scalar_one_or_none()
        
        assert deleted is None


class TestUserComplaintRelationship:
    """Тесты связи User -> Complaint"""
    
    @pytest.mark.asyncio
    async def test_user_has_many_complaints(self, test_session, test_user, test_request):
        """Пользователь может иметь много жалоб"""
        for i in range(3):
            complaint = Complaint(
                user_id=test_user.id,
                request_id=test_request.id,
                reason=f"Причина {i}",
                text=f"Жалоба {i}"
            )
            test_session.add(complaint)
        await test_session.flush()
        
        result = await test_session.execute(
            select(Complaint).where(Complaint.user_id == test_user.id)
        )
        complaints = list(result.scalars().all())
        
        assert len(complaints) == 3
    
    @pytest.mark.asyncio
    async def test_complaint_belongs_to_user(self, test_session, test_user, test_request):
        """Жалоба принадлежит пользователю"""
        complaint = Complaint(
            user_id=test_user.id,
            request_id=test_request.id,
            reason="Тест",
            text="Тестовая жалоба"
        )
        test_session.add(complaint)
        await test_session.flush()
        
        result = await test_session.execute(
            select(Complaint)
            .where(Complaint.id == complaint.id)
            .options(selectinload(Complaint.user))
        )
        loaded = result.scalar_one()
        
        assert loaded.user_id == test_user.id


class TestComplexRelationships:
    """Тесты сложных связей"""
    
    @pytest.mark.asyncio
    async def test_user_with_requests_and_photos(self, test_session, test_user):
        """Пользователь с заявками и фото"""
        # Создаем заявку
        request = Request(
            number="ЗХ-010125-001",
            user_id=test_user.id,
            category="Тест",
            description="Заявка с фото",
            priority="normal",
            status="new"
        )
        test_session.add(request)
        await test_session.flush()
        
        # Добавляем фото
        for i in range(2):
            photo = RequestPhoto(
                request_id=request.id,
                file_id=f"photo_{i}"
            )
            test_session.add(photo)
        await test_session.flush()
        
        # Получаем все
        result = await test_session.execute(
            select(Request)
            .where(Request.user_id == test_user.id)
            .options(selectinload(Request.photos))
        )
        loaded = result.scalar_one()
        
        # Проверяем что фото загружены
        photos_result = await test_session.execute(
            select(RequestPhoto).where(RequestPhoto.request_id == loaded.id)
        )
        photos = list(photos_result.scalars().all())
        
        assert len(photos) == 2
    
    @pytest.mark.asyncio
    async def test_complaint_links_user_and_request(self, test_session, test_user, test_request):
        """Жалоба связывает пользователя и заявку"""
        complaint = Complaint(
            user_id=test_user.id,
            request_id=test_request.id,
            reason="Связь",
            text="Проверка связи"
        )
        test_session.add(complaint)
        await test_session.flush()
        
        assert complaint.user_id == test_user.id
        assert complaint.request_id == test_request.id

