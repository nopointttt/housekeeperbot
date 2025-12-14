"""Клавиатуры для завхоза"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import Optional


def get_warehouseman_keyboard(new_requests_count: Optional[int] = None, is_manager: bool = False) -> ReplyKeyboardMarkup:
    """
    Получить ReplyKeyboard для завхоза
    
    Args:
        new_requests_count: Количество новых заявок для отображения в бейджике (не используется, оставлено для совместимости)
        is_manager: Если True, показывает кнопку возврата к роли руководителя
    """
    buttons = [
        [KeyboardButton(text="Все заявки")],
        [KeyboardButton(text="Все заявки за сегодня")],
        [KeyboardButton(text="Все заявки за неделю")],
        [KeyboardButton(text="Склад")],
        [KeyboardButton(text="Рассылка всем сотрудникам")],
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

