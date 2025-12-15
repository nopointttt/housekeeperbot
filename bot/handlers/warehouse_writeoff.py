"""Обработчики списания со склада при закрытии заявки"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from bot.services.warehouse_service import warehouse_service
from bot.services.warehouseman_service import warehouseman_service
from bot.services.notification_service import NotificationService
from bot.utils.request_formatter import format_request_full
from bot.keyboards.warehouseman import get_warehouseman_keyboard
from bot.states.warehouse_management import WarehouseManagementStates

router = Router(name="warehouse_writeoff")


@router.callback_query(F.data.startswith("writeoff_item_"))
async def process_writeoff_item(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора позиции для списания"""
    item_id = int(callback.data.split("_")[-1])
    
    # Сохраняем ID позиции
    await state.update_data(writeoff_item_id=item_id)
    await state.set_state(WarehouseManagementStates.waiting_for_writeoff_quantity)
    
    await callback.message.edit_text(
        "➖ <b>Списание со склада</b>\n\n"
        "Введите количество для списания:",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "writeoff_cancel")
async def cancel_writeoff(callback: CallbackQuery, state: FSMContext, db_session, bot, base_role: str):
    """Отмена списания, просто завершаем заявку"""
    data = await state.get_data()
    request_id = data.get("request_id")
    
    if not request_id:
        await callback.answer("Ошибка: данные не найдены", show_alert=True)
        await state.clear()
        return
    
    # Завершаем заявку без списания
    request = await warehouseman_service.complete_request(db_session, request_id)
    
    if not request:
        await callback.answer("❌ Не удалось завершить заявку", show_alert=True)
        await state.clear()
        return
    
    # Уведомляем пользователя
    notification_service = NotificationService(bot)
    await notification_service.notify_employee_request_status_changed(request, "Выполнено")
    
    await callback.message.edit_text(
        f"✅ Заявка {request.number} завершена.\n"
        "Списание со склада отменено."
    )
    
    await state.clear()
    await callback.answer("Заявка завершена")


@router.message(WarehouseManagementStates.waiting_for_writeoff_quantity)
async def process_writeoff_quantity(message: Message, state: FSMContext, db_session, bot, base_role: str):
    """Обработка количества для списания"""
    try:
        quantity = int(message.text.strip())
        
        if quantity <= 0:
            await message.answer("❌ Количество должно быть больше 0. Введите число:")
            return
        
        data = await state.get_data()
        request_id = data.get("request_id")
        item_id = data.get("writeoff_item_id")
        
        if not request_id or not item_id:
            await message.answer("❌ Ошибка: данные не найдены. Начните заново.")
            await state.clear()
            return
        
        # Сначала списываем со склада
        item = await warehouse_service.subtract_quantity(db_session, item_id, quantity)
        
        if not item:
            # Проверяем, недостаточно ли товара
            existing_item = await warehouse_service.get_item_by_id(db_session, item_id)
            if existing_item and existing_item.current_quantity < quantity:
                await message.answer(
                    f"❌ Недостаточно товара на складе!\n"
                    f"Текущее количество: {existing_item.current_quantity} шт.\n"
                    f"Попытка списать: {quantity} шт.\n\n"
                    "Заявка будет завершена без списания со склада."
                )
            else:
                await message.answer("❌ Позиция не найдена на складе.")
            
            # Все равно завершаем заявку
            request = await warehouseman_service.complete_request(db_session, request_id)
            if request:
                notification_service = NotificationService(bot)
                await notification_service.notify_employee_request_status_changed(request, "Выполнено")
            
            await state.clear()
            return
        
        # Теперь завершаем заявку
        request = await warehouseman_service.complete_request(db_session, request_id)
        
        if not request:
            await message.answer("❌ Не удалось завершить заявку.")
            await state.clear()
            return
        
        # Уведомляем пользователя
        notification_service = NotificationService(bot)
        await notification_service.notify_employee_request_status_changed(request, "Выполнено")
        
        await message.answer(
            f"✅ Заявка {request.number} завершена!\n"
            f"✅ Со склада списано: {item.name} - {quantity} шт.\n"
            f"Остаток на складе: {item.current_quantity} шт.",
            reply_markup=get_warehouseman_keyboard(is_manager=(base_role == "manager"))
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите число (например: 10)")

