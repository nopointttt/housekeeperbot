"""Обработчики для руководителя"""
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from bot.services.manager_service import manager_service
from bot.services.request_service import request_service
from bot.services.complaint_service import complaint_service
from bot.services.role_service import role_service
from bot.utils.request_formatter import format_request_list, format_request_full
from bot.keyboards.manager import get_manager_keyboard
from bot.keyboards.inline import get_request_details_keyboard
from bot.states.manager_period import PeriodReportStates

router = Router(name="manager")


async def get_users_info_map(bot, user_ids: set[int]) -> dict[int, tuple[str, str, Optional[str]]]:
    """
    Получить информацию о пользователях через Telegram API
    
    Args:
        bot: Экземпляр бота
        user_ids: Множество user_id для получения информации
        
    Returns:
        Словарь {user_id: (full_name, username, phone)}
    """
    user_info_map = {}
    for user_id in user_ids:
        try:
            chat = await bot.get_chat(user_id)
            # Формируем полное имя (first_name + last_name если есть)
            full_name_parts = []
            if chat.first_name:
                full_name_parts.append(chat.first_name)
            if chat.last_name:
                full_name_parts.append(chat.last_name)
            full_name = " ".join(full_name_parts) if full_name_parts else f"ID: {user_id}"
            username = f"@{chat.username}" if chat.username else f"ID: {user_id}"
            # Пытаемся получить номер телефона (доступен не всегда)
            phone = None
            if hasattr(chat, 'phone_number') and chat.phone_number:
                phone = chat.phone_number
            user_info_map[user_id] = (full_name, username, phone)
        except Exception:
            # Если не удалось получить - используем ID
            user_info_map[user_id] = (f"ID: {user_id}", f"ID: {user_id}", None)
    return user_info_map


@router.message(F.text == "Все заявки")
async def show_all_requests(message: Message, user_role: str, tenant_id: int, db_session, bot):
    """Показать все заявки с кнопками для просмотра деталей"""
    if user_role != "manager":
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    requests = await manager_service.get_all_requests(db_session, tenant_id=tenant_id, limit=20)  # Последние 20 заявок
    
    if not requests:
        await message.answer("📋 Заявок пока нет.", parse_mode="HTML")
        return
    
    # Получаем информацию о пользователях для отображения
    user_ids = {request.user_id for request in requests}
    user_info_map = await get_users_info_map(bot, user_ids)
    
    text, request_ids = format_request_list(requests, title="Все заявки", user_info_map=user_info_map)
    
    # Создаем inline кнопки для просмотра деталей
    keyboard = None
    if request_ids:
        buttons = []
        # Группируем по 2 кнопки в ряд
        for i in range(0, min(len(request_ids), 20), 2):
            row = []
            request = requests[i]
            row.append(InlineKeyboardButton(
                text=f"📋 {request.number}",
                callback_data=f"manager_view_{request.id}"
            ))
            
            if i + 1 < len(request_ids):
                request = requests[i + 1]
                row.append(InlineKeyboardButton(
                    text=f"📋 {request.number}",
                    callback_data=f"manager_view_{request.id}"
                ))
            
            buttons.append(row)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("manager_view_"))
async def manager_view_request_details(callback: CallbackQuery, tenant_id: int, db_session, bot):
    """Просмотр деталей заявки руководителем"""
    await callback.answer()
    
    request_id = int(callback.data.split("_")[-1])
    
    request = await request_service.get_request_by_id(db_session, tenant_id=tenant_id, request_id=request_id, load_user=True, load_photos=True)
    
    if not request:
        await callback.message.answer("❌ Заявка не найдена.")
        return
    
    # Получаем ФИО, username и номер телефона отправителя через Telegram API
    try:
        chat = await bot.get_chat(request.user_id)
        # Формируем полное имя (first_name + last_name если есть)
        full_name_parts = []
        if chat.first_name:
            full_name_parts.append(chat.first_name)
        if chat.last_name:
            full_name_parts.append(chat.last_name)
        full_name = " ".join(full_name_parts) if full_name_parts else f"ID: {request.user_id}"
        username = f"@{chat.username}" if chat.username else f"ID: {request.user_id}"
        # Пытаемся получить номер телефона (доступен не всегда)
        phone = None
        if hasattr(chat, 'phone_number') and chat.phone_number:
            phone = chat.phone_number
    except Exception as e:
        full_name = f"ID: {request.user_id}"
        username = f"ID: {request.user_id}"
        phone = None
    
    text = format_request_full(request, user_full_name=full_name, user_username=username, user_phone=phone)
    
    # Отправляем фото если есть
    if request.photos:
        # Отправляем первое фото с текстом
        await callback.message.answer_photo(
            photo=request.photos[0].file_id,
            caption=text,
            parse_mode="HTML"
        )
        
        # Отправляем остальные фото
        for photo in request.photos[1:]:
            await callback.message.answer_photo(photo=photo.file_id)
    else:
        await callback.message.answer(
            text,
            parse_mode="HTML"
        )


@router.message(F.text == "Заявки за сегодня")
async def show_requests_today(message: Message, user_role: str, tenant_id: int, db_session, bot):
    """Показать заявки за сегодня"""
    if user_role != "manager":
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    requests = await manager_service.get_requests_today(db_session, tenant_id=tenant_id)
    
    if not requests:
        await message.answer(
            "📋 <b>Заявки за сегодня</b>\n\n"
            "За сегодня заявок нет.",
            parse_mode="HTML"
        )
        return
    
    # Получаем информацию о пользователях для отображения
    user_ids = {request.user_id for request in requests}
    user_info_map = await get_users_info_map(bot, user_ids)
    
    text, request_ids = format_request_list(requests, title="Заявки за сегодня", user_info_map=user_info_map)
    
    # Создаем inline кнопки для просмотра деталей
    keyboard = None
    if request_ids:
        buttons = []
        for i in range(0, min(len(request_ids), 20), 2):
            row = []
            request = requests[i]
            row.append(InlineKeyboardButton(
                text=f"📋 {request.number}",
                callback_data=f"manager_view_{request.id}"
            ))
            
            if i + 1 < len(request_ids):
                request = requests[i + 1]
                row.append(InlineKeyboardButton(
                    text=f"📋 {request.number}",
                    callback_data=f"manager_view_{request.id}"
                ))
            
            buttons.append(row)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.message(F.text == "Заявки за неделю")
async def show_requests_week(message: Message, user_role: str, tenant_id: int, db_session, bot):
    """Показать заявки за неделю"""
    if user_role != "manager":
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    requests = await manager_service.get_requests_week(db_session, tenant_id=tenant_id)
    
    if not requests:
        await message.answer(
            "📋 <b>Заявки за неделю</b>\n\n"
            "За неделю заявок нет.",
            parse_mode="HTML"
        )
        return
    
    # Получаем информацию о пользователях для отображения
    user_ids = {request.user_id for request in requests}
    user_info_map = await get_users_info_map(bot, user_ids)
    
    text, request_ids = format_request_list(requests, title="Заявки за неделю", user_info_map=user_info_map)
    
    # Создаем inline кнопки для просмотра деталей
    keyboard = None
    if request_ids:
        buttons = []
        for i in range(0, min(len(request_ids), 20), 2):
            row = []
            request = requests[i]
            row.append(InlineKeyboardButton(
                text=f"📋 {request.number}",
                callback_data=f"manager_view_{request.id}"
            ))
            
            if i + 1 < len(request_ids):
                request = requests[i + 1]
                row.append(InlineKeyboardButton(
                    text=f"📋 {request.number}",
                    callback_data=f"manager_view_{request.id}"
                ))
            
            buttons.append(row)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.message(F.text == "В работе > 3 дней")
async def show_requests_over_3_days(message: Message, user_role: str, tenant_id: int, db_session, bot):
    """Показать заявки в работе более 3 дней"""
    if user_role != "manager":
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    requests = await manager_service.get_requests_in_work_over_days(db_session, tenant_id=tenant_id, days=3)
    
    if not requests:
        await message.answer(
            "⏰ <b>Заявки в работе > 3 дней</b>\n\n"
            "Нет заявок в работе более 3 дней.",
            parse_mode="HTML"
        )
        return
    
    if len(requests) > 0:
        # Получаем информацию о пользователях для отображения
        user_ids = {request.user_id for request in requests}
        user_info_map = await get_users_info_map(bot, user_ids)
        
        text, request_ids = format_request_list(requests, title=f"Заявки в работе более 3 дней (найдено: {len(requests)})", user_info_map=user_info_map)
        
        # Создаем inline кнопки для просмотра деталей
        keyboard = None
        if request_ids:
            buttons = []
            for i in range(0, min(len(request_ids), 20), 2):
                row = []
                request = requests[i]
                row.append(InlineKeyboardButton(
                    text=f"📋 {request.number}",
                    callback_data=f"manager_view_{request.id}"
                ))
                
                if i + 1 < len(request_ids):
                    request = requests[i + 1]
                    row.append(InlineKeyboardButton(
                        text=f"📋 {request.number}",
                        callback_data=f"manager_view_{request.id}"
                    ))
                
                buttons.append(row)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    else:
        text = "⏰ <b>Заявки в работе более 3 дней</b>\n\nНайдено: 0 заявок"
        keyboard = None
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.message(F.text == "В работе > 7 дней")
async def show_requests_over_7_days(message: Message, user_role: str, tenant_id: int, db_session, bot):
    """Показать заявки в работе более 7 дней"""
    if user_role != "manager":
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    requests = await manager_service.get_requests_in_work_over_days(db_session, tenant_id=tenant_id, days=7)
    
    if not requests:
        await message.answer(
            "⏰ <b>Заявки в работе > 7 дней</b>\n\n"
            "Нет заявок в работе более 7 дней.",
            parse_mode="HTML"
        )
        return
    
    if len(requests) > 0:
        # Получаем информацию о пользователях для отображения
        user_ids = {request.user_id for request in requests}
        user_info_map = await get_users_info_map(bot, user_ids)
        
        text, request_ids = format_request_list(requests, title=f"Заявки в работе более 7 дней (найдено: {len(requests)})", user_info_map=user_info_map)
        
        # Создаем inline кнопки для просмотра деталей
        keyboard = None
        if request_ids:
            buttons = []
            for i in range(0, min(len(request_ids), 20), 2):
                row = []
                request = requests[i]
                row.append(InlineKeyboardButton(
                    text=f"📋 {request.number}",
                    callback_data=f"manager_view_{request.id}"
                ))
                
                if i + 1 < len(request_ids):
                    request = requests[i + 1]
                    row.append(InlineKeyboardButton(
                        text=f"📋 {request.number}",
                        callback_data=f"manager_view_{request.id}"
                    ))
                
                buttons.append(row)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    else:
        text = "⏰ <b>Заявки в работе более 7 дней</b>\n\nНайдено: 0 заявок"
        keyboard = None
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.message(F.text == "Отчёт за период")
async def start_period_report(message: Message, user_role: str, state: FSMContext):
    """Начало создания отчета за период"""
    if user_role != "manager":
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    await state.set_state(PeriodReportStates.waiting_for_start_date)
    
    await message.answer(
        "📊 <b>Отчет за период</b>\n\n"
        "Введите начальную дату в формате ДД.ММ.ГГГГ\n"
        "Например: 01.12.2024\n\n"
        "Или отправьте 'сегодня', 'вчера', 'неделя' для быстрого выбора.",
        parse_mode="HTML"
    )


@router.message(PeriodReportStates.waiting_for_start_date)
async def process_start_date(message: Message, state: FSMContext):
    """Обработка начальной даты"""
    text = message.text.strip().lower()
    
    # Быстрый выбор
    if text == "сегодня":
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif text == "вчера":
        start_date = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    elif text == "неделя":
        start_date = datetime.now() - timedelta(days=7)
    else:
        # Парсинг даты ДД.ММ.ГГГГ
        try:
            start_date = datetime.strptime(text, "%d.%m.%Y")
        except ValueError:
            await message.answer(
                "❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ (например: 01.12.2024)\n"
                "Или отправьте 'сегодня', 'вчера', 'неделя'."
            )
            return
    
    await state.update_data(start_date=start_date)
    await state.set_state(PeriodReportStates.waiting_for_end_date)
    
    await message.answer(
        "Теперь введите конечную дату в формате ДД.ММ.ГГГГ\n"
        "Например: 31.12.2024\n\n"
        "Или отправьте 'сегодня' для текущей даты.",
        parse_mode="HTML"
    )


@router.message(PeriodReportStates.waiting_for_end_date)
async def process_end_date(message: Message, state: FSMContext, tenant_id: int, db_session):
    """Обработка конечной даты и генерация отчета"""
    text = message.text.strip().lower()
    
    # Быстрый выбор
    if text == "сегодня":
        end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        # Парсинг даты ДД.ММ.ГГГГ
        try:
            end_date = datetime.strptime(text, "%d.%m.%Y")
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            await message.answer(
                "❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ (например: 31.12.2024)\n"
                "Или отправьте 'сегодня'."
            )
            return
    
    data = await state.get_data()
    start_date = data.get("start_date")
    
    if not start_date:
        await message.answer("❌ Ошибка: начальная дата не найдена. Начните заново.")
        await state.clear()
        return
    
    if end_date < start_date:
        await message.answer("❌ Конечная дата не может быть раньше начальной. Попробуйте снова.")
        return
    
    # Получаем отчет
    report = await manager_service.get_period_report(db_session, tenant_id=tenant_id, start_date=start_date, end_date=end_date)
    
    # Форматируем даты для отображения
    start_str = start_date.strftime("%d.%m.%Y")
    end_str = end_date.strftime("%d.%m.%Y")
    
    # Формируем текст отчета
    report_text = f"📊 <b>Отчет за период</b>\n\n"
    report_text += f"<b>Период:</b> {start_str} - {end_str}\n\n"
    report_text += f"📋 <b>Статистика:</b>\n"
    report_text += f"• Новые: {report['new']}\n"
    report_text += f"• В работе: {report['in_progress']}\n"
    report_text += f"• Выполнено: {report['completed']}\n"
    report_text += f"• Отклонено: {report['rejected']}\n"
    report_text += f"• <b>Всего:</b> {report['total']}\n"
    
    await state.clear()
    await message.answer(report_text, parse_mode="HTML")


@router.message(F.text == "Жалобы на техника")
async def show_complaints(message: Message, user_role: str, tenant_id: int, db_session):
    """Показать все жалобы на техника"""
    import logging
    logger = logging.getLogger(__name__)
    
    if user_role != "manager":
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    logger.debug(f"Руководитель запросил список жалоб, user_role={user_role}")
    complaints = await manager_service.get_all_complaints(db_session, tenant_id=tenant_id)
    logger.debug(f"Получено жалоб: {len(complaints)}")
    
    if not complaints:
        await message.answer(
            "📝 <b>Жалобы на техника</b>\n\n"
            "Жалоб нет.",
            parse_mode="HTML"
        )
        return
    
    text = f"📝 <b>Жалобы на техника</b>\n\n"
    text += f"Всего жалоб: {len(complaints)}\n\n"
    
    for complaint in complaints:
        user_name = complaint.user.id  # Telegram ID, так как имени нет в модели
        created_at = complaint.created_at.strftime("%d.%m.%Y %H:%M")
        
        text += f"━━━━━━━━━━━━━━━━\n"
        text += f"<b>ID:</b> {complaint.id}\n"
        text += f"<b>От:</b> {user_name}\n"
        text += f"<b>Причина:</b> {complaint.reason}\n"
        text += f"<b>Дата:</b> {created_at}\n"
        text += f"<b>Текст:</b> {complaint.text}\n"
        text += f"<b>Заявка:</b> {complaint.request_id}\n\n"
    
    # Разбиваем на части, если сообщение слишком длинное
    if len(text) > 4000:
        # Отправляем первую часть
        await message.answer(text[:4000], parse_mode="HTML")
        # Отправляем остальные части
        remaining = text[4000:]
        while len(remaining) > 4000:
            await message.answer(remaining[:4000], parse_mode="HTML")
            remaining = remaining[4000:]
        if remaining:
            await message.answer(remaining, parse_mode="HTML")
    else:
        await message.answer(text, parse_mode="HTML")


@router.message(F.text == "Зайти как пользователь")
async def switch_to_employee_role(message: Message, base_role: str, user_id: int, db_session, telegram_user):
    """Переключиться на роль пользователя"""
    if base_role != "manager":
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    # Переключаем роль
    success = await role_service.switch_role(db_session, user_id, "employee")
    
    if success:
        # Получаем клавиатуру пользователя (передаем is_manager=True для показа кнопки "Зайти как руководитель")
        from bot.keyboards.employee import get_employee_keyboard
        
        await message.answer(
            "✅ Вы переключились на роль <b>Пользователь</b>.\n\n"
            "Теперь вы можете:\n"
            "• Создавать заявки\n"
            "• Просматривать свои заявки\n"
            "• Связаться с техником\n\n"
            "Используйте кнопку 'Зайти как руководитель', чтобы вернуться обратно.",
            reply_markup=get_employee_keyboard(is_manager=True),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Ошибка при переключении роли.")


@router.message(F.text == "Зайти как техник")
async def switch_to_warehouseman_role(message: Message, base_role: str, user_id: int, db_session, telegram_user):
    """Переключиться на роль техника"""
    if base_role != "manager":
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    # Переключаем роль
    success = await role_service.switch_role(db_session, user_id, "warehouseman")
    
    if success:
        # Получаем клавиатуру техника (передаем is_manager=True для показа кнопки "Зайти как руководитель")
        from bot.keyboards.warehouseman import get_warehouseman_keyboard
        
        await message.answer(
            "✅ Вы переключились на роль <b>Техник</b>.\n\n"
            "Теперь вы можете:\n"
            "• Управлять заявками\n"
            "• Работать со складом\n"
            "• Делать рассылки пользователям\n\n"
            "Используйте кнопку 'Зайти как руководитель', чтобы вернуться обратно.",
            reply_markup=get_warehouseman_keyboard(is_manager=True),
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Ошибка при переключении роли.")
