"""Клавиатуры для пользователей"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import Optional


def get_employee_keyboard(is_manager: bool = False) -> ReplyKeyboardMarkup:
    """
    Получить ReplyKeyboard для пользователя
    
    Args:
        is_manager: Если True, показывает кнопку "Зайти как руководитель"
    """
    buttons = [
        [KeyboardButton(text="Новая заявка")],
        [KeyboardButton(text="Мои заявки")],
        [KeyboardButton(text="Связаться с техником")],
        [KeyboardButton(text="Помощь")],
    ]
    
    # Добавляем кнопку для менеджера
    if is_manager:
        buttons.append([KeyboardButton(text="Зайти как руководитель")])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard

