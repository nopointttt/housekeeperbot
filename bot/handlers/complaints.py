"""Обработчики для создания жалоб"""
import logging
import traceback
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.states.complaint_creation import ComplaintCreationStates
from bot.services.complaint_service import complaint_service
from bot.services.request_service import request_service
from bot.services.notification_service import NotificationService
from bot.keyboards.complaints import get_complaint_reasons_keyboard, COMPLAINT_REASONS
from bot.keyboards.employee import get_employee_keyboard
from bot.keyboards.inline import get_cancel_keyboard

router = Router(name="complaints")
logger = logging.getLogger(__name__)


# ==================== НАЧАЛО СОЗДАНИЯ ЖАЛОБЫ ====================

@router.callback_query(F.data.startswith("complaint_start_"))
async def start_complaint_creation(callback: CallbackQuery, state: FSMContext, user_id: int, tenant_id: int, db_session):
    """Начало создания жалобы"""
    # Сразу отвечаем на callback, чтобы убрать индикатор загрузки
    await callback.answer()
    
    try:
        request_id = int(callback.data.split("_")[-1])
        logger.debug(f"Начало создания жалобы для заявки {request_id}, пользователь {user_id}")
    except (ValueError, IndexError) as e:
        logger.error(f"Ошибка парсинга request_id: {e}, callback.data={callback.data}")
        logger.error(f"Трейсбек: {traceback.format_exc()}")
        await callback.message.answer("❌ Ошибка: неверный формат данных.")
        return
    
    try:
        # Проверяем, что заявка существует и принадлежит пользователю
        # Для жалобы не нужен user, только номер заявки - оптимизируем запрос
        request = await request_service.get_request_by_id(
            db_session, 
            tenant_id,
            request_id, 
            load_user=False,  # Не загружаем user - ускоряет запрос
            load_photos=False  # Не загружаем фото - ускоряет запрос
        )
        
        if not request:
            logger.warning(f"Заявка {request_id} не найдена")
            await callback.message.answer("❌ Заявка не найдена.")
            return
        
        if request.user_id != user_id:
            logger.warning(f"Попытка доступа к заявке {request_id} пользователем {user_id} (владелец: {request.user_id})")
            await callback.message.answer("❌ У вас нет доступа к этой заявке.")
            return
        
        # Сохраняем ID заявки в состоянии
        await state.update_data(request_id=request_id)
        await state.set_state(ComplaintCreationStates.waiting_for_reason)
        
        keyboard = get_complaint_reasons_keyboard()
        
        text = (
            f"⚠️ <b>Жалоба на техника</b>\n\n"
            f"📋 Заявка: <b>{request.number}</b>\n\n"
            "Выберите причину жалобы:"
        )
        
        # Проверяем, можно ли редактировать сообщение
        # Если сообщение содержит медиа (фото), его нельзя редактировать
        try:
            # Пытаемся отредактировать сообщение
            if callback.message.text or callback.message.caption:
                # Сообщение содержит текст - можно редактировать
                await callback.message.edit_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                logger.debug(f"Сообщение отредактировано для заявки {request_id}")
            else:
                # Сообщение не содержит текста - отправляем новое
                raise ValueError("Message has no text to edit")
        except Exception as edit_error:
            # Не удалось отредактировать (например, сообщение с фото)
            logger.debug(f"Не удалось отредактировать сообщение: {edit_error}, отправляем новое")
            await callback.message.answer(
                text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Ошибка при создании жалобы для заявки {request_id}: {e}")
        logger.error(f"Трейсбек: {traceback.format_exc()}")
        await callback.message.answer(
            f"❌ Ошибка при загрузке заявки: {e}\n"
            "Попробуйте позже."
        )


# ==================== ВЫБОР ПРИЧИНЫ ЖАЛОБЫ ====================

@router.callback_query(F.data.startswith("complaint_reason_"), ComplaintCreationStates.waiting_for_reason)
async def process_complaint_reason(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора причины жалобы"""
    await callback.answer()
    
    try:
        reason_index = int(callback.data.split("_")[-1])
        reason = COMPLAINT_REASONS[reason_index]
        logger.debug(f"Выбрана причина жалобы: {reason} (индекс {reason_index})")
    except (ValueError, IndexError, KeyError) as e:
        logger.error(f"Ошибка выбора причины жалобы: {e}, callback.data={callback.data}")
        logger.error(f"Трейсбек: {traceback.format_exc()}")
        await callback.message.answer("❌ Ошибка: неверная причина жалобы.")
        return
    
    try:
        # Сохраняем причину
        await state.update_data(reason=reason)
        await state.set_state(ComplaintCreationStates.waiting_for_text)
        
        text = (
            f"✅ <b>Причина:</b> {reason}\n\n"
            "💬 Опишите ситуацию подробнее (свободный текст):"
        )
        
        # Проверяем, можно ли редактировать сообщение
        try:
            if callback.message.text or callback.message.caption:
                await callback.message.edit_text(
                    text,
                    reply_markup=get_cancel_keyboard(),
                    parse_mode="HTML"
                )
            else:
                raise ValueError("Message has no text to edit")
        except Exception as edit_error:
            logger.debug(f"Не удалось отредактировать сообщение: {edit_error}, отправляем новое")
            await callback.message.answer(
                text,
                reply_markup=get_cancel_keyboard(),
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Ошибка при обработке причины жалобы: {e}")
        logger.error(f"Трейсбек: {traceback.format_exc()}")
        await callback.message.answer(
            f"❌ Ошибка: {e}\n"
            "Попробуйте начать заново."
        )


# ==================== ВВОД ТЕКСТА ЖАЛОБЫ ====================

@router.message(ComplaintCreationStates.waiting_for_text)
async def process_complaint_text(message: Message, state: FSMContext, user_id: int, tenant_id: int, db_session, bot, base_role: str):
    """Обработка ввода текста жалобы"""
    text = message.text.strip()
    
    if len(text) < 10:
        await message.answer(
            "❌ Текст жалобы слишком короткий. Пожалуйста, опишите ситуацию подробнее (минимум 10 символов)."
        )
        return
    
    # Получаем данные из состояния
    data = await state.get_data()
    request_id = data.get("request_id")
    reason = data.get("reason")
    
    if not request_id or not reason:
        await message.answer("❌ Ошибка: данные не найдены. Начните заново.")
        await state.clear()
        return
    
    # Получаем заявку
    request = await request_service.get_request_by_id(db_session, tenant_id=tenant_id, request_id=request_id)
    if not request:
        await message.answer("❌ Заявка не найдена.")
        await state.clear()
        return
    
    try:
        logger.debug(f"Создание жалобы: user_id={user_id}, request_id={request_id}, reason={reason}, text_length={len(text)}")
        
        # Создаем жалобу
        complaint = await complaint_service.create_complaint(
            session=db_session,
            tenant_id=tenant_id,
            user_id=user_id,
            request_id=request_id,
            reason=reason,
            text=text
        )
        
        logger.info(f"Жалоба создана: ID={complaint.id}, user_id={user_id}, request_id={request_id}")
        
        # Отправляем уведомление только руководителю
        notification_service = NotificationService(bot)
        try:
            await notification_service.notify_manager_complaint(complaint, request)
            logger.debug("Уведомление руководителю отправлено")
        except Exception as notify_error:
            logger.error(f"Ошибка отправки уведомления руководителю: {notify_error}")
        
        # Очищаем состояние
        await state.clear()
        
        await message.answer(
            "✅ <b>Жалоба отправлена!</b>\n\n"
            "Руководитель получил уведомление.",
            reply_markup=get_employee_keyboard(is_manager=(base_role == "manager")),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при создании жалобы: {e}")
        logger.error(f"Трейсбек: {traceback.format_exc()}")
        await message.answer(
            f"❌ Ошибка при создании жалобы: {e}\n"
            "Попробуйте позже или обратитесь к руководителю напрямую.",
            reply_markup=get_employee_keyboard(is_manager=(base_role == "manager"))
        )
        await state.clear()


# ==================== ОТМЕНА СОЗДАНИЯ ЖАЛОБЫ ====================

@router.callback_query(F.data == "cancel_complaint")
async def cancel_complaint_creation(callback: CallbackQuery, state: FSMContext, base_role: str):
    """Отмена создания жалобы"""
    await state.clear()
    
    await callback.message.edit_text("❌ Создание жалобы отменено.")
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=get_employee_keyboard(is_manager=(base_role == "manager"))
    )
    
    await callback.answer("Отменено")

