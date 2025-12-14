"""Клавиатуры для завхоза"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import Optional


def get_warehouseman_keyboard(new_requests_count: Optional[int] = None) -> ReplyKeyboardMarkup:
    """
    Получить ReplyKeyboard для завхоза
    
    Args:
        new_requests_count: Количество новых заявок для отображения в бейджике (не используется, оставлено для совместимости)
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Все заявки")],
            [KeyboardButton(text="Все заявки за сегодня")],
            [KeyboardButton(text="Все заявки за неделю")],
            [KeyboardButton(text="Склад")],
            [KeyboardButton(text="Рассылка всем сотрудникам")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard

