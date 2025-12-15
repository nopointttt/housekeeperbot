"""Клавиатуры для руководителя"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_manager_keyboard() -> ReplyKeyboardMarkup:
    """Получить ReplyKeyboard для руководителя"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Новая заявка")],
            [KeyboardButton(text="Все заявки")],
            [KeyboardButton(text="Заявки за сегодня")],
            [KeyboardButton(text="Заявки за неделю")],
            [KeyboardButton(text="В работе > 3 дней")],
            [KeyboardButton(text="В работе > 7 дней")],
            [KeyboardButton(text="Отчёт за период")],
            [KeyboardButton(text="Жалобы на техника")],
            [KeyboardButton(text="Склад")],
            [KeyboardButton(text="Управление техниками")],
            [KeyboardButton(text="Зайти как пользователь"), KeyboardButton(text="Зайти как техник")],
            [KeyboardButton(text="Зайти как руководитель")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard

