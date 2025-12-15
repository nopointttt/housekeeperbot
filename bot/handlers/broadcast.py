"""Обработчики для рассылок"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.services.broadcast_service import broadcast_service
from bot.keyboards.warehouseman import get_warehouseman_keyboard
from bot.keyboards.inline import get_confirmation_keyboard, get_cancel_keyboard
from bot.states.broadcast import BroadcastStates

router = Router(name="broadcast")


@router.message(F.text == "Рассылка всем пользователям")
async def start_broadcast(message: Message, state: FSMContext, user_role: str):
    """Начало создания рассылки"""
    if user_role != "warehouseman":
        await message.answer("❌ У вас нет доступа к рассылкам. Эта функция доступна только технику.")
        return
    
    await state.set_state(BroadcastStates.waiting_for_message)
    
    await message.answer(
        "📢 <b>Рассылка всем пользователям</b>\n\n"
        "Напишите сообщение для рассылки:",
        reply_markup=get_cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext, db_session):
    """Обработка текста рассылки"""
    text = message.text.strip()
    
    if len(text) < 5:
        await message.answer("❌ Сообщение слишком короткое. Пожалуйста, напишите подробнее (минимум 5 символов).")
        return
    
    # Сохраняем текст сообщения
    await state.update_data(broadcast_text=text)
    await state.set_state(BroadcastStates.waiting_for_confirmation)
    
    # Получаем количество получателей
    employees = await broadcast_service.get_all_employees(db_session)
    count = len(employees)
    
    preview_text = f"📢 <b>Предпросмотр рассылки</b>\n\n"
    preview_text += f"<b>Сообщение:</b>\n{text}\n\n"
    preview_text += f"👥 <b>Получателей:</b> {count} пользователей"
    
    keyboard = get_confirmation_keyboard("broadcast")
    
    await message.answer(
        preview_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "broadcast_confirm", BroadcastStates.waiting_for_confirmation)
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext, db_session, bot, base_role: str):
    """Подтверждение и отправка рассылки"""
    data = await state.get_data()
    text = data.get("broadcast_text")
    
    if not text:
        await callback.answer("❌ Ошибка: сообщение не найдено", show_alert=True)
        await state.clear()
        return
    
    # Получаем всех пользователей
    employees = await broadcast_service.get_all_employees(db_session)
    
    if not employees:
        await callback.answer("❌ Нет пользователей для рассылки", show_alert=True)
        await state.clear()
        return
    
    # Формируем сообщение
    broadcast_message = f"📢 <b>Рассылка от техника</b>\n\n{text}"
    
    # Отправляем сообщение всем пользователям
    success_count = 0
    failed_count = 0
    
    for employee in employees:
        try:
            await bot.send_message(
                chat_id=employee.id,
                text=broadcast_message,
                parse_mode="HTML"
            )
            success_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Ошибка отправки рассылки пользователю {employee.id}: {e}")
    
    # Очищаем состояние
    await state.clear()
    
    # Отправляем отчет
    report_text = f"✅ <b>Рассылка завершена</b>\n\n"
    report_text += f"✅ Успешно отправлено: {success_count}\n"
    if failed_count > 0:
        report_text += f"❌ Ошибок: {failed_count}"
    
    await callback.message.edit_text(
        report_text,
        parse_mode="HTML"
    )
    
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_warehouseman_keyboard(is_manager=(base_role == "manager"))
    )
    
    await callback.answer(f"Рассылка отправлена {success_count} пользователям")


@router.callback_query(F.data == "broadcast_cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext, base_role: str):
    """Отмена рассылки"""
    await state.clear()
    
    await callback.message.edit_text("❌ Рассылка отменена.")
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_warehouseman_keyboard(is_manager=(base_role == "manager"))
    )
    
    await callback.answer("Отменено")

