"""Клавиатуры для сотрудников"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import Optional


def get_employee_keyboard(is_manager: bool = False) -> ReplyKeyboardMarkup:
    """
    Получить ReplyKeyboard для сотрудника
    
    Args:
        is_manager: Если True, показывает кнопку возврата к роли руководителя
    """
    buttons = [
        [KeyboardButton(text="Новая заявка")],
        [KeyboardButton(text="Мои заявки")],
        [KeyboardButton(text="Связаться с завхозом")],
        [KeyboardButton(text="Помощь")],
    ]
    
    # Добавляем кнопку возврата для менеджера
    if is_manager:
        buttons.append([KeyboardButton(text="Вернуться к роли руководителя")])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard

