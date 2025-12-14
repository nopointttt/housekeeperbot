"""
Unit тесты для NotificationService

Тестируемые методы:
- notify_warehouseman_new_request() - уведомление завхозу о новой заявке
- notify_manager_complaint() - уведомление руководителю о жалобе
- notify_warehouseman_complaint() - уведомление завхозу о жалобе на него
- notify_employee_request_status_changed() - уведомление сотруднику о смене статуса
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from bot.services.notification_service import NotificationService
from bot.database.models import Request, Complaint, User


class TestNotificationServiceWarehousemanNewRequest:
    """Тесты уведомления завхозу о новой заявке"""
    
    @pytest.mark.asyncio
    async def test_notify_warehouseman_new_request_calls_bot(self, mock_bot, mock_config):
        """Отправляется сообщение боту"""
        service = NotificationService(mock_bot)
        service.config = mock_config
        
        # Создаем мок заявки
        request = MagicMock(spec=Request)
        request.id = 1
        request.number = "ЗХ-010125-001"
        request.category = "Канцелярия"
        request.description = "Тестовое описание"
        request.quantity = 10
        request.priority = "normal"
        request.status = "new"
        request.created_at = datetime.now()
        request.updated_at = datetime.now()
        request.completed_at = None
        request.rejection_reason = None
        request.photos = []
        
        # Патчим функции по месту их определения (они импортируются внутри метода)
        with patch('bot.utils.request_formatter.format_request_full', return_value="Форматированная заявка"):
            with patch('bot.keyboards.inline.get_request_actions_keyboard', return_value=MagicMock()):
                await service.notify_warehouseman_new_request(request)
        
        # Проверяем что send_message был вызван
        mock_bot.send_message.assert_called_once()
        
        # Проверяем параметры
        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs['chat_id'] == mock_config.warehouseman_id
        assert "🆕" in call_args.kwargs['text'] or "Новая заявка" in call_args.kwargs['text']
        assert call_args.kwargs['parse_mode'] == "HTML"
    
    @pytest.mark.asyncio
    async def test_notify_warehouseman_new_request_handles_error(self, mock_bot, mock_config):
        """Ошибка отправки не прерывает выполнение"""
        service = NotificationService(mock_bot)
        service.config = mock_config
        
        # Мок бота выбрасывает ошибку
        mock_bot.send_message = AsyncMock(side_effect=Exception("Network error"))
        
        request = MagicMock(spec=Request)
        request.id = 1
        request.number = "ЗХ-010125-001"
        request.category = "Канцелярия"
        request.description = "Тест"
        request.quantity = None
        request.priority = "normal"
        request.status = "new"
        request.created_at = datetime.now()
        request.updated_at = datetime.now()
        request.completed_at = None
        request.rejection_reason = None
        request.photos = []
        
        with patch('bot.utils.request_formatter.format_request_full', return_value="Текст"):
            with patch('bot.keyboards.inline.get_request_actions_keyboard', return_value=MagicMock()):
                # Не должно выбрасывать исключение
                await service.notify_warehouseman_new_request(request)


class TestNotificationServiceManagerComplaint:
    """Тесты уведомления руководителю о жалобе"""
    
    @pytest.mark.asyncio
    async def test_notify_manager_complaint_calls_bot(self, mock_bot, mock_config):
        """Отправляется сообщение руководителю"""
        service = NotificationService(mock_bot)
        service.config = mock_config
        
        # Создаем моки
        user = MagicMock(spec=User)
        user.first_name = "Иван"
        
        complaint = MagicMock(spec=Complaint)
        complaint.user = user
        complaint.reason = "Долгое выполнение"
        complaint.text = "Жду неделю"
        complaint.created_at = datetime.now()
        
        request = MagicMock(spec=Request)
        request.number = "ЗХ-010125-001"
        request.status = "new"
        request.category = "Канцелярия"
        request.description = "Тест"
        request.created_at = datetime.now()
        
        with patch('bot.utils.request_formatter.format_request_short', return_value="Краткое описание"):
            await service.notify_manager_complaint(complaint, request)
        
        # Проверяем вызов
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs['chat_id'] == mock_config.manager_id
        assert "⚠️" in call_args.kwargs['text'] or "Жалоба" in call_args.kwargs['text']
    
    @pytest.mark.asyncio
    async def test_notify_manager_complaint_handles_error(self, mock_bot, mock_config):
        """Ошибка не прерывает выполнение"""
        service = NotificationService(mock_bot)
        service.config = mock_config
        
        mock_bot.send_message = AsyncMock(side_effect=Exception("Error"))
        
        user = MagicMock()
        user.first_name = "Тест"
        
        complaint = MagicMock()
        complaint.user = user
        complaint.reason = "Тест"
        complaint.text = "Тест"
        complaint.created_at = datetime.now()
        
        request = MagicMock()
        request.number = "ЗХ-010125-001"
        request.status = "new"
        request.category = "Тест"
        request.description = "Тест"
        request.created_at = datetime.now()
        
        with patch('bot.utils.request_formatter.format_request_short', return_value="Текст"):
            await service.notify_manager_complaint(complaint, request)


class TestNotificationServiceWarehousemanComplaint:
    """Тесты уведомления завхозу о жалобе на него"""
    
    @pytest.mark.asyncio
    async def test_notify_warehouseman_complaint_calls_bot(self, mock_bot, mock_config):
        """Отправляется сообщение завхозу"""
        service = NotificationService(mock_bot)
        service.config = mock_config
        
        user = MagicMock()
        user.first_name = "Петр"
        
        complaint = MagicMock()
        complaint.user = user
        complaint.reason = "Грубость"
        complaint.text = "Грубо ответил"
        complaint.created_at = datetime.now()
        
        request = MagicMock()
        request.number = "ЗХ-010125-001"
        request.status = "new"
        request.category = "Канцелярия"
        request.description = "Тест"
        request.created_at = datetime.now()
        
        with patch('bot.utils.request_formatter.format_request_short', return_value="Краткое"):
            await service.notify_warehouseman_complaint(complaint, request)
        
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs['chat_id'] == mock_config.warehouseman_id
        assert "Жалоба на вас" in call_args.kwargs['text']


class TestNotificationServiceEmployeeStatusChanged:
    """Тесты уведомления сотруднику о смене статуса"""
    
    @pytest.mark.asyncio
    async def test_notify_employee_status_changed_calls_bot(self, mock_bot, mock_config):
        """Отправляется сообщение сотруднику"""
        service = NotificationService(mock_bot)
        service.config = mock_config
        
        request = MagicMock()
        request.user_id = 100001
        request.number = "ЗХ-010125-001"
        request.status = "in_progress"
        request.category = "Канцелярия"
        request.description = "Тест"
        request.created_at = datetime.now()
        request.rejection_reason = None
        
        with patch('bot.utils.request_formatter.format_request_short', return_value="Краткое"):
            await service.notify_employee_request_status_changed(request, "В работе")
        
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert call_args.kwargs['chat_id'] == 100001
        assert "🔄" in call_args.kwargs['text'] or "Статус" in call_args.kwargs['text']
    
    @pytest.mark.asyncio
    async def test_notify_employee_includes_rejection_reason(self, mock_bot, mock_config):
        """При отклонении включается причина"""
        service = NotificationService(mock_bot)
        service.config = mock_config
        
        request = MagicMock()
        request.user_id = 100001
        request.number = "ЗХ-010125-001"
        request.status = "rejected"
        request.category = "Канцелярия"
        request.description = "Тест"
        request.created_at = datetime.now()
        request.rejection_reason = "Нет в наличии"
        
        with patch('bot.utils.request_formatter.format_request_short', return_value="Краткое"):
            await service.notify_employee_request_status_changed(request, "Отклонено")
        
        call_args = mock_bot.send_message.call_args
        assert "Нет в наличии" in call_args.kwargs['text']
    
    @pytest.mark.asyncio
    async def test_notify_employee_handles_error(self, mock_bot, mock_config):
        """Ошибка не прерывает выполнение"""
        service = NotificationService(mock_bot)
        service.config = mock_config
        
        mock_bot.send_message = AsyncMock(side_effect=Exception("Error"))
        
        request = MagicMock()
        request.user_id = 100001
        request.number = "ЗХ-010125-001"
        request.status = "completed"
        request.category = "Тест"
        request.description = "Тест"
        request.created_at = datetime.now()
        request.rejection_reason = None
        
        with patch('bot.utils.request_formatter.format_request_short', return_value="Текст"):
            await service.notify_employee_request_status_changed(request, "Выполнено")
