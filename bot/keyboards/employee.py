"""Клавиатуры для сотрудников"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_employee_keyboard() -> ReplyKeyboardMarkup:
    """Получить ReplyKeyboard для сотрудника"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Новая заявка")],
            [KeyboardButton(text="Мои заявки")],
            [KeyboardButton(text="Связаться с завхозом")],
            [KeyboardButton(text="Помощь")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard

