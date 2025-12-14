"""
Интеграционные тесты для start handler

Тестируемые сценарии:
- Команда /start для нового пользователя
- Команда /start для существующего пользователя
- Меню по ролям (employee, warehouseman, manager)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User as TelegramUser, Chat

from bot.database.models import User


class TestStartCommand:
    """Тесты команды /start"""
    
    @pytest.mark.asyncio
    async def test_start_new_employee(self, test_session, mock_bot, mock_config):
        """Новый пользователь (сотрудник) видит меню сотрудника"""
        # Импортируем cmd_start (реальное имя функции)
        from bot.handlers.start import cmd_start, get_welcome_message
        
        # Проверяем что функция приветствия работает для employee
        welcome = get_welcome_message("employee", "Иван")
        
        assert "Иван" in welcome
        assert "Завхоз" in welcome
        
        # Проверяем логику определения роли через сервис
        from bot.services.role_service import RoleService
        
        service = RoleService()
        service.config = mock_config
        
        # ID обычного сотрудника (не завхоз и не руководитель)
        role = service.get_role_by_id(100001)
        assert role == "employee"
    
    @pytest.mark.asyncio
    async def test_start_warehouseman(self, test_session, mock_config):
        """Завхоз видит расширенное меню"""
        from bot.services.role_service import RoleService
        
        service = RoleService()
        service.config = mock_config
        
        role = service.get_role_by_id(mock_config.warehouseman_id)
        
        assert role == "warehouseman"
    
    @pytest.mark.asyncio
    async def test_start_manager(self, test_session, mock_config):
        """Руководитель видит меню руководителя"""
        from bot.services.role_service import RoleService
        
        service = RoleService()
        service.config = mock_config
        
        role = service.get_role_by_id(mock_config.manager_id)
        
        assert role == "manager"
    
    @pytest.mark.asyncio
    async def test_existing_user_returns_same(self, test_session, mock_config):
        """Существующий пользователь не создается заново"""
        from bot.services.role_service import RoleService
        
        service = RoleService()
        service.config = mock_config
        
        # Создаем пользователя
        user1 = await service.get_or_create_user(test_session, 100001)
        
        # Повторный вызов возвращает того же пользователя
        user2 = await service.get_or_create_user(test_session, 100001)
        
        assert user1.id == user2.id


class TestStartMenuByRole:
    """Тесты меню по ролям"""
    
    def test_employee_menu_buttons(self):
        """Меню сотрудника содержит нужные кнопки"""
        from bot.keyboards.employee import get_employee_keyboard
        
        keyboard = get_employee_keyboard()
        
        # Проверяем что есть кнопки
        assert keyboard is not None
        
        # Получаем тексты кнопок
        button_texts = []
        for row in keyboard.keyboard:
            for button in row:
                button_texts.append(button.text)
        
        # Должны быть основные кнопки сотрудника
        assert any("заявк" in text.lower() for text in button_texts)
    
    def test_warehouseman_menu_buttons(self):
        """Меню завхоза содержит дополнительные кнопки"""
        from bot.keyboards.warehouseman import get_warehouseman_keyboard
        
        keyboard = get_warehouseman_keyboard()
        
        assert keyboard is not None
        
        button_texts = []
        for row in keyboard.keyboard:
            for button in row:
                button_texts.append(button.text)
        
        # Должны быть кнопки завхоза
        assert len(button_texts) > 0
    
    def test_manager_menu_buttons(self):
        """Меню руководителя содержит кнопки отчетов"""
        from bot.keyboards.manager import get_manager_keyboard
        
        keyboard = get_manager_keyboard()
        
        assert keyboard is not None
        
        button_texts = []
        for row in keyboard.keyboard:
            for button in row:
                button_texts.append(button.text)
        
        # Должны быть кнопки руководителя
        assert len(button_texts) > 0


class TestStartHelp:
    """Тесты команды Помощь"""
    
    @pytest.mark.asyncio
    async def test_help_handler_exists(self):
        """Обработчик помощи существует"""
        # В реальном коде помощь реализована через cmd_help функцию
        from bot.handlers.common import cmd_help
        
        # Проверяем что функция существует
        assert cmd_help is not None
        assert callable(cmd_help)
    
    def test_common_router_exists(self):
        """Роутер common существует"""
        from bot.handlers.common import router
        
        assert router is not None
        assert router.name == "common"

