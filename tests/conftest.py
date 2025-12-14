"""
Общие fixtures для всех тестов

Этот файл автоматически загружается pytest.
Все fixtures доступны во всех тестах.
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import patch, MagicMock
from dataclasses import dataclass

# Добавляем корневую директорию в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ===== Тестовая конфигурация =====

@dataclass
class TestConfig:
    """Тестовая конфигурация (заменяет реальную)"""
    bot_token: str = "test_token:ABC123"
    database_url: str = "sqlite+aiosqlite:///:memory:"
    warehouseman_id: int = 999001
    manager_id: int = 999002
    timezone: str = "Europe/Moscow"
    log_level: str = "DEBUG"
    
    def get_role_by_id(self, user_id: int) -> str:
        if user_id == self.warehouseman_id:
            return "warehouseman"
        elif user_id == self.manager_id:
            return "manager"
        else:
            return "employee"


# Создаем тестовую конфигурацию
_test_config = TestConfig()


# Патчим конфигурацию ДО импорта модулей бота
@pytest.fixture(scope="session", autouse=True)
def patch_config():
    """Патч конфигурации на всю сессию тестирования"""
    with patch.dict(os.environ, {
        'BOT_TOKEN': 'test_token:ABC123',
        'DATABASE_URL': 'sqlite+aiosqlite:///:memory:',
        'WAREHOUSEMAN_ID': '999001',
        'MANAGER_ID': '999002',
        'TIMEZONE': 'Europe/Moscow',
        'LOG_LEVEL': 'DEBUG',
    }):
        # Патчим get_config и config
        with patch('bot.config._config_instance', _test_config):
            with patch('bot.config.get_config', return_value=_test_config):
                yield _test_config


# ===== Импорт fixtures из модулей =====

# Fixtures для БД
from tests.fixtures.database import (
    event_loop,
    test_engine,
    test_session_maker,
    test_session,
    test_session_with_commit,
)

# Fixtures для моков Telegram Bot
from tests.fixtures.bot import (
    mock_bot,
    mock_dispatcher,
    mock_telegram_user,
    mock_telegram_employee,
    mock_telegram_warehouseman,
    mock_telegram_manager,
    mock_chat,
    mock_message,
    mock_callback_query,
    mock_fsm_context,
    mock_config,
)

# Fixtures для тестовых данных
from tests.fixtures.data import (
    test_user_data,
    test_employee_data,
    test_warehouseman_data,
    test_manager_data,
    test_user,
    test_warehouseman,
    test_manager,
    test_request_data,
    test_request,
    test_request_with_photos,
    test_warehouse_item_data,
    test_warehouse_item,
    test_warehouse_items,
    test_low_stock_items,
    test_complaint_data,
    test_complaint,
)


# ===== Дополнительные общие fixtures =====

@pytest.fixture
def anyio_backend():
    """Backend для asyncio"""
    return 'asyncio'


@pytest.fixture
async def clean_database(test_session):
    """
    Fixture для очистки БД перед тестом
    
    Использовать когда нужна чистая БД
    """
    from bot.database.models import User, Request, RequestPhoto, WarehouseItem, Complaint
    
    # Удаляем все данные
    await test_session.execute(RequestPhoto.__table__.delete())
    await test_session.execute(Complaint.__table__.delete())
    await test_session.execute(Request.__table__.delete())
    await test_session.execute(WarehouseItem.__table__.delete())
    await test_session.execute(User.__table__.delete())
    await test_session.flush()
    
    yield test_session


# ===== Хелперы для тестов =====

def assert_message_contains(message_mock, expected_text: str):
    """Проверить, что сообщение содержит ожидаемый текст"""
    calls = message_mock.call_args_list
    for call in calls:
        text = call.kwargs.get('text', '') or (call.args[0] if call.args else '')
        if expected_text in text:
            return True
    raise AssertionError(f"Текст '{expected_text}' не найден в сообщениях: {calls}")

