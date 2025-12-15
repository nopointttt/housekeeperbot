"""Обработчики для техника"""
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.services.warehouseman_service import warehouseman_service
from bot.services.request_service import request_service
from bot.services.notification_service import NotificationService
from bot.utils.request_formatter import format_request_full, format_request_list
from bot.keyboards.warehouseman import get_warehouseman_keyboard
from bot.keyboards.inline import get_request_actions_keyboard, get_cancel_keyboard
from bot.states.warehouseman_actions import WarehousemanActionStates

router = Router(name="warehouseman")


# ==================== ВСЕ ЗАЯВКИ ====================

async def get_users_info_map(bot, user_ids: set[int]) -> dict[int, tuple[str, str, Optional[str]]]:
    """
    Получить информацию о пользователях через Telegram API
    
    Args:
        bot: Экземпляр бота
        user_ids: Множество user_id для получения информации
        
    Returns:
        Словарь {user_id: (full_name, username, phone)}
    """
    from typing import Optional
    
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
async def show_all_requests(message: Message, tenant_id: int, db_session, bot):
    """Показать все заявки с кнопками для просмотра деталей"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    requests = await warehouseman_service.get_all_requests(db_session, tenant_id=tenant_id, limit=20)  # Последние 20 заявок
    
    if not requests:
        await message.answer("📋 Заявок пока нет.")
        return
    
    # Получаем информацию о пользователях для отображения
    user_ids = {request.user_id for request in requests}
    user_info_map = await get_users_info_map(bot, user_ids)
    
    text, request_ids = format_request_list(requests, title="Все заявки", user_info_map=user_info_map)
    
    # Создаем inline кнопки для просмотра деталей (как у пользователя)
    keyboard = None
    if request_ids:
        buttons = []
        # Группируем по 2 кнопки в ряд
        for i in range(0, min(len(request_ids), 20), 2):
            row = []
            request = requests[i]
            row.append(InlineKeyboardButton(
                text=f"📋 {request.number}",
                callback_data=f"warehouseman_view_{request.id}"
            ))
            
            if i + 1 < len(request_ids):
                request = requests[i + 1]
                row.append(InlineKeyboardButton(
                    text=f"📋 {request.number}",
                    callback_data=f"warehouseman_view_{request.id}"
                ))
            
            buttons.append(row)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ==================== ПРОСМОТР ДЕТАЛЕЙ ЗАЯВКИ ====================

@router.callback_query(F.data.startswith("warehouseman_view_"))
async def view_request_details(callback: CallbackQuery, tenant_id: int, db_session, bot):
    """Просмотр деталей заявки техником"""
    await callback.answer()
    
    request_id = int(callback.data.split("_")[-1])
    
    request = await request_service.get_request_by_id(db_session, tenant_id=tenant_id, request_id=request_id)
    
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
    
    # Добавляем кнопки для изменения статуса
    keyboard = get_request_actions_keyboard(request.id)
    
    # Отправляем фото если есть
    if request.photos:
        # Отправляем первое фото с текстом
        await callback.message.answer_photo(
            photo=request.photos[0].file_id,
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        # Отправляем остальные фото
        for photo in request.photos[1:]:
            await callback.message.answer_photo(photo=photo.file_id)
    else:
        await callback.message.answer(
            text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


# ==================== ЗАЯВКИ ЗА СЕГОДНЯ ====================

@router.message(F.text == "Все заявки за сегодня")
async def show_requests_today(message: Message, tenant_id: int, db_session, bot):
    """Показать все заявки за сегодня с кнопками для просмотра"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    requests = await warehouseman_service.get_requests_today(db_session, tenant_id=tenant_id)
    
    if not requests:
        await message.answer("📋 Заявок за сегодня нет.")
        return
    
    # Получаем информацию о пользователях для отображения
    user_ids = {request.user_id for request in requests}
    user_info_map = await get_users_info_map(bot, user_ids)
    
    text, request_ids = format_request_list(requests, title="Заявки за сегодня", user_info_map=user_info_map)
    
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
                callback_data=f"warehouseman_view_{request.id}"
            ))
            
            if i + 1 < len(request_ids):
                request = requests[i + 1]
                row.append(InlineKeyboardButton(
                    text=f"📋 {request.number}",
                    callback_data=f"warehouseman_view_{request.id}"
                ))
            
            buttons.append(row)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ==================== ЗАЯВКИ ЗА НЕДЕЛЮ ====================

@router.message(F.text == "Все заявки за неделю")
async def show_requests_week(message: Message, tenant_id: int, db_session, bot):
    """Показать все заявки за неделю с кнопками для просмотра"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    requests = await warehouseman_service.get_requests_week(db_session, tenant_id=tenant_id)
    
    if not requests:
        await message.answer("📋 Заявок за неделю нет.")
        return
    
    # Получаем информацию о пользователях для отображения
    user_ids = {request.user_id for request in requests}
    user_info_map = await get_users_info_map(bot, user_ids)
    
    text, request_ids = format_request_list(requests, title="Заявки за неделю", user_info_map=user_info_map)
    
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
                callback_data=f"warehouseman_view_{request.id}"
            ))
            
            if i + 1 < len(request_ids):
                request = requests[i + 1]
                row.append(InlineKeyboardButton(
                    text=f"📋 {request.number}",
                    callback_data=f"warehouseman_view_{request.id}"
                ))
            
            buttons.append(row)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ==================== ДЕЙСТВИЯ С ЗАЯВКАМИ ====================

@router.callback_query(F.data.startswith("request_take_"))
async def take_request_in_work(callback: CallbackQuery, tenant_id: int, db_session, bot):
    """Взять заявку в работу"""
    request_id = int(callback.data.split("_")[-1])
    
    request = await warehouseman_service.take_request_in_work(db_session, tenant_id=tenant_id, request_id=request_id)
    
    if not request:
        await callback.answer("❌ Не удалось взять заявку в работу", show_alert=True)
        return
    
    # Уведомляем пользователя
    from bot.services.notification_service import NotificationService
    notification_service = NotificationService(bot)
    await notification_service.notify_employee_request_status_changed(request, "В работе")
    
    # Обновляем сообщение
    request_text = format_request_full(request)
    # Получаем имя пользователя через Telegram API
    try:
        chat = await bot.get_chat(request.user_id)
        user_name = chat.first_name or chat.username or f"ID: {request.user_id}"
    except:
        user_name = f"ID: {request.user_id}"
    request_text += f"\n👤 <b>От:</b> {user_name}"
    
    keyboard = get_request_actions_keyboard(request.id)
    
    try:
        await callback.message.edit_caption(
            caption=request_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except:
        # Если это не фото, редактируем текст
        await callback.message.edit_text(
            request_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    await callback.answer("✅ Заявка взята в работу")


@router.callback_query(F.data.startswith("request_complete_"))
async def complete_request(callback: CallbackQuery, tenant_id: int, db_session, bot, state: FSMContext):
    """Завершить заявку"""
    from bot.services.warehouse_service import warehouse_service
    from bot.keyboards.warehouse import get_writeoff_item_keyboard
    from bot.states.warehouse_management import WarehouseManagementStates
    from bot.keyboards.warehouseman import get_warehouseman_keyboard
    
    request_id = int(callback.data.split("_")[-1])
    
    # Проверяем, есть ли позиции на складе для списания
    items = await warehouse_service.get_all_items(db_session, tenant_id=tenant_id)
    
    if items:
        # Предлагаем списать со склада
        await state.update_data(request_id=request_id, action="complete_with_writeoff")
        await state.set_state(WarehouseManagementStates.waiting_for_writeoff_item)
        
        keyboard = get_writeoff_item_keyboard(items)
        
        await callback.message.answer(
            "✅ <b>Заявка будет завершена</b>\n\n"
            "Хотите списать товар со склада?\n"
            "Выберите позицию (или отмените):",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()
    else:
        # Нет позиций на складе, просто завершаем заявку
        request = await warehouseman_service.complete_request(db_session, tenant_id=tenant_id, request_id=request_id)
        
        if not request:
            await callback.answer("❌ Не удалось завершить заявку", show_alert=True)
            return
        
        # Уведомляем пользователя
        notification_service = NotificationService(bot)
        await notification_service.notify_employee_request_status_changed(request, "Выполнено")
        
        # Обновляем сообщение
        request_text = format_request_full(request)
        # Получаем имя пользователя через Telegram API
        try:
            chat = await bot.get_chat(request.user_id)
            user_name = chat.first_name or chat.username or f"ID: {request.user_id}"
        except:
            user_name = f"ID: {request.user_id}"
        request_text += f"\n👤 <b>От:</b> {user_name}"
        
        # Убираем кнопки действий, так как заявка завершена
        try:
            await callback.message.edit_caption(
                caption=request_text,
                parse_mode="HTML"
            )
        except:
            await callback.message.edit_text(
                request_text,
                parse_mode="HTML"
            )
        
        # Возвращаем меню
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=get_warehouseman_keyboard(is_manager=False)
        )
        
        await callback.answer("✅ Заявка выполнена")


@router.callback_query(F.data.startswith("request_reject_"))
async def start_reject_request(callback: CallbackQuery, state: FSMContext):
    """Начало отклонения заявки"""
    from bot.states.warehouseman_actions import WarehousemanActionStates
    
    request_id = int(callback.data.split("_")[-1])
    
    # Сохраняем ID заявки в состоянии
    await state.update_data(request_id=request_id)
    await state.set_state(WarehousemanActionStates.waiting_for_rejection_reason)
    
    await callback.message.answer(
        "❌ <b>Отклонение заявки</b>\n\n"
        "Укажите причину отклонения:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    
    await callback.answer()


@router.message(WarehousemanActionStates.waiting_for_rejection_reason)
async def process_rejection_reason(message: Message, state: FSMContext, tenant_id: int, db_session, bot, base_role: str):
    """Обработка причины отклонения"""
    from bot.states.warehouseman_actions import WarehousemanActionStates
    
    reason = message.text.strip()
    
    if len(reason) < 5:
        await message.answer("❌ Причина отклонения слишком короткая. Пожалуйста, укажите подробнее (минимум 5 символов).")
        return
    
    # Получаем ID заявки из состояния
    data = await state.get_data()
    request_id = data.get("request_id")
    
    if not request_id:
        await message.answer("❌ Ошибка: данные не найдены. Начните заново.")
        await state.clear()
        return
    
    # Отклоняем заявку (tenant isolation)
    request = await warehouseman_service.reject_request(db_session, tenant_id=tenant_id, request_id=request_id, reason=reason)
    
    if not request:
        await message.answer("❌ Не удалось отклонить заявку.")
        await state.clear()
        return
    
    # Уведомляем пользователя
    notification_service = NotificationService(bot)
    await notification_service.notify_employee_request_status_changed(request, "Отклонено")
    
    await message.answer(
        f"✅ Заявка {request.number} отклонена.\n"
        f"Пользователь получил уведомление.",
        reply_markup=get_warehouseman_keyboard(is_manager=(base_role == "manager"))
    )
    
    await state.clear()


@router.callback_query(F.data.startswith("request_message_"))
async def start_message_to_employee(callback: CallbackQuery, state: FSMContext, tenant_id: int, db_session, bot):
    """Начало отправки сообщения пользователю"""
    from bot.states.warehouseman_actions import WarehousemanActionStates
    
    request_id = int(callback.data.split("_")[-1])
    
    # Получаем заявку для информации о пользователе (tenant isolation)
    request = await request_service.get_request_by_id(db_session, tenant_id=tenant_id, request_id=request_id)
    
    if not request:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    
    # Сохраняем ID заявки и ID пользователя в состоянии
    await state.update_data(request_id=request_id, employee_id=request.user_id)
    await state.set_state(WarehousemanActionStates.waiting_for_message_to_employee)
    
    # Получаем имя пользователя через Telegram API
    try:
        chat = await bot.get_chat(request.user_id)
        user_name = chat.first_name or chat.username or f"ID: {request.user_id}"
    except:
        user_name = f"ID: {request.user_id}"
    
    await callback.message.answer(
        f"💬 <b>Написать пользователю</b>\n\n"
        f"Заявка: <b>{request.number}</b>\n"
        f"Пользователь: <b>{user_name}</b>\n\n"
        "Напишите ваше сообщение:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    
    await callback.answer()


@router.message(WarehousemanActionStates.waiting_for_message_to_employee)
async def send_message_to_employee(message: Message, state: FSMContext, tenant_id: int, bot, base_role: str):
    """Отправка сообщения пользователю"""
    from bot.states.warehouseman_actions import WarehousemanActionStates
    
    # Получаем данные из состояния
    data = await state.get_data()
    request_id = data.get("request_id")
    employee_id = data.get("employee_id")
    
    if not request_id or not employee_id:
        await message.answer("❌ Ошибка: данные не найдены. Начните заново.")
        await state.clear()
        return
    
    # Получаем заявку для информации (tenant isolation)
    from bot.database.engine import async_session_maker
    async with async_session_maker() as session:
        request = await request_service.get_request_by_id(session, tenant_id=tenant_id, request_id=request_id)
        
        if not request:
            await message.answer("❌ Заявка не найдена.")
            await state.clear()
            return
        
        # Формируем сообщение для пользователя
        text = f"💬 <b>Сообщение от техника</b>\n\n"
        text += f"📋 <b>По заявке:</b> {request.number}\n"
        text += f"💬 <b>Сообщение:</b>\n{message.text}"
        
        try:
            await bot.send_message(
                chat_id=employee_id,
                text=text,
                parse_mode="HTML"
            )
            
            await message.answer(
                "✅ Сообщение отправлено пользователю!",
                reply_markup=get_warehouseman_keyboard(is_manager=(base_role == "manager"))
            )
            
            await state.clear()
        except Exception as e:
            await message.answer(
                f"❌ Ошибка при отправке сообщения: {e}",
                reply_markup=get_warehouseman_keyboard(is_manager=(base_role == "manager"))
            )
            await state.clear()


# ==================== ОТМЕНА ДЕЙСТВИЙ ====================

@router.callback_query(F.data == "cancel")
async def cancel_warehouseman_action(callback: CallbackQuery, state: FSMContext, base_role: str):
    """Отмена действия техника"""
    await state.clear()
    
    await callback.message.edit_text("❌ Действие отменено.")
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_warehouseman_keyboard(is_manager=(base_role == "manager"))
    )
    
    await callback.answer("Отменено")

