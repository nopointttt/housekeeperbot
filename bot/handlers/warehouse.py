"""Обработчики для управления складом"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.services.warehouse_service import warehouse_service
from bot.keyboards.warehouse import (
    get_warehouse_list_keyboard,
    get_warehouse_item_keyboard,
    get_writeoff_item_keyboard,
    get_cancel_keyboard
)
from bot.keyboards.warehouseman import get_warehouseman_keyboard
from bot.states.warehouse_management import WarehouseManagementStates

router = Router(name="warehouse")


# ==================== ПРОСМОТР СКЛАДА ====================

@router.message(F.text == "Склад")
async def show_warehouse(message: Message, db_session):
    """Показать склад"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    items = await warehouse_service.get_all_items(db_session)
    
    if not items:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить позицию", callback_data="warehouse_add_item")]
            ]
        )
        await message.answer(
            "📦 <b>Склад</b>\n\n"
            "Позиций на складе пока нет.\n"
            "Добавьте первую позицию:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    # Формируем текст со списком позиций
    text = "📦 <b>Склад</b>\n\n"
    
    low_stock_count = sum(1 for item in items if item.current_quantity <= item.min_quantity)
    if low_stock_count > 0:
        text += f"⚠️ <b>Внимание!</b> {low_stock_count} позиций с низким остатком\n\n"
    
    for item in items:
        indicator = "⚠️" if item.current_quantity <= item.min_quantity else "✅"
        text += f"{indicator} <b>{item.name}</b>\n"
        text += f"   Текущее: {item.current_quantity} шт.\n"
        text += f"   Мин. остаток: {item.min_quantity} шт.\n\n"
    
    keyboard = get_warehouse_list_keyboard(items)
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ==================== ПРОСМОТР ДЕТАЛЕЙ ПОЗИЦИИ ====================

@router.callback_query(F.data.startswith("warehouse_item_"))
async def show_warehouse_item(callback: CallbackQuery, db_session):
    """Показать детали позиции на складе"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    item_id = int(callback.data.split("_")[-1])
    item = await warehouse_service.get_item_by_id(db_session, item_id)
    
    if not item:
        await callback.answer("Позиция не найдена", show_alert=True)
        return
    
    indicator = "⚠️" if item.current_quantity <= item.min_quantity else "✅"
    status_text = "Низкий остаток!" if item.current_quantity <= item.min_quantity else "Остаток в норме"
    
    text = f"📦 <b>{item.name}</b>\n\n"
    text += f"{indicator} <b>Статус:</b> {status_text}\n"
    text += f"📊 <b>Текущее количество:</b> {item.current_quantity} шт.\n"
    text += f"📉 <b>Минимальный остаток:</b> {item.min_quantity} шт.\n"
    text += f"📅 <b>Обновлено:</b> {item.updated_at.strftime('%d.%m.%Y %H:%M')}"
    
    keyboard = get_warehouse_item_keyboard(item.id)
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ==================== ДОБАВЛЕНИЕ ПОЗИЦИИ ====================

@router.callback_query(F.data == "warehouse_add_item")
async def start_add_item(callback: CallbackQuery, state: FSMContext):
    """Начало добавления новой позиции"""
    await state.set_state(WarehouseManagementStates.waiting_for_item_name)
    
    await callback.message.answer(
        "➕ <b>Добавление позиции на склад</b>\n\n"
        "Введите название позиции:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(WarehouseManagementStates.waiting_for_item_name)
async def process_item_name(message: Message, state: FSMContext, db_session):
    """Обработка названия позиции"""
    name = message.text.strip()
    
    if len(name) < 2:
        await message.answer("❌ Название слишком короткое. Введите название (минимум 2 символа):")
        return
    
    # Проверяем, не существует ли уже такая позиция
    existing = await warehouse_service.get_item_by_name(db_session, name)
    if existing:
        await message.answer(
            f"❌ Позиция '{name}' уже существует на складе.\n"
            "Введите другое название:"
        )
        return
    
    # Сохраняем название и переходим к минимальному остатку
    await state.update_data(item_name=name)
    await state.set_state(WarehouseManagementStates.waiting_for_min_quantity)
    
    await message.answer(
        f"✅ Название: <b>{name}</b>\n\n"
        "Введите минимальный остаток (число, можно 0):",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(WarehouseManagementStates.waiting_for_min_quantity)
async def process_min_quantity(message: Message, state: FSMContext, db_session):
    """Обработка минимального остатка"""
    try:
        min_quantity = int(message.text.strip())
        
        if min_quantity < 0:
            await message.answer("❌ Минимальный остаток не может быть отрицательным. Введите число (0 или больше):")
            return
        
        # Получаем название из состояния
        data = await state.get_data()
        item_name = data.get("item_name")
        
        if not item_name:
            await message.answer("❌ Ошибка: название не найдено. Начните заново.")
            await state.clear()
            return
        
        # Создаем позицию
        item = await warehouse_service.create_item(db_session, item_name, min_quantity)
        
        await message.answer(
            f"✅ Позиция '{item.name}' добавлена на склад!\n"
            f"Минимальный остаток: {item.min_quantity} шт.",
            reply_markup=get_warehouseman_keyboard()
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите число (например: 10)")


# ==================== УПРАВЛЕНИЕ КОЛИЧЕСТВОМ ====================

@router.callback_query(F.data.startswith("warehouse_add_"))
async def start_add_quantity(callback: CallbackQuery, state: FSMContext):
    """Начало добавления количества"""
    item_id = int(callback.data.split("_")[-1])
    
    await state.update_data(item_id=item_id, action="add")
    await state.set_state(WarehouseManagementStates.waiting_for_add_quantity)
    
    await callback.message.answer(
        "➕ <b>Приход товара</b>\n\n"
        "Введите количество для добавления:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("warehouse_subtract_"))
async def start_subtract_quantity(callback: CallbackQuery, state: FSMContext):
    """Начало списания количества"""
    item_id = int(callback.data.split("_")[-1])
    
    await state.update_data(item_id=item_id, action="subtract")
    await state.set_state(WarehouseManagementStates.waiting_for_subtract_quantity)
    
    await callback.message.answer(
        "➖ <b>Списание товара</b>\n\n"
        "Введите количество для списания:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(WarehouseManagementStates.waiting_for_add_quantity)
async def process_add_quantity(message: Message, state: FSMContext, db_session):
    """Обработка добавления количества"""
    try:
        quantity = int(message.text.strip())
        
        if quantity <= 0:
            await message.answer("❌ Количество должно быть больше 0. Введите число:")
            return
        
        data = await state.get_data()
        item_id = data.get("item_id")
        
        if not item_id:
            await message.answer("❌ Ошибка: данные не найдены. Начните заново.")
            await state.clear()
            return
        
        item = await warehouse_service.add_quantity(db_session, item_id, quantity)
        
        if not item:
            await message.answer("❌ Позиция не найдена.")
            await state.clear()
            return
        
        await message.answer(
            f"✅ Добавлено {quantity} шт.\n"
            f"Текущее количество: {item.current_quantity} шт.",
            reply_markup=get_warehouseman_keyboard()
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите число (например: 10)")


@router.message(WarehouseManagementStates.waiting_for_subtract_quantity)
async def process_subtract_quantity(message: Message, state: FSMContext, db_session):
    """Обработка списания количества"""
    try:
        quantity = int(message.text.strip())
        
        if quantity <= 0:
            await message.answer("❌ Количество должно быть больше 0. Введите число:")
            return
        
        data = await state.get_data()
        item_id = data.get("item_id")
        
        if not item_id:
            await message.answer("❌ Ошибка: данные не найдены. Начните заново.")
            await state.clear()
            return
        
        item = await warehouse_service.subtract_quantity(db_session, item_id, quantity)
        
        if not item:
            # Проверяем, недостаточно ли товара
            existing_item = await warehouse_service.get_item_by_id(db_session, item_id)
            if existing_item and existing_item.current_quantity < quantity:
                await message.answer(
                    f"❌ Недостаточно товара!\n"
                    f"Текущее количество: {existing_item.current_quantity} шт.\n"
                    f"Попытка списать: {quantity} шт."
                )
            else:
                await message.answer("❌ Позиция не найдена.")
            await state.clear()
            return
        
        await message.answer(
            f"✅ Списано {quantity} шт.\n"
            f"Текущее количество: {item.current_quantity} шт.",
            reply_markup=get_warehouseman_keyboard()
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите число (например: 10)")


# ==================== ИЗМЕНЕНИЕ МИНИМАЛЬНОГО ОСТАТКА ====================

@router.callback_query(F.data.startswith("warehouse_min_"))
async def start_change_min_quantity(callback: CallbackQuery, state: FSMContext):
    """Начало изменения минимального остатка"""
    item_id = int(callback.data.split("_")[-1])
    
    await state.update_data(item_id=item_id)
    await state.set_state(WarehouseManagementStates.waiting_for_new_min_quantity)
    
    await callback.message.answer(
        "⚙️ <b>Изменение минимального остатка</b>\n\n"
        "Введите новый минимальный остаток:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(WarehouseManagementStates.waiting_for_new_min_quantity)
async def process_new_min_quantity(message: Message, state: FSMContext, db_session):
    """Обработка нового минимального остатка"""
    try:
        min_quantity = int(message.text.strip())
        
        if min_quantity < 0:
            await message.answer("❌ Минимальный остаток не может быть отрицательным. Введите число (0 или больше):")
            return
        
        data = await state.get_data()
        item_id = data.get("item_id")
        
        if not item_id:
            await message.answer("❌ Ошибка: данные не найдены. Начните заново.")
            await state.clear()
            return
        
        item = await warehouse_service.update_min_quantity(db_session, item_id, min_quantity)
        
        if not item:
            await message.answer("❌ Позиция не найдена.")
            await state.clear()
            return
        
        await message.answer(
            f"✅ Минимальный остаток обновлен!\n"
            f"Новый минимальный остаток: {item.min_quantity} шт.\n"
            f"Текущее количество: {item.current_quantity} шт.",
            reply_markup=get_warehouseman_keyboard()
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите число (например: 10)")


# ==================== ОТМЕНА ====================

@router.callback_query(F.data == "warehouse_cancel")
async def cancel_warehouse_action(callback: CallbackQuery, state: FSMContext):
    """Отмена действия со складом"""
    await state.clear()
    
    await callback.message.edit_text("❌ Действие отменено.")
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_warehouseman_keyboard()
    )
    
    await callback.answer("Отменено")

