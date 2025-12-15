"""Сервис для отправки уведомлений"""
import logging
from aiogram import Bot
from aiogram.types import Message
from bot.config import get_config
from bot.database.models import Request, Complaint

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для отправки уведомлений пользователям"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.config = get_config()
    
    async def _get_user_name(self, user_id: int) -> str:
        """
        Получить имя пользователя через Telegram API
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Имя пользователя или ID если не удалось получить
        """
        try:
            chat = await self.bot.get_chat(user_id)
            return chat.first_name or chat.username or f"ID: {user_id}"
        except Exception as e:
            logger.warning(f"Не удалось получить имя пользователя {user_id}: {e}")
            return f"ID: {user_id}"
    
    async def _get_user_full_info(self, user_id: int) -> tuple[str, str]:
        """
        Получить полное имя и username пользователя через Telegram API
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            Кортеж (full_name, username), где username может быть пустой строкой
        """
        try:
            chat = await self.bot.get_chat(user_id)
            full_name = chat.first_name or f"ID: {user_id}"
            username = f"@{chat.username}" if chat.username else f"ID: {user_id}"
            return (full_name, username)
        except Exception as e:
            logger.warning(f"Не удалось получить информацию о пользователе {user_id}: {e}")
            return (f"ID: {user_id}", f"ID: {user_id}")
    
    async def notify_warehouseman_new_request(self, request: Request):
        """
        Уведомить техника о новой заявке
        
        Args:
            request: Новая заявка
        """
        from bot.utils.request_formatter import format_request_full
        from bot.keyboards.inline import get_request_actions_keyboard
        
        # Получаем ФИО и username отправителя
        full_name, username = await self._get_user_full_info(request.user_id)
        
        text = "🆕 <b>Новая заявка!</b>\n\n"
        text += f"👤 <b>Отправитель:</b> {full_name} ({username})\n\n"
        text += format_request_full(request, include_photos=False)  # Фото отправим отдельно
        
        keyboard = get_request_actions_keyboard(request.id)
        
        # В demo режиме не шлем уведомления на "реальные" ID,
        # чтобы не было пересечений между тестировщиками.
        target_warehouseman_chat_id = request.user_id if self.config.demo_mode else self.config.warehouseman_id

        try:
            # Получаем фото безопасным способом
            # Сначала пробуем использовать закэшированные file_ids (если есть)
            photo_file_ids = getattr(request, '_cached_photo_file_ids', None)
            
            if photo_file_ids is not None:
                # Используем закэшированные file_ids
                photos = [type('Photo', (), {'file_id': fid})() for fid in photo_file_ids]
            else:
                # Пытаемся получить через relationship (может не сработать после commit)
                photos = []
                try:
                    from sqlalchemy import inspect
                    insp = inspect(request)
                    if 'photos' in insp.attrs:
                        photos_attr = insp.attrs['photos']
                        if photos_attr.loaded_value is not None:
                            # Photos загружены, можно безопасно использовать
                            photos = list(request.photos) if request.photos else []
                except Exception:
                    # Если не удалось получить - значит фото нет или сессия закрыта
                    photos = []
            
            if photos:
                # Отправляем первое фото с текстом и кнопками
                await self.bot.send_photo(
                    chat_id=target_warehouseman_chat_id,
                    photo=photos[0].file_id,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                
                # Остальные фото отправляем отдельными сообщениями
                if len(photos) > 1:
                    for photo in photos[1:]:
                        await self.bot.send_photo(
                            chat_id=target_warehouseman_chat_id,
                            photo=photo.file_id
                        )
            else:
                # Нет фото - отправляем обычное текстовое сообщение
                await self.bot.send_message(
                    chat_id=target_warehouseman_chat_id,
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            logger.error(f"Ошибка отправки уведомления технику: {e}")
    
    async def notify_manager_complaint(self, complaint: Complaint, request: Request):
        """
        Уведомить руководителя о жалобе
        
        Args:
            complaint: Жалоба
            request: Заявка, на которую пожаловались
        """
        from bot.utils.request_formatter import format_request_short
        
        # Получаем имя пользователя через Telegram API
        user_name = await self._get_user_name(complaint.user_id)
        
        text = "⚠️ <b>Жалоба на техника</b>\n\n"
        text += f"📋 <b>Заявка:</b> {request.number}\n"
        text += format_request_short(request)
        text += f"\n\n"
        text += f"👤 <b>От:</b> {user_name}\n"
        text += f"📝 <b>Причина:</b> {complaint.reason}\n"
        text += f"💬 <b>Текст жалобы:</b>\n{complaint.text}\n"
        text += f"\n📅 {complaint.created_at.strftime('%d.%m.%Y %H:%M')}"
        
        target_manager_chat_id = complaint.user_id if self.config.demo_mode else self.config.manager_id

        try:
            await self.bot.send_message(
                chat_id=target_manager_chat_id,
                text=text,
                parse_mode="HTML"
            )
            logger.debug(f"Уведомление руководителю отправлено: жалоба ID={complaint.id}")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления руководителю: {e}")
            # Не прерываем выполнение - жалоба уже создана
    
    async def notify_warehouseman_complaint(self, complaint: Complaint, request: Request):
        """
        Уведомить техника о жалобе (копия)
        
        Args:
            complaint: Жалоба
            request: Заявка, на которую пожаловались
        """
        from bot.utils.request_formatter import format_request_short
        
        # Получаем имя пользователя через Telegram API
        user_name = await self._get_user_name(complaint.user_id)
        
        text = "⚠️ <b>Жалоба на вас</b>\n\n"
        text += f"📋 <b>Заявка:</b> {request.number}\n"
        text += format_request_short(request)
        text += f"\n\n"
        text += f"👤 <b>От:</b> {user_name}\n"
        text += f"📝 <b>Причина:</b> {complaint.reason}\n"
        text += f"💬 <b>Текст жалобы:</b>\n{complaint.text}\n"
        text += f"\n📅 {complaint.created_at.strftime('%d.%m.%Y %H:%M')}"
        
        target_warehouseman_chat_id = complaint.user_id if self.config.demo_mode else self.config.warehouseman_id

        try:
            await self.bot.send_message(
                chat_id=target_warehouseman_chat_id,
                text=text,
                parse_mode="HTML"
            )
            logger.debug(f"Уведомление технику отправлено: жалоба ID={complaint.id}")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления технику о жалобе: {e}")
            # Не прерываем выполнение - жалоба уже создана
    
    async def notify_employee_request_status_changed(self, request: Request, status_text: str):
        """
        Уведомить пользователя об изменении статуса заявки
        
        Args:
            request: Заявка
            status_text: Текст статуса
        """
        from bot.utils.request_formatter import format_request_short
        
        text = f"🔄 <b>Статус заявки изменен</b>\n\n"
        text += format_request_short(request)
        text += f"\n\nНовый статус: <b>{status_text}</b>"
        
        if request.rejection_reason:
            text += f"\n\n❌ <b>Причина отклонения:</b> {request.rejection_reason}"
        
        try:
            await self.bot.send_message(
                chat_id=request.user_id,
                text=text,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Ошибка отправки уведомления пользователю: {e}")

