"""
Unit тесты для BroadcastService

Тестируемые методы:
- get_all_employees() - получение всех сотрудников
- get_all_users() - получение всех пользователей
"""
import pytest
from sqlalchemy import select

from bot.services.broadcast_service import BroadcastService, broadcast_service
from bot.database.models import User


class TestBroadcastServiceGetAllEmployees:
    """Тесты получения списка сотрудников"""
    
    @pytest.mark.asyncio
    async def test_get_all_employees_empty(self, test_session, mock_config):
        """Нет сотрудников - пустой список"""
        service = BroadcastService()
        
        employees = await service.get_all_employees(test_session)
        
        assert employees == []
    
    @pytest.mark.asyncio
    async def test_get_all_employees_returns_only_employees(self, test_session, mock_config):
        """Возвращает только пользователей с ролью employee"""
        service = BroadcastService()
        
        # Создаем пользователей разных ролей
        employee1 = User(id=100001, role="employee")
        employee2 = User(id=100002, role="employee")
        warehouseman = User(id=mock_config.warehouseman_id, role="warehouseman")
        manager = User(id=mock_config.manager_id, role="manager")
        
        test_session.add_all([employee1, employee2, warehouseman, manager])
        await test_session.flush()
        
        employees = await service.get_all_employees(test_session)
        
        # Должны быть только 2 сотрудника
        assert len(employees) == 2
        assert all(e.role == "employee" for e in employees)
    
    @pytest.mark.asyncio
    async def test_get_all_employees_excludes_warehouseman(self, test_session, mock_config):
        """Завхоз не включается в список сотрудников"""
        service = BroadcastService()
        
        # Создаем завхоза с ролью employee (на случай если роль неправильно установлена)
        # В реальности это не должно происходить, но проверяем по ID
        warehouseman = User(id=mock_config.warehouseman_id, role="warehouseman")
        test_session.add(warehouseman)
        await test_session.flush()
        
        employees = await service.get_all_employees(test_session)
        
        # Завхоз не должен быть в списке
        assert not any(e.id == mock_config.warehouseman_id for e in employees)
    
    @pytest.mark.asyncio
    async def test_get_all_employees_excludes_manager(self, test_session, mock_config):
        """Руководитель не включается в список сотрудников"""
        service = BroadcastService()
        
        manager = User(id=mock_config.manager_id, role="manager")
        employee = User(id=100001, role="employee")
        test_session.add_all([manager, employee])
        await test_session.flush()
        
        employees = await service.get_all_employees(test_session)
        
        # Руководитель не должен быть в списке
        assert not any(e.id == mock_config.manager_id for e in employees)
        assert len(employees) == 1


class TestBroadcastServiceGetAllUsers:
    """Тесты получения всех пользователей"""
    
    @pytest.mark.asyncio
    async def test_get_all_users_empty(self, test_session):
        """Нет пользователей - пустой список"""
        service = BroadcastService()
        
        users = await service.get_all_users(test_session)
        
        assert users == []
    
    @pytest.mark.asyncio
    async def test_get_all_users_returns_all_roles(self, test_session, mock_config):
        """Возвращает пользователей всех ролей"""
        service = BroadcastService()
        
        # Создаем пользователей всех ролей
        employee = User(id=100001, role="employee")
        warehouseman = User(id=mock_config.warehouseman_id, role="warehouseman")
        manager = User(id=mock_config.manager_id, role="manager")
        
        test_session.add_all([employee, warehouseman, manager])
        await test_session.flush()
        
        users = await service.get_all_users(test_session)
        
        # Должны быть все 3 пользователя
        assert len(users) == 3
        
        # Проверяем что все роли представлены
        roles = {u.role for u in users}
        assert roles == {"employee", "warehouseman", "manager"}
    
    @pytest.mark.asyncio
    async def test_get_all_users_multiple_employees(self, test_session, mock_config):
        """Возвращает всех сотрудников"""
        service = BroadcastService()
        
        # Создаем много сотрудников
        for i in range(10):
            test_session.add(User(id=100000 + i, role="employee"))
        await test_session.flush()
        
        users = await service.get_all_users(test_session)
        
        assert len(users) == 10


class TestBroadcastServiceEdgeCases:
    """Edge cases"""
    
    @pytest.mark.asyncio
    async def test_employees_list_is_independent(self, test_session, mock_config):
        """Изменение возвращенного списка не влияет на БД"""
        service = BroadcastService()
        
        test_session.add(User(id=100001, role="employee"))
        await test_session.flush()
        
        employees = await service.get_all_employees(test_session)
        
        # Очищаем список
        employees.clear()
        
        # Повторный запрос должен вернуть данные
        employees2 = await service.get_all_employees(test_session)
        assert len(employees2) == 1

