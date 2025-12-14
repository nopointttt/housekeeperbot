"""Inline клавиатуры для всех ролей"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Optional


def get_request_actions_keyboard(request_id: int) -> InlineKeyboardMarkup:
    """
    Получить inline клавиатуру с действиями для заявки (для завхоза)
    
    Args:
        request_id: ID заявки
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Взять в работу", callback_data=f"request_take_{request_id}"),
                InlineKeyboardButton(text="Выполнено", callback_data=f"request_complete_{request_id}"),
            ],
            [
                InlineKeyboardButton(text="Отклонить", callback_data=f"request_reject_{request_id}"),
                InlineKeyboardButton(text="Написать сотруднику", callback_data=f"request_message_{request_id}"),
            ],
        ]
    )
    return keyboard


def get_complaint_button_keyboard(request_id: int) -> InlineKeyboardMarkup:
    """
    Получить inline клавиатуру с кнопкой жалобы (для сотрудника)
    
    Args:
        request_id: ID заявки
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Пожаловаться руководителю", callback_data=f"complaint_{request_id}"),
            ],
        ]
    )
    return keyboard


def get_confirmation_keyboard(action: str, item_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру подтверждения/отмены
    
    Args:
        action: Действие (например, 'send_broadcast')
        item_id: ID элемента (опционально)
    """
    callback_data = f"{action}_confirm"
    if item_id:
        callback_data = f"{action}_{item_id}_confirm"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=callback_data),
                InlineKeyboardButton(text="❌ Отменить", callback_data=f"{action}_cancel"),
            ],
        ]
    )
    return keyboard


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру с кнопкой отмены"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel"),
            ],
        ]
    )
    return keyboard


def get_request_details_keyboard(request_id: int) -> InlineKeyboardMarkup:
    """
    Получить inline клавиатуру для просмотра деталей заявки (для руководителя)
    
    Args:
        request_id: ID заявки
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Подробнее", callback_data=f"manager_view_{request_id}"),
            ],
        ]
    )
    return keyboard
