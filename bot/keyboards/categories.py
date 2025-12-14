"""Клавиатуры для выбора категорий и приоритетов"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Фиксированный список категорий
CATEGORIES = [
    "Канцелярия",
    "Чай, кофе, сахар, вода",
    "Хозтовары и уборка",
    "Лампочки и мелкая электрика",
    "Сантехника",
    "Ремонт мебели, окон, дверей",
    "Ключи и пропуска",
    "ИТ-оборудование и расходники",
    "Прочее",
]


def get_categories_keyboard() -> InlineKeyboardMarkup:
    """Получить inline клавиатуру с категориями заявок"""
    buttons = []
    
    # Создаем кнопки по 2 в ряд
    for i in range(0, len(CATEGORIES), 2):
        row = []
        row.append(InlineKeyboardButton(
            text=CATEGORIES[i],
            callback_data=f"category_{i}"
        ))
        
        if i + 1 < len(CATEGORIES):
            row.append(InlineKeyboardButton(
                text=CATEGORIES[i + 1],
                callback_data=f"category_{i + 1}"
            ))
        
        buttons.append(row)
    
    # Добавляем кнопку отмены
    buttons.append([InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_request")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_priority_keyboard() -> InlineKeyboardMarkup:
    """Получить inline клавиатуру с приоритетами"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⏰ Обычная", callback_data="priority_normal"),
                InlineKeyboardButton(text="🚨 Срочно", callback_data="priority_urgent"),
            ],
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_request"),
            ],
        ]
    )
    return keyboard


def get_photos_keyboard(current_count: int, max_count: int = 5) -> InlineKeyboardMarkup:
    """
    Получить клавиатуру для загрузки фото
    
    Args:
        current_count: Текущее количество загруженных фото
        max_count: Максимальное количество фото
    """
    buttons = []
    
    if current_count < max_count:
        buttons.append([
            InlineKeyboardButton(
                text="⏭️ Пропустить",
                callback_data="skip_photos"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="✅ Перейти к подтверждению",
                callback_data="proceed_to_confirm"
            )
        ])
    
    buttons.append([
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_request")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру подтверждения заявки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Создать заявку", callback_data="confirm_request"),
                InlineKeyboardButton(text="✏️ Изменить", callback_data="edit_request"),
            ],
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_request"),
            ],
        ]
    )
    return keyboard


def get_edit_request_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру для редактирования заявки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📂 Категория", callback_data="edit_category"),
                InlineKeyboardButton(text="📝 Описание", callback_data="edit_description"),
            ],
            [
                InlineKeyboardButton(text="🔢 Количество", callback_data="edit_quantity"),
                InlineKeyboardButton(text="⏰ Приоритет", callback_data="edit_priority"),
            ],
            [
                InlineKeyboardButton(text="📷 Фото", callback_data="edit_photos"),
            ],
            [
                InlineKeyboardButton(text="✅ Вернуться к подтверждению", callback_data="back_to_confirm"),
            ],
        ]
    )
    return keyboard

