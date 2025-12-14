"""Fixtures для моков Telegram Bot API"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.types import User, Message, Chat, CallbackQuery, Update
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage


@pytest.fixture
def mock_bot() -> MagicMock:
    """
    Мок объекта Bot из aiogram
    
    Все методы отправки сообщений замокированы
    """
    bot = MagicMock(spec=Bot)
    bot.id = 123456789
    bot.token = "test_token:ABC123"
    
    # Мокаем методы отправки
    bot.send_message = AsyncMock(return_value=MagicMock())
    bot.send_photo = AsyncMock(return_value=MagicMock())
    bot.edit_message_text = AsyncMock(return_value=MagicMock())
    bot.edit_message_reply_markup = AsyncMock(return_value=MagicMock())
    bot.answer_callback_query = AsyncMock(return_value=True)
    bot.delete_message = AsyncMock(return_value=True)
    
    return bot


@pytest.fixture
def mock_dispatcher() -> Dispatcher:
    """
    Мок Dispatcher из aiogram
    """
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    return dp


@pytest.fixture
def mock_telegram_user() -> User:
    """
    Мок пользователя Telegram
    """
    return User(
        id=12345,
        is_bot=False,
        first_name="Тестовый",
        last_name="Пользователь",
        username="test_user",
        language_code="ru"
    )


@pytest.fixture
def mock_telegram_employee() -> User:
    """Мок сотрудника (обычный пользователь)"""
    return User(
        id=100001,
        is_bot=False,
        first_name="Сотрудник",
        last_name="Иванов",
        username="employee_user",
        language_code="ru"
    )


@pytest.fixture
def mock_telegram_warehouseman() -> User:
    """Мок завхоза"""
    return User(
        id=999001,  # Должен совпадать с WAREHOUSEMAN_ID в тестовом конфиге
        is_bot=False,
        first_name="Завхоз",
        last_name="Петров",
        username="warehouseman_user",
        language_code="ru"
    )


@pytest.fixture
def mock_telegram_manager() -> User:
    """Мок руководителя"""
    return User(
        id=999002,  # Должен совпадать с MANAGER_ID в тестовом конфиге
        is_bot=False,
        first_name="Руководитель",
        last_name="Сидоров",
        username="manager_user",
        language_code="ru"
    )


@pytest.fixture
def mock_chat() -> Chat:
    """Мок чата (личные сообщения)"""
    return Chat(
        id=12345,
        type="private",
        title=None,
        username="test_user",
        first_name="Тестовый",
        last_name="Пользователь"
    )


@pytest.fixture
def mock_message(mock_telegram_user, mock_chat, mock_bot) -> Message:
    """
    Мок объекта Message
    
    Args:
        mock_telegram_user: Мок пользователя
        mock_chat: Мок чата
        mock_bot: Мок бота
    """
    message = MagicMock(spec=Message)
    message.message_id = 1
    message.date = datetime.now()
    message.chat = mock_chat
    message.from_user = mock_telegram_user
    message.text = "Тестовое сообщение"
    message.bot = mock_bot
    
    # Мокаем методы ответа
    message.answer = AsyncMock(return_value=MagicMock())
    message.reply = AsyncMock(return_value=MagicMock())
    message.edit_text = AsyncMock(return_value=MagicMock())
    message.delete = AsyncMock(return_value=True)
    
    return message


@pytest.fixture
def mock_callback_query(mock_telegram_user, mock_message, mock_bot) -> CallbackQuery:
    """
    Мок объекта CallbackQuery (нажатие на inline кнопку)
    """
    callback = MagicMock(spec=CallbackQuery)
    callback.id = "callback_123"
    callback.from_user = mock_telegram_user
    callback.message = mock_message
    callback.data = "test_callback_data"
    callback.bot = mock_bot
    
    # Мокаем методы
    callback.answer = AsyncMock(return_value=True)
    
    return callback


@pytest.fixture
def mock_fsm_context() -> FSMContext:
    """
    Мок FSM контекста для тестирования состояний
    """
    storage = MemoryStorage()
    
    # Создаем мок контекста
    context = MagicMock(spec=FSMContext)
    context.state = None
    context._data = {}
    
    async def get_state():
        return context.state
    
    async def set_state(state):
        context.state = state
    
    async def get_data():
        return context._data.copy()
    
    async def set_data(data):
        context._data = data
    
    async def update_data(**kwargs):
        context._data.update(kwargs)
        return context._data
    
    async def clear():
        context.state = None
        context._data = {}
    
    context.get_state = AsyncMock(side_effect=get_state)
    context.set_state = AsyncMock(side_effect=set_state)
    context.get_data = AsyncMock(side_effect=get_data)
    context.set_data = AsyncMock(side_effect=set_data)
    context.update_data = AsyncMock(side_effect=update_data)
    context.clear = AsyncMock(side_effect=clear)
    
    return context


@pytest.fixture
def mock_config():
    """
    Мок конфигурации бота для тестов
    
    Возвращает патч для get_config()
    """
    from dataclasses import dataclass
    
    @dataclass
    class TestConfig:
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
    
    config = TestConfig()
    
    with patch('bot.config.get_config', return_value=config):
        with patch('bot.config.config', config):
            yield config

