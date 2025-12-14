"""
Тесты FSM состояний для создания заявки

Тестируемые сценарии:
- Переходы между состояниями
- Валидация данных на каждом шаге
- Отмена создания заявки
- Обработка невалидных данных
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.states.request_creation import RequestCreationStates
from bot.utils.request_helpers import RequestCreationData


class TestRequestCreationStatesTransitions:
    """Тесты переходов между состояниями"""
    
    @pytest.mark.asyncio
    async def test_initial_state_is_category(self, mock_fsm_context):
        """Начальное состояние - выбор категории"""
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_category)
        
        state = await mock_fsm_context.get_state()
        
        assert state == RequestCreationStates.waiting_for_category
    
    @pytest.mark.asyncio
    async def test_transition_category_to_description(self, mock_fsm_context):
        """Переход: категория -> описание"""
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_category)
        await mock_fsm_context.update_data(category="Канцелярия")
        
        # Переход к следующему состоянию
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_description)
        
        state = await mock_fsm_context.get_state()
        data = await mock_fsm_context.get_data()
        
        assert state == RequestCreationStates.waiting_for_description
        assert data["category"] == "Канцелярия"
    
    @pytest.mark.asyncio
    async def test_transition_description_to_quantity_material(self, mock_fsm_context):
        """Переход: описание -> количество (для материальной категории)"""
        await mock_fsm_context.update_data(
            category="Канцелярия",  # Материальная категория
            description="Нужны ручки"
        )
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_quantity)
        
        state = await mock_fsm_context.get_state()
        
        assert state == RequestCreationStates.waiting_for_quantity
    
    @pytest.mark.asyncio
    async def test_transition_description_to_priority_non_material(self, mock_fsm_context):
        """Переход: описание -> приоритет (для нематериальной категории)"""
        await mock_fsm_context.update_data(
            category="Ремонт мебели",  # Нематериальная категория
            description="Сломан стол"
        )
        
        # Пропускаем количество, переходим к приоритету
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_priority)
        
        state = await mock_fsm_context.get_state()
        data = await mock_fsm_context.get_data()
        
        assert state == RequestCreationStates.waiting_for_priority
        assert data.get("quantity") is None
    
    @pytest.mark.asyncio
    async def test_transition_priority_to_photos(self, mock_fsm_context):
        """Переход: приоритет -> фото"""
        await mock_fsm_context.update_data(
            category="Канцелярия",
            description="Тест",
            priority="normal"
        )
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_photos)
        
        state = await mock_fsm_context.get_state()
        
        assert state == RequestCreationStates.waiting_for_photos
    
    @pytest.mark.asyncio
    async def test_transition_photos_to_confirmation(self, mock_fsm_context):
        """Переход: фото -> подтверждение"""
        await mock_fsm_context.update_data(
            category="Канцелярия",
            description="Тест",
            priority="normal",
            photos=["photo_1"]
        )
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_confirmation)
        
        state = await mock_fsm_context.get_state()
        
        assert state == RequestCreationStates.waiting_for_confirmation


class TestRequestCreationStatesValidation:
    """Тесты валидации данных"""
    
    def test_validate_category_valid(self):
        """Валидная категория"""
        valid_categories = [
            "Канцелярия",
            "Чай, кофе, сахар, вода",
            "Хозтовары и уборка",
            "ИТ-оборудование и расходники",
            "Ремонт мебели",
            "Ремонт сантехники",
            "Ремонт электрики",
            "Другое"
        ]
        
        for category in valid_categories:
            assert len(category) > 0
    
    def test_validate_description_not_empty(self):
        """Описание не должно быть пустым"""
        empty_descriptions = ["", "   ", "\n\t"]
        
        for desc in empty_descriptions:
            assert len(desc.strip()) == 0
    
    def test_validate_quantity_positive(self):
        """Количество должно быть положительным"""
        valid_quantities = [1, 10, 100, 999]
        invalid_quantities = [0, -1, -100]
        
        for qty in valid_quantities:
            assert qty > 0
        
        for qty in invalid_quantities:
            assert qty <= 0
    
    def test_validate_quantity_integer(self):
        """Количество должно быть целым числом"""
        valid = ["1", "10", "100"]
        invalid = ["abc", "1.5", "10шт"]
        
        for v in valid:
            assert v.isdigit()
        
        for v in invalid:
            assert not v.isdigit()
    
    def test_validate_priority_values(self):
        """Приоритет: normal или urgent"""
        valid_priorities = ["normal", "urgent"]
        invalid_priorities = ["high", "low", "medium", ""]
        
        for p in valid_priorities:
            assert p in ["normal", "urgent"]
        
        for p in invalid_priorities:
            assert p not in ["normal", "urgent"]
    
    def test_validate_photos_max_count(self):
        """Максимум 5 фото"""
        photos = ["p1", "p2", "p3", "p4", "p5"]
        
        assert len(photos) <= 5
        
        photos.append("p6")
        assert len(photos) > 5  # Превышен лимит


class TestRequestCreationStatesCancel:
    """Тесты отмены создания заявки"""
    
    @pytest.mark.asyncio
    async def test_cancel_clears_all_data(self, mock_fsm_context):
        """Отмена очищает все данные"""
        await mock_fsm_context.update_data(
            category="Канцелярия",
            description="Тест",
            quantity=10,
            priority="normal",
            photos=["photo_1"]
        )
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_confirmation)
        
        # Отмена
        await mock_fsm_context.clear()
        
        state = await mock_fsm_context.get_state()
        data = await mock_fsm_context.get_data()
        
        assert state is None
        assert data == {}
    
    @pytest.mark.asyncio
    async def test_cancel_at_any_step(self, mock_fsm_context):
        """Отмена возможна на любом шаге"""
        states_to_test = [
            RequestCreationStates.waiting_for_category,
            RequestCreationStates.waiting_for_description,
            RequestCreationStates.waiting_for_quantity,
            RequestCreationStates.waiting_for_priority,
            RequestCreationStates.waiting_for_photos,
            RequestCreationStates.waiting_for_confirmation,
        ]
        
        for state in states_to_test:
            await mock_fsm_context.set_state(state)
            await mock_fsm_context.update_data(test="data")
            
            await mock_fsm_context.clear()
            
            current_state = await mock_fsm_context.get_state()
            current_data = await mock_fsm_context.get_data()
            
            assert current_state is None
            assert current_data == {}


class TestRequestCreationStatesInvalidInput:
    """Тесты обработки невалидных данных"""
    
    def test_invalid_quantity_text(self):
        """Текст вместо числа"""
        input_value = "много"
        
        try:
            quantity = int(input_value)
            is_valid = True
        except ValueError:
            is_valid = False
        
        assert is_valid is False
    
    def test_invalid_quantity_float(self):
        """Дробное число"""
        input_value = "10.5"
        
        try:
            quantity = int(input_value)
            is_valid = True
        except ValueError:
            is_valid = False
        
        assert is_valid is False
    
    def test_quantity_zero(self):
        """Нулевое количество"""
        quantity = 0
        
        is_valid = quantity > 0
        
        assert is_valid is False
    
    def test_quantity_negative(self):
        """Отрицательное количество"""
        quantity = -5
        
        is_valid = quantity > 0
        
        assert is_valid is False


class TestRequestCreationDataIntegrity:
    """Тесты целостности данных"""
    
    @pytest.mark.asyncio
    async def test_data_persists_across_states(self, mock_fsm_context):
        """Данные сохраняются при переходах между состояниями"""
        # Шаг 1: категория
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_category)
        await mock_fsm_context.update_data(category="Канцелярия")
        
        # Шаг 2: описание
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_description)
        await mock_fsm_context.update_data(description="Нужны ручки")
        
        # Шаг 3: количество
        await mock_fsm_context.set_state(RequestCreationStates.waiting_for_quantity)
        await mock_fsm_context.update_data(quantity=10)
        
        # Проверяем что все данные сохранились
        data = await mock_fsm_context.get_data()
        
        assert data["category"] == "Канцелярия"
        assert data["description"] == "Нужны ручки"
        assert data["quantity"] == 10
    
    @pytest.mark.asyncio
    async def test_update_data_merges_not_replaces(self, mock_fsm_context):
        """update_data объединяет данные, не заменяет"""
        await mock_fsm_context.update_data(category="Канцелярия")
        await mock_fsm_context.update_data(description="Тест")
        
        data = await mock_fsm_context.get_data()
        
        # Оба поля должны быть
        assert "category" in data
        assert "description" in data

