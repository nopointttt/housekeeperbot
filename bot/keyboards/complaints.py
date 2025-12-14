"""Клавиатуры для жалоб"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Причины жалоб (фиксированный список)
COMPLAINT_REASONS = [
    "Не отвечает на сообщения",
    "Игнорирует заявку",
    "Некорректное поведение",
    "Нарушение сроков",
    "Другое"
]


def get_complaint_reasons_keyboard() -> InlineKeyboardMarkup:
    """Получить inline клавиатуру с причинами жалоб"""
    buttons = []
    
    # Создаем кнопки по 1 в ряд
    for i, reason in enumerate(COMPLAINT_REASONS):
        buttons.append([
            InlineKeyboardButton(
                text=reason,
                callback_data=f"complaint_reason_{i}"
            )
        ])
    
    # Добавляем кнопку отмены
    buttons.append([InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_complaint")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_complaint_button_keyboard(request_id: int) -> InlineKeyboardMarkup:
    """
    Получить inline клавиатуру с кнопкой жалобы для заявки
    
    Args:
        request_id: ID заявки
    """
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚠️ Пожаловаться руководителю",
                    callback_data=f"complaint_start_{request_id}"
                ),
            ],
        ]
    )
    return keyboard

