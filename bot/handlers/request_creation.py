"""Обработчики создания заявки"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states.request_creation import RequestCreationStates
from bot.utils.request_helpers import RequestCreationData
from bot.services.request_service import request_service
from bot.keyboards.categories import (
    get_categories_keyboard,
    get_priority_keyboard,
    get_photos_keyboard,
    get_confirmation_keyboard,
    get_edit_request_keyboard,
    CATEGORIES
)
from bot.keyboards.employee import get_employee_keyboard
from bot.keyboards.inline import get_cancel_keyboard

router = Router(name="request_creation")


# ==================== ШАГ 1: ВЫБОР КАТЕГОРИИ ====================

@router.message(F.text == "Новая заявка")
async def start_request_creation(message: Message, state: FSMContext):
    """Начало создания заявки"""
    # Инициализируем данные
    data = RequestCreationData()
    await state.set_data(data.to_dict())
    await state.set_state(RequestCreationStates.waiting_for_category)
    
    keyboard = get_categories_keyboard()
    await message.answer(
        "📂 <b>Шаг 1 из 6</b>\n\n"
        "Выберите категорию заявки:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("category_"), RequestCreationStates.waiting_for_category)
async def process_category(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора категории"""
    # Получаем индекс категории из callback_data
    category_index = int(callback.data.split("_")[1])
    category = CATEGORIES[category_index]
    
    # Обновляем данные
    data_dict = await state.get_data()
    data = RequestCreationData.from_dict(data_dict)
    data.category = category
    await state.set_data(data.to_dict())
    
    # Переходим к следующему шагу
    await state.set_state(RequestCreationStates.waiting_for_description)
    
    await callback.message.edit_text(
        f"✅ <b>Категория выбрана:</b> {category}\n\n"
        "📝 <b>Шаг 2 из 6</b>\n\n"
        "Опишите, что нужно или какая проблема:",
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== ШАГ 2: ВВОД ОПИСАНИЯ ====================

@router.message(RequestCreationStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """Обработка ввода описания"""
    description = message.text.strip()
    
    if len(description) < 5:
        await message.answer(
            "❌ Описание слишком короткое. Пожалуйста, укажите подробнее (минимум 5 символов)."
        )
        return
    
    # Обновляем данные
    data_dict = await state.get_data()
    data = RequestCreationData.from_dict(data_dict)
    data.description = description
    await state.set_data(data.to_dict())
    
    # Проверяем, нужен ли шаг с количеством
    if data.is_material_category():
        # Переходим к вводу количества
        await state.set_state(RequestCreationStates.waiting_for_quantity)
        await message.answer(
            "🔢 <b>Шаг 3 из 6</b>\n\n"
            "Укажите количество (только число):",
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )
    else:
        # Пропускаем количество, переходим к приоритету
        await state.set_state(RequestCreationStates.waiting_for_priority)
        keyboard = get_priority_keyboard()
        await message.answer(
            "⏰ <b>Шаг 4 из 6</b>\n\n"
            "Выберите приоритет заявки:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )


# ==================== ШАГ 3: ВВОД КОЛИЧЕСТВА (условно) ====================

@router.message(RequestCreationStates.waiting_for_quantity)
async def process_quantity(message: Message, state: FSMContext):
    """Обработка ввода количества"""
    try:
        quantity = int(message.text.strip())
        
        if quantity <= 0:
            await message.answer("❌ Количество должно быть больше 0. Введите корректное число:")
            return
        
        # Обновляем данные
        data_dict = await state.get_data()
        data = RequestCreationData.from_dict(data_dict)
        data.quantity = quantity
        await state.set_data(data.to_dict())
        
        # Переходим к приоритету
        await state.set_state(RequestCreationStates.waiting_for_priority)
        keyboard = get_priority_keyboard()
        await message.answer(
            f"✅ <b>Количество:</b> {quantity} шт.\n\n"
            "⏰ <b>Шаг 4 из 6</b>\n\n"
            "Выберите приоритет заявки:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except ValueError:
        await message.answer("❌ Введите число (например: 5)")


# ==================== ШАГ 4: ВЫБОР ПРИОРИТЕТА ====================

@router.callback_query(F.data.startswith("priority_"), RequestCreationStates.waiting_for_priority)
async def process_priority(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора приоритета"""
    priority_type = callback.data.split("_")[1]  # 'normal' or 'urgent'
    
    # Обновляем данные
    data_dict = await state.get_data()
    data = RequestCreationData.from_dict(data_dict)
    data.priority = priority_type
    await state.set_data(data.to_dict())
    
    # Переходим к загрузке фото
    await state.set_state(RequestCreationStates.waiting_for_photos)
    
    priority_text = "Срочно 🚨" if priority_type == "urgent" else "Обычная ⏰"
    
    keyboard = get_photos_keyboard(current_count=0)
    
    await callback.message.edit_text(
        f"✅ <b>Приоритет:</b> {priority_text}\n\n"
        "📷 <b>Шаг 5 из 6</b>\n\n"
        "Можно приложить до 5 фото (необязательно).\n"
        "Отправьте фото или нажмите 'Пропустить':",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== ШАГ 5: ЗАГРУЗКА ФОТО ====================

# Обработка текста в состоянии ожидания фото (помощь пользователю)
@router.message(RequestCreationStates.waiting_for_photos, ~F.photo)
async def process_non_photo_in_photos_state(message: Message, state: FSMContext):
    """Обработка текста вместо фото"""
    if message.text and message.text.strip().lower() in ["пропустить", "skip", "далее"]:
        # Пользователь написал текст "пропустить"
        data_dict = await state.get_data()
        data = RequestCreationData.from_dict(data_dict)
        await proceed_to_confirmation(message, state, data)
    else:
        await message.answer(
            "📷 Отправьте фото или нажмите кнопку 'Пропустить'.\n"
            "Если хотите пропустить загрузку фото, используйте кнопку ниже:",
            reply_markup=get_photos_keyboard(current_count=0)
        )


# Обработка текста в состоянии ожидания фото (помощь пользователю)
@router.message(RequestCreationStates.waiting_for_photos, ~F.photo)
async def process_non_photo_in_photos_state(message: Message, state: FSMContext):
    """Обработка текста вместо фото"""
    # Проверяем, если пользователь написал команду отмены
    if message.text and message.text.strip().lower() in ["отмена", "отменить", "cancel"]:
        await message.answer("Используйте кнопку 'Отменить' для отмены создания заявки.")
        return
    
    data_dict = await state.get_data()
    data = RequestCreationData.from_dict(data_dict)
    current_count = len(data.photos)
    
    keyboard = get_photos_keyboard(current_count=current_count)
    await message.answer(
        "📷 Пожалуйста, отправьте фото или нажмите кнопку 'Пропустить' для продолжения.",
        reply_markup=keyboard
    )


@router.message(RequestCreationStates.waiting_for_photos, F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Обработка загрузки фото"""
    # Получаем самое большое фото (лучшее качество)
    photo = message.photo[-1]
    file_id = photo.file_id
    
    # Обновляем данные
    data_dict = await state.get_data()
    data = RequestCreationData.from_dict(data_dict)
    
    if len(data.photos) >= 5:
        await message.answer("❌ Можно приложить максимум 5 фото. Переходим к подтверждению.")
        await proceed_to_confirmation(message, state, data)
        return
    
    data.photos.append(file_id)
    await state.set_data(data.to_dict())
    
    current_count = len(data.photos)
    
    if current_count >= 5:
        # Достигнут максимум
        keyboard = get_photos_keyboard(current_count=5, max_count=5)
        await message.answer(
            f"✅ Фото {current_count}/5 добавлено.\n\n"
            "Достигнут максимум фото. Переходим к подтверждению:",
            reply_markup=keyboard
        )
    else:
        # Можно добавить еще
        keyboard = get_photos_keyboard(current_count=current_count)
        await message.answer(
            f"✅ Фото {current_count}/5 добавлено.\n\n"
            "Отправьте следующее фото или нажмите 'Пропустить':",
            reply_markup=keyboard
        )


@router.callback_query(F.data == "skip_photos", RequestCreationStates.waiting_for_photos)
async def skip_photos(callback: CallbackQuery, state: FSMContext):
    """Пропустить загрузку фото"""
    data_dict = await state.get_data()
    data = RequestCreationData.from_dict(data_dict)
    
    await callback.message.delete()
    await proceed_to_confirmation(callback.message, state, data)
    await callback.answer()


@router.callback_query(F.data == "proceed_to_confirm", RequestCreationStates.waiting_for_photos)
async def proceed_from_photos(callback: CallbackQuery, state: FSMContext):
    """Переход к подтверждению после загрузки фото"""
    data_dict = await state.get_data()
    data = RequestCreationData.from_dict(data_dict)
    
    await callback.message.delete()
    await proceed_to_confirmation(callback.message, state, data)
    await callback.answer()


# ==================== ШАГ 6: ПОДТВЕРЖДЕНИЕ ====================

async def proceed_to_confirmation(message: Message, state: FSMContext, data: RequestCreationData):
    """Переход к экрану подтверждения"""
    await state.set_state(RequestCreationStates.waiting_for_confirmation)
    
    preview_text = data.to_preview_text()
    keyboard = get_confirmation_keyboard()
    
    await message.answer(
        preview_text + "\n\n"
        "📋 <b>Шаг 6 из 6</b>\n\n"
        "Проверьте данные и подтвердите создание заявки:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "confirm_request", RequestCreationStates.waiting_for_confirmation)
async def confirm_request(callback: CallbackQuery, state: FSMContext, user_id: int, user_role: str, db_session, bot):
    """Подтверждение и создание заявки"""
    data_dict = await state.get_data()
    data = RequestCreationData.from_dict(data_dict)
    
    # Проверяем полноту данных
    if not data.is_complete():
        await callback.answer("❌ Данные неполные. Пожалуйста, заполните все поля.", show_alert=True)
        return
    
    try:
        # Создаем заявку
        request = await request_service.create_request(
            session=db_session,
            user_id=user_id,
            category=data.category,
            description=data.description,
            priority=data.priority,
            quantity=data.quantity,
            photo_file_ids=data.photos if data.photos else None
        )
        
        # Отправляем уведомление завхозу
        from bot.services.notification_service import NotificationService
        notification_service = NotificationService(bot)
        await notification_service.notify_warehouseman_new_request(request)
        
        # Очищаем состояние
        await state.clear()
        
        # Отправляем подтверждение
        await callback.message.edit_text(
            f"✅ <b>Заявка успешно создана!</b>\n\n"
            f"📋 <b>Номер заявки:</b> {request.number}\n\n"
            "Заявка отправлена завхозу. Вы получите уведомление о смене статуса.",
            parse_mode="HTML"
        )
        
        # Возвращаем главное меню в зависимости от роли
        from bot.keyboards.manager import get_manager_keyboard
        from bot.keyboards.warehouseman import get_warehouseman_keyboard
        
        if user_role == "manager":
            keyboard = get_manager_keyboard()
        elif user_role == "warehouseman":
            keyboard = get_warehouseman_keyboard()
        else:
            keyboard = get_employee_keyboard()
        
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=keyboard
        )
        
        await callback.answer("Заявка создана!")
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка при создании заявки: {e}", show_alert=True)


# ==================== РЕДАКТИРОВАНИЕ ЗАЯВКИ ====================

@router.callback_query(F.data == "edit_request", RequestCreationStates.waiting_for_confirmation)
async def edit_request(callback: CallbackQuery, state: FSMContext):
    """Меню редактирования заявки"""
    keyboard = get_edit_request_keyboard()
    
    await callback.message.edit_text(
        "✏️ Что вы хотите изменить?",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "edit_category", RequestCreationStates.waiting_for_confirmation)
async def edit_category(callback: CallbackQuery, state: FSMContext):
    """Редактирование категории"""
    await state.set_state(RequestCreationStates.waiting_for_category)
    keyboard = get_categories_keyboard()
    
    await callback.message.edit_text(
        "📂 Выберите категорию заявки:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "edit_description", RequestCreationStates.waiting_for_confirmation)
async def edit_description(callback: CallbackQuery, state: FSMContext):
    """Редактирование описания"""
    await state.set_state(RequestCreationStates.waiting_for_description)
    
    await callback.message.edit_text(
        "📝 Опишите, что нужно или какая проблема:"
    )
    await callback.answer()


@router.callback_query(F.data == "edit_quantity", RequestCreationStates.waiting_for_confirmation)
async def edit_quantity(callback: CallbackQuery, state: FSMContext):
    """Редактирование количества"""
    data_dict = await state.get_data()
    data = RequestCreationData.from_dict(data_dict)
    
    if not data.is_material_category():
        await callback.answer("Для этой категории количество не требуется.", show_alert=True)
        return
    
    await state.set_state(RequestCreationStates.waiting_for_quantity)
    
    await callback.message.edit_text(
        "🔢 Укажите количество (только число):",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "edit_priority", RequestCreationStates.waiting_for_confirmation)
async def edit_priority(callback: CallbackQuery, state: FSMContext):
    """Редактирование приоритета"""
    await state.set_state(RequestCreationStates.waiting_for_priority)
    keyboard = get_priority_keyboard()
    
    await callback.message.edit_text(
        "⏰ Выберите приоритет заявки:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "edit_photos", RequestCreationStates.waiting_for_confirmation)
async def edit_photos(callback: CallbackQuery, state: FSMContext):
    """Редактирование фото"""
    data_dict = await state.get_data()
    data = RequestCreationData.from_dict(data_dict)
    
    await state.set_state(RequestCreationStates.waiting_for_photos)
    keyboard = get_photos_keyboard(current_count=len(data.photos))
    
    await callback.message.edit_text(
        "📷 Можно приложить до 5 фото.\n"
        "Отправьте фото или нажмите 'Пропустить':",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_confirm", RequestCreationStates.waiting_for_confirmation)
async def back_to_confirm(callback: CallbackQuery, state: FSMContext):
    """Вернуться к подтверждению"""
    data_dict = await state.get_data()
    data = RequestCreationData.from_dict(data_dict)
    
    preview_text = data.to_preview_text()
    keyboard = get_confirmation_keyboard()
    
    await callback.message.edit_text(
        preview_text + "\n\n"
        "📋 Проверьте данные и подтвердите создание заявки:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


# ==================== ОТМЕНА СОЗДАНИЯ ЗАЯВКИ ====================

@router.callback_query(F.data == "cancel_request")
async def cancel_request_creation(callback: CallbackQuery, state: FSMContext, user_role: str):
    """Отмена создания заявки"""
    await state.clear()
    
    await callback.message.edit_text(
        "❌ Создание заявки отменено."
    )
    
    # Возвращаем главное меню в зависимости от роли
    from bot.keyboards.employee import get_employee_keyboard
    from bot.keyboards.warehouseman import get_warehouseman_keyboard
    from bot.keyboards.manager import get_manager_keyboard
    
    if user_role == "warehouseman":
        keyboard = get_warehouseman_keyboard()
    elif user_role == "manager":
        keyboard = get_manager_keyboard()
    else:
        keyboard = get_employee_keyboard()
    
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=keyboard
    )
    
    await callback.answer("Отменено")

