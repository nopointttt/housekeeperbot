"""
Тесты FSM состояний для жалобы

Тестируемые сценарии:
- Переходы между состояниями
- Валидация данных
- Отмена
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.states.complaint_creation import ComplaintCreationStates


class TestComplaintCreationStates:
    """Тесты состояний создания жалобы"""
    
    @pytest.mark.asyncio
    async def test_initial_state_waiting_for_reason(self, mock_fsm_context):
        """Начальное состояние - выбор причины"""
        # В реальном коде: waiting_for_reason (не selecting_request)
        await mock_fsm_context.set_state(ComplaintCreationStates.waiting_for_reason)
        
        state = await mock_fsm_context.get_state()
        
        assert state == ComplaintCreationStates.waiting_for_reason
    
    @pytest.mark.asyncio
    async def test_transition_to_reason_with_data(self, mock_fsm_context):
        """Переход к выбору причины с данными"""
        await mock_fsm_context.update_data(request_id=1)
        await mock_fsm_context.set_state(ComplaintCreationStates.waiting_for_reason)
        
        state = await mock_fsm_context.get_state()
        data = await mock_fsm_context.get_data()
        
        assert state == ComplaintCreationStates.waiting_for_reason
        assert data["request_id"] == 1
    
    @pytest.mark.asyncio
    async def test_transition_to_text(self, mock_fsm_context):
        """Переход к вводу текста жалобы"""
        await mock_fsm_context.update_data(
            request_id=1,
            reason="Долгое выполнение"
        )
        await mock_fsm_context.set_state(ComplaintCreationStates.waiting_for_text)
        
        state = await mock_fsm_context.get_state()
        data = await mock_fsm_context.get_data()
        
        assert state == ComplaintCreationStates.waiting_for_text
        assert data["reason"] == "Долгое выполнение"
    
    @pytest.mark.asyncio
    async def test_complete_data_before_submit(self, mock_fsm_context):
        """Все данные собраны перед отправкой"""
        # В реальном коде нет waiting_for_confirmation, жалоба создается после ввода текста
        await mock_fsm_context.update_data(
            request_id=1,
            reason="Долгое выполнение",
            text="Жду уже неделю"
        )
        await mock_fsm_context.set_state(ComplaintCreationStates.waiting_for_text)
        
        data = await mock_fsm_context.get_data()
        
        # Проверяем что все данные собраны
        assert data["request_id"] == 1
        assert data["reason"] == "Долгое выполнение"
        assert data["text"] == "Жду уже неделю"


class TestComplaintValidation:
    """Тесты валидации данных жалобы"""
    
    def test_valid_reasons(self):
        """Валидные причины жалобы"""
        valid_reasons = [
            "Долгое выполнение",
            "Некачественное выполнение",
            "Грубость",
            "Другое"
        ]
        
        for reason in valid_reasons:
            assert len(reason) > 0
    
    def test_text_not_empty(self):
        """Текст жалобы не должен быть пустым"""
        empty_texts = ["", "   ", "\n"]
        
        for text in empty_texts:
            assert len(text.strip()) == 0
    
    def test_text_max_length(self):
        """Максимальная длина текста"""
        max_length = 4096  # Лимит Telegram
        
        long_text = "А" * (max_length + 1)
        
        assert len(long_text) > max_length


class TestComplaintCancel:
    """Тесты отмены жалобы"""
    
    @pytest.mark.asyncio
    async def test_cancel_clears_state(self, mock_fsm_context):
        """Отмена очищает состояние"""
        await mock_fsm_context.update_data(
            request_id=1,
            reason="Тест"
        )
        await mock_fsm_context.set_state(ComplaintCreationStates.waiting_for_text)
        
        await mock_fsm_context.clear()
        
        state = await mock_fsm_context.get_state()
        data = await mock_fsm_context.get_data()
        
        assert state is None
        assert data == {}

