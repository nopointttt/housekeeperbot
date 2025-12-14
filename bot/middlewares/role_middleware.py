"""Middleware для проверки ролей пользователей"""
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TelegramUser, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.engine import async_session_maker
from bot.services.role_service import role_service
from bot.database.models import AllowedUser
from bot.config import get_config

logger = logging.getLogger(__name__)


class RoleMiddleware(BaseMiddleware):
    """Middleware для добавления информации о роли пользователя"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """
        Обработка события с добавлением информации о роли пользователя
        
        Добавляет в data:
        - user_role: роль пользователя (str)
        - user_id: Telegram ID пользователя (int)
        - db_session: сессия БД (AsyncSession)
        """
        # Получаем пользователя из события
        telegram_user: TelegramUser | None = data.get("event_from_user")
        
        if telegram_user is None:
            # Если пользователя нет, пропускаем
            return await handler(event, data)
        
        user_id = telegram_user.id
        config = get_config()
        
        # Создаем сессию БД (не закрываем автоматически, handler сам закроет)
        session = async_session_maker()
        
        try:
            # Проверяем доступ через конфиг (приоритетный источник)
            if not config.is_allowed_user(user_id):
                # Пользователя нет в конфиге - проверяем БД как fallback
                result = await session.execute(
                    select(AllowedUser).where(AllowedUser.id == user_id)
                )
                allowed_user = result.scalar_one_or_none()
                
                if not allowed_user:
                    # Пользователя нет ни в конфиге, ни в БД - блокируем доступ
                    await session.close()
                    
                    # Пытаемся отправить сообщение об отказе в доступе
                    try:
                        bot = data.get("bot")
                        if bot is None and isinstance(event, (Message, CallbackQuery)):
                            bot = event.bot
                        
                        if bot:
                            error_message = "❌ У вас нет доступа к этому боту"
                            if isinstance(event, Message):
                                await event.answer(error_message)
                            elif isinstance(event, CallbackQuery):
                                await event.message.answer(error_message)
                                await event.answer(error_message, show_alert=True)
                    except Exception as e:
                        logger.warning(f"Не удалось отправить сообщение об отказе в доступе: {e}")
                    
                    # Прерываем выполнение - не вызываем handler
                    return
            
            # Получаем или создаем пользователя в БД
            user = await role_service.get_or_create_user(session, user_id, telegram_user.username)
            
            # Добавляем информацию в data для использования в handlers
            data["user_role"] = user.role
            data["user_id"] = user_id
            data["db_session"] = session
            data["telegram_user"] = telegram_user
            
            # Вызываем следующий handler
            result = await handler(event, data)
            
            # Коммитим изменения если они были
            try:
                await session.commit()
                logger.debug(f"Middleware: изменения закоммичены для user_id={user_id}")
            except Exception as commit_error:
                logger.error(f"Middleware: ошибка при commit: {commit_error}")
                await session.rollback()
                raise
            
            return result
        except Exception as e:
            # Откатываем в случае ошибки
            logger.error(f"Middleware: ошибка в handler, rollback: {e}")
            await session.rollback()
            raise
        finally:
            # Закрываем сессию после обработки
            await session.close()

