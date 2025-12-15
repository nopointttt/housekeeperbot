"""Клавиатуры для техника"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import Optional


def get_warehouseman_keyboard(new_requests_count: Optional[int] = None, is_manager: bool = False) -> ReplyKeyboardMarkup:
    """
    Получить ReplyKeyboard для техника
    
    Args:
        new_requests_count: Количество новых заявок для отображения в бейджике (не используется, оставлено для совместимости)
        is_manager: Если True, показывает кнопку "Зайти как руководитель"
    """
    buttons = [
        [KeyboardButton(text="Все заявки")],
        [KeyboardButton(text="Все заявки за сегодня")],
        [KeyboardButton(text="Все заявки за неделю")],
        [KeyboardButton(text="Склад")],
        [KeyboardButton(text="Рассылка всем пользователям")],
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

