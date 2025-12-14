"""
Unit тесты для RoleService

Тестируемые методы:
- get_role_by_id() - определение роли по Telegram ID
- get_or_create_user() - получение или создание пользователя
- is_role(), is_employee(), is_warehouseman(), is_manager() - проверка ролей
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import select

from bot.services.role_service import RoleService
from bot.database.models import User


class TestRoleServiceGetRoleById:
    """Тесты определения роли по ID"""
    
    def test_get_role_by_id_warehouseman(self, mock_config):
        """ID завхоза возвращает роль 'warehouseman'"""
        service = RoleService()
        service.config = mock_config
        
        role = service.get_role_by_id(mock_config.warehouseman_id)
        
        assert role == "warehouseman"
    
    def test_get_role_by_id_manager(self, mock_config):
        """ID руководителя возвращает роль 'manager'"""
        service = RoleService()
        service.config = mock_config
        
        role = service.get_role_by_id(mock_config.manager_id)
        
        assert role == "manager"
    
    def test_get_role_by_id_employee(self, mock_config):
        """Любой другой ID возвращает роль 'employee'"""
        service = RoleService()
        service.config = mock_config
        
        # Любой ID, отличный от завхоза и руководителя
        role = service.get_role_by_id(12345)
        
        assert role == "employee"
    
    def test_get_role_by_id_random_ids(self, mock_config):
        """Случайные ID - всегда employee"""
        service = RoleService()
        service.config = mock_config
        
        random_ids = [1, 100, 1000, 10000, 100000, 9999999]
        
        for user_id in random_ids:
            if user_id not in [mock_config.warehouseman_id, mock_config.manager_id]:
                assert service.get_role_by_id(user_id) == "employee"


class TestRoleServiceGetOrCreateUser:
    """Тесты получения/создания пользователя"""
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_creates_new(self, test_session, mock_config):
        """Создание нового пользователя если не существует"""
        service = RoleService()
        service.config = mock_config
        
        new_user_id = 123456
        
        # Проверяем что пользователя нет
        result = await test_session.execute(
            select(User).where(User.id == new_user_id)
        )
        assert result.scalar_one_or_none() is None
        
        # Создаем пользователя
        user = await service.get_or_create_user(test_session, new_user_id)
        
        assert user is not None
        assert user.id == new_user_id
        assert user.role == "employee"
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_returns_existing(self, test_session, mock_config):
        """Возвращает существующего пользователя"""
        service = RoleService()
        service.config = mock_config
        
        # Создаем пользователя вручную
        existing_user = User(id=789012, role="employee")
        test_session.add(existing_user)
        await test_session.flush()
        
        # Пытаемся получить/создать
        user = await service.get_or_create_user(test_session, 789012)
        
        assert user.id == existing_user.id
        assert user.role == "employee"
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_updates_role_if_changed(self, test_session, mock_config):
        """Обновляет роль если ID теперь в конфиге (стал завхозом/руководителем)"""
        service = RoleService()
        service.config = mock_config
        
        # Создаем пользователя как employee
        user = User(id=mock_config.warehouseman_id, role="employee")
        test_session.add(user)
        await test_session.flush()
        
        # Теперь get_or_create должен обновить роль на warehouseman
        updated_user = await service.get_or_create_user(
            test_session, 
            mock_config.warehouseman_id
        )
        
        assert updated_user.role == "warehouseman"
    
    @pytest.mark.asyncio
    async def test_get_or_create_warehouseman(self, test_session, mock_config):
        """Создание пользователя-завхоза"""
        service = RoleService()
        service.config = mock_config
        
        user = await service.get_or_create_user(
            test_session, 
            mock_config.warehouseman_id
        )
        
        assert user.role == "warehouseman"
    
    @pytest.mark.asyncio
    async def test_get_or_create_manager(self, test_session, mock_config):
        """Создание пользователя-руководителя"""
        service = RoleService()
        service.config = mock_config
        
        user = await service.get_or_create_user(
            test_session, 
            mock_config.manager_id
        )
        
        assert user.role == "manager"


class TestRoleServiceIsRole:
    """Тесты проверки ролей"""
    
    @pytest.mark.asyncio
    async def test_is_role_employee(self, test_session, mock_config):
        """Проверка роли employee"""
        service = RoleService()
        service.config = mock_config
        
        # Создаем пользователя-сотрудника
        user = User(id=111111, role="employee")
        test_session.add(user)
        await test_session.flush()
        
        result = await service.is_role(test_session, 111111, "employee")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_is_role_wrong_role(self, test_session, mock_config):
        """Проверка неправильной роли возвращает False"""
        service = RoleService()
        service.config = mock_config
        
        user = User(id=222222, role="employee")
        test_session.add(user)
        await test_session.flush()
        
        result = await service.is_role(test_session, 222222, "manager")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_is_employee(self, test_session, mock_config):
        """Проверка is_employee()"""
        service = RoleService()
        service.config = mock_config
        
        user = User(id=333333, role="employee")
        test_session.add(user)
        await test_session.flush()
        
        assert await service.is_employee(test_session, 333333) is True
        assert await service.is_warehouseman(test_session, 333333) is False
        assert await service.is_manager(test_session, 333333) is False
    
    @pytest.mark.asyncio
    async def test_is_warehouseman(self, test_session, mock_config):
        """Проверка is_warehouseman()"""
        service = RoleService()
        service.config = mock_config
        
        user = User(id=mock_config.warehouseman_id, role="warehouseman")
        test_session.add(user)
        await test_session.flush()
        
        assert await service.is_warehouseman(test_session, mock_config.warehouseman_id) is True
        assert await service.is_employee(test_session, mock_config.warehouseman_id) is False
    
    @pytest.mark.asyncio
    async def test_is_manager(self, test_session, mock_config):
        """Проверка is_manager()"""
        service = RoleService()
        service.config = mock_config
        
        user = User(id=mock_config.manager_id, role="manager")
        test_session.add(user)
        await test_session.flush()
        
        assert await service.is_manager(test_session, mock_config.manager_id) is True
        assert await service.is_employee(test_session, mock_config.manager_id) is False


class TestRoleServiceEdgeCases:
    """Edge cases"""
    
    @pytest.mark.asyncio
    async def test_get_or_create_with_username(self, test_session, mock_config):
        """Создание пользователя с username (username не сохраняется в модели)"""
        service = RoleService()
        service.config = mock_config
        
        user = await service.get_or_create_user(
            test_session, 
            444444, 
            username="test_username"
        )
        
        assert user.id == 444444
        # Username не хранится в модели User (по текущей схеме)
    
    @pytest.mark.asyncio
    async def test_concurrent_get_or_create(self, test_session, mock_config):
        """Повторный вызов get_or_create не создает дубликат"""
        service = RoleService()
        service.config = mock_config
        
        user1 = await service.get_or_create_user(test_session, 555555)
        user2 = await service.get_or_create_user(test_session, 555555)
        
        # Должен быть один и тот же пользователь
        assert user1.id == user2.id
        
        # Проверяем что в БД только один
        result = await test_session.execute(
            select(User).where(User.id == 555555)
        )
        users = list(result.scalars().all())
        assert len(users) == 1

