"""Обработчики для сотрудников"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.services.request_service import request_service
from bot.utils.request_formatter import format_request_list, format_request_full
from bot.keyboards.employee import get_employee_keyboard
from bot.keyboards.complaints import get_complaint_button_keyboard
from bot.keyboards.inline import get_cancel_keyboard
from bot.states.contact_warehouseman import ContactWarehousemanStates

router = Router(name="employee")


# ==================== МОИ ЗАЯВКИ ====================

@router.message(F.text == "Мои заявки")
async def show_my_requests(message: Message, user_id: int, db_session):
    """Показать список заявок сотрудника"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    requests = await request_service.get_user_requests(
        session=db_session,
        user_id=user_id,
        limit=10  # Последние 10 заявок
    )
    
    text, request_ids = format_request_list(requests, title="Мои заявки")
    
    # Создаем inline кнопки для просмотра деталей
    keyboard = None
    if request_ids:
        buttons = []
        # Группируем по 2 кнопки в ряд
        for i in range(0, min(len(request_ids), 10), 2):
            row = []
            request = requests[i]
            row.append(InlineKeyboardButton(
                text=f"📋 {request.number}",
                callback_data=f"view_request_{request.id}"
            ))
            
            if i + 1 < len(request_ids):
                request = requests[i + 1]
                row.append(InlineKeyboardButton(
                    text=f"📋 {request.number}",
                    callback_data=f"view_request_{request.id}"
                ))
            
            buttons.append(row)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ==================== ПРОСМОТР ДЕТАЛЕЙ ЗАЯВКИ ====================

@router.callback_query(F.data.startswith("view_request_"))
async def view_request_details(callback: CallbackQuery, user_id: int, db_session):
    """Просмотр деталей заявки"""
    request_id = int(callback.data.split("_")[-1])
    
    request = await request_service.get_request_by_id(db_session, request_id)
    
    if not request:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    
    # Проверяем, что заявка принадлежит пользователю (для сотрудников)
    if request.user_id != user_id:
        await callback.answer("У вас нет доступа к этой заявке", show_alert=True)
        return
    
    text = format_request_full(request)
    
    # Добавляем кнопку жалобы, если заявка не выполнена и не отклонена
    keyboard = None
    if request.status in ["new", "in_progress"]:
        keyboard = get_complaint_button_keyboard(request.id)
    
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
    
    await callback.answer()


# ==================== СВЯЗАТЬСЯ С ЗАВХОЗОМ ====================

@router.message(F.text == "Связаться с завхозом")
async def start_contact_warehouseman(message: Message, state: FSMContext):
    """Начало отправки сообщения завхозу"""
    from bot.states.contact_warehouseman import ContactWarehousemanStates
    
    await state.set_state(ContactWarehousemanStates.waiting_for_message)
    
    await message.answer(
        "💬 <b>Связаться с завхозом</b>\n\n"
        "Напишите ваше сообщение завхозу:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(ContactWarehousemanStates.waiting_for_message)
async def send_message_to_warehouseman(message: Message, state: FSMContext, user_id: int, telegram_user, bot):
    """Отправка сообщения завхозу"""
    from bot.states.contact_warehouseman import ContactWarehousemanStates
    from bot.config import get_config
    
    config = get_config()
    user_name = telegram_user.first_name or "Сотрудник"
    user_username = f"@{telegram_user.username}" if telegram_user.username else f"ID: {user_id}"
    
    # Формируем сообщение для завхоза
    text = f"💬 <b>Сообщение от сотрудника</b>\n\n"
    text += f"👤 <b>От:</b> {user_name} ({user_username})\n"
    text += f"💬 <b>Сообщение:</b>\n{message.text}"
    
    try:
        await bot.send_message(
            chat_id=config.warehouseman_id,
            text=text,
            parse_mode="HTML"
        )
        
        await message.answer(
            "✅ Сообщение отправлено завхозу!",
            reply_markup=get_employee_keyboard()
        )
        
        await state.clear()
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при отправке сообщения: {e}\n"
            "Попробуйте позже или обратитесь к руководителю.",
            reply_markup=get_employee_keyboard()
        )
        await state.clear()


# ==================== ОТМЕНА ОТПРАВКИ СООБЩЕНИЯ ====================

@router.callback_query(F.data == "cancel")
async def cancel_message_to_warehouseman(callback: CallbackQuery, state: FSMContext):
    """Отмена отправки сообщения завхозу"""
    from bot.keyboards.employee import get_employee_keyboard
    
    await state.clear()
    
    await callback.message.edit_text("❌ Отправка сообщения отменена.")
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_employee_keyboard()
    )
    
    await callback.answer("Отменено")

