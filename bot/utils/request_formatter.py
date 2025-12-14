"""Утилиты для форматирования заявок для отображения"""
from bot.database.models import Request
from typing import Optional


def format_request_short(request: Request, user_full_name: Optional[str] = None, user_username: Optional[str] = None, user_phone: Optional[str] = None) -> str:
    """
    Краткое форматирование заявки для списка
    
    Args:
        request: Объект заявки
        user_full_name: ФИО создателя заявки (опционально)
        user_username: Username создателя заявки (опционально)
        user_phone: Номер телефона создателя заявки (опционально)
        
    Returns:
        Отформатированная строка
    """
    status_emoji = {
        "new": "🆕",
        "in_progress": "🔄",
        "completed": "✅",
        "rejected": "❌"
    }
    
    status_text = {
        "new": "Новая",
        "in_progress": "В работе",
        "completed": "Выполнено",
        "rejected": "Отклонено"
    }
    
    emoji = status_emoji.get(request.status, "📋")
    status = status_text.get(request.status, request.status)
    
    text = f"{emoji} <b>{request.number}</b> - {status}\n"
    text += f"📂 {request.category}\n"
    
    # Обрезаем описание если слишком длинное
    description = request.description
    if len(description) > 50:
        description = description[:47] + "..."
    
    text += f"📝 {description}\n"
    
    # Добавляем информацию о создателе, если предоставлена
    if user_full_name or user_username or user_phone:
        user_info = user_full_name or f"ID: {request.user_id}"
        # Формируем дополнительную информацию
        extra_info = []
        if user_username and not user_username.startswith("ID:"):
            extra_info.append(user_username)
        if user_phone:
            extra_info.append(f"📞 {user_phone}")
        
        if extra_info:
            text += f"👤 {user_info} ({', '.join(extra_info)})\n"
        else:
            text += f"👤 {user_info}\n"
    
    text += f"📅 {request.created_at.strftime('%d.%m.%Y %H:%M')}"
    
    return text


def format_request_full(request: Request, include_photos: bool = True, user_full_name: Optional[str] = None, user_username: Optional[str] = None, user_phone: Optional[str] = None) -> str:
    """
    Полное форматирование заявки с деталями
    
    Args:
        request: Объект заявки
        include_photos: Включать ли информацию о фото
        user_full_name: ФИО создателя заявки (опционально)
        user_username: Username создателя заявки (опционально)
        user_phone: Номер телефона создателя заявки (опционально)
        
    Returns:
        Отформатированная строка
    """
    status_emoji = {
        "new": "🆕",
        "in_progress": "🔄",
        "completed": "✅",
        "rejected": "❌"
    }
    
    status_text = {
        "new": "Новая",
        "in_progress": "В работе",
        "completed": "Выполнено",
        "rejected": "Отклонено"
    }
    
    priority_emoji = "🚨" if request.priority == "urgent" else "⏰"
    priority_text = "Срочно" if request.priority == "urgent" else "Обычная"
    
    emoji = status_emoji.get(request.status, "📋")
    status = status_text.get(request.status, request.status)
    
    text = f"📋 <b>Заявка {request.number}</b>\n\n"
    
    # Добавляем информацию о создателе в начале
    if user_full_name or user_username or user_phone:
        user_info = user_full_name or f"ID: {request.user_id}"
        # Формируем дополнительную информацию
        extra_info = []
        if user_username and not user_username.startswith("ID:"):
            extra_info.append(user_username)
        if user_phone:
            extra_info.append(f"📞 {user_phone}")
        
        if extra_info:
            text += f"👤 <b>Создатель:</b> {user_info} ({', '.join(extra_info)})\n\n"
        else:
            text += f"👤 <b>Создатель:</b> {user_info}\n\n"
    
    text += f"{emoji} <b>Статус:</b> {status}\n"
    text += f"📂 <b>Категория:</b> {request.category}\n"
    text += f"📝 <b>Описание:</b> {request.description}\n"
    
    if request.quantity:
        text += f"🔢 <b>Количество:</b> {request.quantity} шт.\n"
    
    text += f"{priority_emoji} <b>Приоритет:</b> {priority_text}\n"
    text += f"📅 <b>Создана:</b> {request.created_at.strftime('%d.%m.%Y %H:%M')}\n"
    
    if request.updated_at != request.created_at:
        text += f"🔄 <b>Обновлена:</b> {request.updated_at.strftime('%d.%m.%Y %H:%M')}\n"
    
    if request.completed_at:
        text += f"✅ <b>Завершена:</b> {request.completed_at.strftime('%d.%m.%Y %H:%M')}\n"
    
    if request.rejection_reason:
        text += f"❌ <b>Причина отклонения:</b> {request.rejection_reason}\n"
    
    # Безопасная проверка наличия photos без lazy loading
    # Проблема: обращение к request.photos вызывает lazy loading, что приводит к ошибке greenlet
    # Решение: проверяем через inspect, загружены ли photos, перед обращением к ним
    if include_photos:
        try:
            from sqlalchemy import inspect
            insp = inspect(request)
            
            # Проверяем, загружены ли photos
            if 'photos' in insp.attrs:
                photos_attr = insp.attrs['photos']
                # Если photos загружены (loaded_value не является lazy loader)
                # loaded_value будет None если не загружено, или список если загружено
                if photos_attr.loaded_value is not None:
                    # Photos загружены, можно безопасно использовать
                    photos = request.photos
                    if photos:
                        text += f"📷 <b>Фото:</b> {len(photos)} шт.\n"
        except Exception:
            # Если возникла ошибка при проверке или доступе к photos, просто пропускаем
            # Это безопасно - мы просто не показываем информацию о фото
            pass
    
    return text


def format_request_list(requests: list[Request], title: str = "Ваши заявки", user_info_map: Optional[dict[int, tuple[str, str, Optional[str]]]] = None) -> tuple[str, list]:
    """
    Форматирование списка заявок
    
    Args:
        requests: Список заявок
        title: Заголовок списка
        user_info_map: Словарь {user_id: (full_name, username, phone)} для отображения информации о создателях (опционально)
        
    Returns:
        Кортеж (текст, список ID заявок для кнопок)
    """
    if not requests:
        return f"📋 <b>{title}</b>\n\nЗаявок пока нет.", []
    
    text = f"📋 <b>{title}</b>\n\n"
    request_ids = []
    
    for i, request in enumerate(requests, 1):
        # Получаем информацию о пользователе если есть
        user_full_name = None
        user_username = None
        user_phone = None
        if user_info_map and request.user_id in user_info_map:
            user_info = user_info_map[request.user_id]
            if len(user_info) >= 2:
                user_full_name, user_username = user_info[0], user_info[1]
            if len(user_info) >= 3:
                user_phone = user_info[2]
        
        text += f"{i}. {format_request_short(request, user_full_name=user_full_name, user_username=user_username, user_phone=user_phone)}\n\n"
        request_ids.append(request.id)
    
    return text, request_ids

