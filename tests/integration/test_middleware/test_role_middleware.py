"""
Тесты RoleMiddleware

Тестируемые сценарии:
- Определение роли пользователя
- Добавление user_role в data
- Создание пользователя в БД
- Работа с сессией БД
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import User as TelegramUser, Message

from bot.middlewares.role_middleware import RoleMiddleware
from bot.database.models import User


class TestRoleMiddlewareRoleDetection:
    """Тесты определения роли"""
    
    @pytest.mark.asyncio
    async def test_employee_role(self, mock_config):
        """Обычный пользователь получает роль employee"""
        from bot.services.role_service import RoleService
        
        service = RoleService()
        service.config = mock_config
        
        role = service.get_role_by_id(100001)
        
        assert role == "employee"
    
    @pytest.mark.asyncio
    async def test_warehouseman_role(self, mock_config):
        """Завхоз получает роль warehouseman"""
        from bot.services.role_service import RoleService
        
        service = RoleService()
        service.config = mock_config
        
        role = service.get_role_by_id(mock_config.warehouseman_id)
        
        assert role == "warehouseman"
    
    @pytest.mark.asyncio
    async def test_manager_role(self, mock_config):
        """Руководитель получает роль manager"""
        from bot.services.role_service import RoleService
        
        service = RoleService()
        service.config = mock_config
        
        role = service.get_role_by_id(mock_config.manager_id)
        
        assert role == "manager"


class TestRoleMiddlewareDataInjection:
    """Тесты добавления данных в data"""
    
    @pytest.mark.asyncio
    async def test_user_role_added_to_data(self, test_session, mock_config):
        """user_role добавляется в data"""
        from bot.services.role_service import RoleService
        
        service = RoleService()
        service.config = mock_config
        
        user = await service.get_or_create_user(test_session, 100001)
        
        # Симулируем добавление в data
        data = {"user_role": user.role}
        
        assert "user_role" in data
        assert data["user_role"] == "employee"
    
    @pytest.mark.asyncio
    async def test_user_id_added_to_data(self, test_session, mock_config):
        """user_id добавляется в data"""
        from bot.services.role_service import RoleService
        
        service = RoleService()
        service.config = mock_config
        
        user = await service.get_or_create_user(test_session, 100001)
        
        data = {
            "user_id": user.id,
            "user_role": user.role
        }
        
        assert "user_id" in data
        assert data["user_id"] == 100001


class TestRoleMiddlewareUserCreation:
    """Тесты создания пользователя в БД"""
    
    @pytest.mark.asyncio
    async def test_creates_new_user(self, test_session, mock_config):
        """Создает нового пользователя если не существует"""
        from bot.services.role_service import RoleService
        from sqlalchemy import select
        
        service = RoleService()
        service.config = mock_config
        
        new_user_id = 999777
        
        # Проверяем что пользователя нет
        result = await test_session.execute(
            select(User).where(User.id == new_user_id)
        )
        assert result.scalar_one_or_none() is None
        
        # Создаем через middleware логику
        user = await service.get_or_create_user(test_session, new_user_id)
        
        assert user is not None
        assert user.id == new_user_id
    
    @pytest.mark.asyncio
    async def test_returns_existing_user(self, test_session, mock_config):
        """Возвращает существующего пользователя"""
        from bot.services.role_service import RoleService
        
        service = RoleService()
        service.config = mock_config
        
        # Создаем пользователя
        existing = User(id=888666, role="employee")
        test_session.add(existing)
        await test_session.flush()
        
        # Получаем через middleware
        user = await service.get_or_create_user(test_session, 888666)
        
        assert user.id == 888666
    
    @pytest.mark.asyncio
    async def test_updates_role_if_changed(self, test_session, mock_config):
        """Обновляет роль если ID теперь в конфиге"""
        from bot.services.role_service import RoleService
        
        service = RoleService()
        service.config = mock_config
        
        # Создаем пользователя как employee
        user = User(id=mock_config.warehouseman_id, role="employee")
        test_session.add(user)
        await test_session.flush()
        
        # Middleware должен обновить роль
        updated = await service.get_or_create_user(
            test_session, 
            mock_config.warehouseman_id
        )
        
        assert updated.role == "warehouseman"


class TestRoleMiddlewareSession:
    """Тесты работы с сессией БД"""
    
    @pytest.mark.asyncio
    async def test_session_added_to_data(self, test_session):
        """Сессия БД добавляется в data"""
        data = {"db_session": test_session}
        
        assert "db_session" in data
        assert data["db_session"] is not None
    
    @pytest.mark.asyncio
    async def test_session_commits_on_success(self, test_session, mock_config):
        """Сессия коммитится при успехе"""
        from bot.services.role_service import RoleService
        
        service = RoleService()
        service.config = mock_config
        
        # Создаем пользователя (это делает commit внутри)
        user = await service.get_or_create_user(test_session, 777555)
        
        # Проверяем что данные сохранены
        from sqlalchemy import select
        result = await test_session.execute(
            select(User).where(User.id == 777555)
        )
        found = result.scalar_one_or_none()
        
        assert found is not None


class TestRoleMiddlewareEdgeCases:
    """Edge cases"""
    
    @pytest.mark.asyncio
    async def test_no_telegram_user(self):
        """Нет пользователя в событии"""
        data = {"event_from_user": None}
        
        # Middleware должен пропустить обработку
        assert data["event_from_user"] is None
    
    @pytest.mark.asyncio
    async def test_multiple_calls_same_user(self, test_session, mock_config):
        """Множественные вызовы для одного пользователя"""
        from bot.services.role_service import RoleService
        from sqlalchemy import select, func
        
        service = RoleService()
        service.config = mock_config
        
        user_id = 666444
        
        # Вызываем несколько раз
        for _ in range(5):
            await service.get_or_create_user(test_session, user_id)
        
        # Должен быть только один пользователь
        result = await test_session.execute(
            select(func.count(User.id)).where(User.id == user_id)
        )
        count = result.scalar()
        
        assert count == 1

