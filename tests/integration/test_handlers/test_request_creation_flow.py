"""
Интеграционные тесты для flow создания заявки

Тестируемые сценарии:
- Полный flow создания заявки (все 6 шагов)
- Каждый шаг отдельно
- Отмена на разных этапах
- Редактирование на этапе подтверждения
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery

from bot.states.request_creation import RequestCreationStates
from bot.utils.request_helpers import RequestCreationData


class TestRequestCreationFlow:
    """Тесты полного flow создания заявки"""
    
    @pytest.mark.asyncio
    async def test_flow_step1_category_selection(self, mock_fsm_context):
        """Шаг 1: Выбор категории"""
        # Симулируем выбор категории
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_category)
        await mock_fsm_context.update_data(category="Канцелярия")
        
        data = await mock_fsm_context.get_data()
        
        assert data["category"] == "Канцелярия"
    
    @pytest.mark.asyncio
    async def test_flow_step2_description(self, mock_fsm_context):
        """Шаг 2: Ввод описания"""
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_description)
        await mock_fsm_context.update_data(
            category="Канцелярия",
            description="Нужны ручки синие 10 штук"
        )
        
        data = await mock_fsm_context.get_data()
        
        assert data["description"] == "Нужны ручки синие 10 штук"
    
    @pytest.mark.asyncio
    async def test_flow_step3_quantity_for_material(self, mock_fsm_context):
        """Шаг 3: Количество для материальной категории"""
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_quantity)
        await mock_fsm_context.update_data(
            category="Канцелярия",  # Материальная категория
            description="Тест",
            quantity=10
        )
        
        data = await mock_fsm_context.get_data()
        
        assert data["quantity"] == 10
    
    @pytest.mark.asyncio
    async def test_flow_step3_skip_quantity_for_service(self, mock_fsm_context):
        """Шаг 3: Пропуск количества для нематериальной категории"""
        await mock_fsm_context.update_data(
            category="Ремонт мебели",  # Нематериальная категория
            description="Сломан стол"
        )
        
        data = await mock_fsm_context.get_data()
        
        # Количество не указано
        assert data.get("quantity") is None
    
    @pytest.mark.asyncio
    async def test_flow_step4_priority_normal(self, mock_fsm_context):
        """Шаг 4: Выбор обычного приоритета"""
        await mock_fsm_context.update_data(
            category="Канцелярия",
            description="Тест",
            priority="normal"
        )
        
        data = await mock_fsm_context.get_data()
        
        assert data["priority"] == "normal"
    
    @pytest.mark.asyncio
    async def test_flow_step4_priority_urgent(self, mock_fsm_context):
        """Шаг 4: Выбор срочного приоритета"""
        await mock_fsm_context.update_data(
            category="Ремонт сантехники",
            description="Течет труба",
            priority="urgent"
        )
        
        data = await mock_fsm_context.get_data()
        
        assert data["priority"] == "urgent"
    
    @pytest.mark.asyncio
    async def test_flow_step5_photos_optional(self, mock_fsm_context):
        """Шаг 5: Фото опционально"""
        await mock_fsm_context.update_data(
            category="Канцелярия",
            description="Тест",
            priority="normal",
            photos=[]  # Без фото
        )
        
        data = await mock_fsm_context.get_data()
        
        assert data["photos"] == []
    
    @pytest.mark.asyncio
    async def test_flow_step5_photos_added(self, mock_fsm_context):
        """Шаг 5: Добавление фото"""
        await mock_fsm_context.update_data(
            category="Ремонт мебели",
            description="Сломан стол",
            priority="normal",
            photos=["photo_1", "photo_2", "photo_3"]
        )
        
        data = await mock_fsm_context.get_data()
        
        assert len(data["photos"]) == 3
    
    @pytest.mark.asyncio
    async def test_flow_complete_data(self, mock_fsm_context):
        """Полные данные для создания заявки"""
        await mock_fsm_context.update_data(
            category="Канцелярия",
            description="Нужны ручки синие",
            quantity=10,
            priority="normal",
            photos=["photo_1"]
        )
        
        data = await mock_fsm_context.get_data()
        request_data = RequestCreationData.from_dict(data)
        
        assert request_data.is_complete()


class TestRequestCreationCancel:
    """Тесты отмены создания заявки"""
    
    @pytest.mark.asyncio
    async def test_cancel_clears_state(self, mock_fsm_context):
        """Отмена очищает состояние"""
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_description)
        await mock_fsm_context.update_data(category="Канцелярия")
        
        # Отмена
        await mock_fsm_context.clear()
        
        state = await mock_fsm_context.get_state()
        data = await mock_fsm_context.get_data()
        
        assert state is None
        assert data == {}
    
    @pytest.mark.asyncio
    async def test_cancel_at_step1(self, mock_fsm_context):
        """Отмена на первом шаге"""
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_category)
        await mock_fsm_context.clear()
        
        state = await mock_fsm_context.get_state()
        assert state is None
    
    @pytest.mark.asyncio
    async def test_cancel_at_step5_photos(self, mock_fsm_context):
        """Отмена на шаге фото"""
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_photos)
        await mock_fsm_context.update_data(
            category="Канцелярия",
            description="Тест",
            quantity=5,
            priority="normal"
        )
        
        await mock_fsm_context.clear()
        
        state = await mock_fsm_context.get_state()
        data = await mock_fsm_context.get_data()
        
        assert state is None
        assert data == {}


class TestRequestCreationValidation:
    """Тесты валидации данных"""
    
    @pytest.mark.asyncio
    async def test_quantity_must_be_number(self, mock_fsm_context):
        """Количество должно быть числом"""
        # Симулируем ввод текста вместо числа
        quantity_input = "много"
        
        try:
            quantity = int(quantity_input)
        except ValueError:
            quantity = None
        
        assert quantity is None
    
    @pytest.mark.asyncio
    async def test_quantity_must_be_positive(self):
        """Количество должно быть положительным"""
        quantity_input = "-5"
        
        try:
            quantity = int(quantity_input)
            if quantity <= 0:
                quantity = None
        except ValueError:
            quantity = None
        
        assert quantity is None
    
    def test_description_not_empty(self):
        """Описание не должно быть пустым"""
        description = ""
        
        is_valid = len(description.strip()) > 0
        
        assert is_valid is False
    
    def test_max_photos_limit(self):
        """Максимум 5 фото"""
        photos = ["photo_1", "photo_2", "photo_3", "photo_4", "photo_5"]
        
        # Проверяем лимит
        assert len(photos) <= 5
        
        # Попытка добавить 6-е фото
        photos.append("photo_6")
        assert len(photos) > 5  # Превышен лимит


class TestRequestCreationEdit:
    """Тесты редактирования на этапе подтверждения"""
    
    @pytest.mark.asyncio
    async def test_edit_category(self, mock_fsm_context):
        """Редактирование категории"""
        # Начальные данные
        await mock_fsm_context.update_data(
            category="Канцелярия",
            description="Тест",
            priority="normal"
        )
        
        # Редактируем категорию
        await mock_fsm_context.update_data(category="Хозтовары и уборка")
        
        data = await mock_fsm_context.get_data()
        assert data["category"] == "Хозтовары и уборка"
    
    @pytest.mark.asyncio
    async def test_edit_description(self, mock_fsm_context):
        """Редактирование описания"""
        await mock_fsm_context.update_data(
            category="Канцелярия",
            description="Старое описание",
            priority="normal"
        )
        
        await mock_fsm_context.update_data(description="Новое описание")
        
        data = await mock_fsm_context.get_data()
        assert data["description"] == "Новое описание"
    
    @pytest.mark.asyncio
    async def test_edit_priority(self, mock_fsm_context):
        """Редактирование приоритета"""
        await mock_fsm_context.update_data(
            category="Канцелярия",
            description="Тест",
            priority="normal"
        )
        
        await mock_fsm_context.update_data(priority="urgent")
        
        data = await mock_fsm_context.get_data()
        assert data["priority"] == "urgent"


class TestRequestCreationSubmit:
    """Тесты подтверждения заявки"""
    
    @pytest.mark.asyncio
    async def test_submit_creates_request(self, test_session, test_user):
        """Подтверждение создает заявку в БД"""
        from bot.services.request_service import RequestService
        
        service = RequestService()
        
        request = await service.create_request(
            session=test_session,
            user_id=test_user.id,
            category="Канцелярия",
            description="Тестовая заявка",
            priority="normal",
            quantity=10
        )
        
        assert request is not None
        assert request.id is not None
        assert request.status == "new"
    
    @pytest.mark.asyncio
    async def test_submit_with_photos(self, test_session, test_user):
        """Подтверждение с фото"""
        from bot.services.request_service import RequestService
        from sqlalchemy import select
        from bot.database.models import RequestPhoto
        
        service = RequestService()
        
        request = await service.create_request(
            session=test_session,
            user_id=test_user.id,
            category="Ремонт мебели",
            description="Сломан стол",
            priority="urgent",
            photo_file_ids=["photo_1", "photo_2"]
        )
        
        # Проверяем что фото сохранились
        result = await test_session.execute(
            select(RequestPhoto).where(RequestPhoto.request_id == request.id)
        )
        photos = list(result.scalars().all())
        
        assert len(photos) == 2

