"""Обработчики для управления техниками (назначение техников руководителям)"""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from bot.services.technician_service import technician_service
from bot.keyboards.manager import get_manager_keyboard
from bot.keyboards.inline import get_cancel_keyboard
from bot.states.technician_management import TechnicianManagementStates

router = Router(name="technicians")


@router.message(F.text == "Управление техниками")
async def show_technician_menu(message: Message, user_role: str, tenant_id: int, db_session, bot: Bot):
    """Показать меню управления техниками"""
    if user_role != "manager":
        await message.answer("❌ У вас нет доступа к этой функции.")
        return
    
    # Получаем список техников
    technicians = await technician_service.get_technicians(db_session, manager_id=tenant_id, bot=bot)
    
    if not technicians:
        text = (
            "👷 <b>Управление техниками</b>\n\n"
            "У вас пока нет назначенных техников.\n\n"
            "Вы можете добавить техника, отправив его Telegram ID или username."
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить техника", callback_data="technician_add")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="technician_cancel")]
        ])
    else:
        text = "👷 <b>Управление техниками</b>\n\n"
        text += "<b>Назначенные техники:</b>\n\n"
        for tech_id, tech_name in technicians:
            text += f"• {tech_name} (ID: {tech_id})\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить техника", callback_data="technician_add")],
            [InlineKeyboardButton(text="➖ Удалить техника", callback_data="technician_remove")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="technician_cancel")]
        ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "technician_add")
async def start_add_technician(callback: CallbackQuery, state: FSMContext):
    """Начало добавления техника"""
    await state.set_state(TechnicianManagementStates.waiting_for_technician_id)
    
    text = (
        "➕ <b>Добавить техника</b>\n\n"
        "Отправьте:\n"
        "• <b>Telegram ID</b> техника (например: 123456789)\n"
        "• Или <b>username</b> без @ (например: username)\n\n"
        "⚠️ <b>Важно:</b> Если используете username, убедитесь что пользователь уже писал боту @housekeeperrrrrbot\n\n"
        "📋 <b>Как узнать ID:</b>\n"
        "• Через @userinfobot\n"
        "• Через @RawDataBot\n"
        "• Или попросите пользователя написать боту /start, затем используйте username"
    )
    
    await callback.message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.message(TechnicianManagementStates.waiting_for_technician_id)
async def process_add_technician(message: Message, state: FSMContext, user_role: str, tenant_id: int, db_session, bot: Bot):
    """Обработка добавления техника"""
    if user_role != "manager":
        await message.answer("❌ У вас нет доступа к этой функции.")
        await state.clear()
        return
    
    input_text = message.text.strip()
    technician_id: int | None = None
    
    # Пытаемся определить, это ID или username
    try:
        # Если это число - это ID
        technician_id = int(input_text)
    except ValueError:
        # Если это username - пытаемся получить ID через бота
        username = input_text.lstrip("@")
        try:
            # Пробуем получить информацию о пользователе
            # Важно: get_chat работает только если пользователь уже взаимодействовал с ботом
            chat = await bot.get_chat(f"@{username}")
            technician_id = chat.id
        except Exception as e:
            # Если не удалось - даем понятное объяснение
            error_msg = (
                f"❌ Не удалось найти пользователя @{username}\n\n"
                "Это может произойти, если:\n"
                "• Пользователь еще не писал боту (@housekeeperrrrrbot)\n"
                "• Username указан неверно\n\n"
                "💡 <b>Решение:</b>\n"
                "1. Попросите пользователя написать боту /start\n"
                "2. Или используйте Telegram ID пользователя\n"
                "   (можно узнать через @userinfobot или @RawDataBot)"
            )
            await message.answer(error_msg, parse_mode="HTML")
            return
    
    # Добавляем техника
    success, msg = await technician_service.add_technician(
        db_session,
        manager_id=tenant_id,
        technician_id=technician_id,
        bot=bot
    )
    
    if success:
        await message.answer(
            f"✅ {msg}\n\n"
            "Техник теперь может работать с вашими заявками и складом.",
            reply_markup=get_manager_keyboard()
        )
    else:
        await message.answer(f"❌ {msg}")
    
    await state.clear()


@router.callback_query(F.data == "technician_remove")
async def start_remove_technician(callback: CallbackQuery, state: FSMContext, tenant_id: int, db_session, bot: Bot):
    """Начало удаления техника"""
    # Получаем список техников
    technicians = await technician_service.get_technicians(db_session, manager_id=tenant_id, bot=bot)
    
    if not technicians:
        await callback.answer("Нет техников для удаления", show_alert=True)
        return
    
    # Создаем inline кнопки для выбора техника
    buttons = []
    for tech_id, tech_name in technicians:
        buttons.append([
            InlineKeyboardButton(
                text=f"➖ {tech_name}",
                callback_data=f"technician_remove_{tech_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="technician_cancel")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(
        "➖ <b>Удалить техника</b>\n\n"
        "Выберите техника, которого хотите удалить:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("technician_remove_"))
async def process_remove_technician(callback: CallbackQuery, user_role: str, tenant_id: int, db_session, bot: Bot):
    """Обработка удаления техника"""
    if user_role != "manager":
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    technician_id = int(callback.data.split("_")[-1])
    
    success, msg = await technician_service.remove_technician(
        db_session,
        manager_id=tenant_id,
        technician_id=technician_id,
        bot=bot
    )
    
    if success:
        await callback.message.edit_text(
            f"✅ {msg}\n\n"
            "Техник больше не имеет доступа к вашим заявкам и складу.",
            parse_mode="HTML"
        )
    else:
        await callback.answer(f"❌ {msg}", show_alert=True)


@router.callback_query(F.data == "technician_cancel")
async def cancel_technician_management(callback: CallbackQuery, state: FSMContext):
    """Отмена управления техниками"""
    await state.clear()
    await callback.message.edit_text("❌ Управление техниками отменено")
    await callback.answer()


@router.callback_query(F.data == "cancel", TechnicianManagementStates.waiting_for_technician_id)
async def cancel_technician_operation(callback: CallbackQuery, state: FSMContext):
    """Отмена операции с техником (из FSM состояния)"""
    await state.clear()
    await callback.message.edit_text("❌ Операция отменена")
    await callback.answer()

