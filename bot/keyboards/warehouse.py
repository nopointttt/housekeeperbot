"""Клавиатуры для управления складом"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List
from bot.database.models import WarehouseItem


def get_warehouse_item_keyboard(item_id: int, user_role: str) -> InlineKeyboardMarkup:
    """
    Получить inline клавиатуру для позиции на складе
    
    Args:
        item_id: ID позиции
        user_role: Роль пользователя ('warehouseman' или 'manager')
                   Техник (warehouseman) может только добавлять, руководитель может и добавлять и списывать
    """
    buttons = []
    
    # Кнопка прихода (доступна всем)
    buttons.append([
        InlineKeyboardButton(text="➕ Приход", callback_data=f"warehouse_add_{item_id}"),
    ])
    
    # Кнопка списания (только для руководителя)
    if user_role == "manager":
        buttons[0].append(InlineKeyboardButton(text="➖ Списать", callback_data=f"warehouse_subtract_{item_id}"))
    
    # Кнопка изменения минимального остатка (доступна всем)
    buttons.append([
        InlineKeyboardButton(text="⚙️ Изменить мин. остаток", callback_data=f"warehouse_min_{item_id}"),
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_warehouse_list_keyboard(items: List[WarehouseItem]) -> InlineKeyboardMarkup:
    """
    Получить inline клавиатуру со списком позиций на складе
    
    Args:
        items: Список позиций
    """
    buttons = []
    
    # Группируем по 2 кнопки в ряд
    for i in range(0, len(items), 2):
        row = []
        item = items[i]
        # Добавляем индикатор низкого остатка
        indicator = "⚠️" if item.current_quantity <= item.min_quantity else "✅"
        row.append(InlineKeyboardButton(
            text=f"{indicator} {item.name}",
            callback_data=f"warehouse_item_{item.id}"
        ))
        
        if i + 1 < len(items):
            item = items[i + 1]
            indicator = "⚠️" if item.current_quantity <= item.min_quantity else "✅"
            row.append(InlineKeyboardButton(
                text=f"{indicator} {item.name}",
                callback_data=f"warehouse_item_{item.id}"
            ))
        
        buttons.append(row)
    
    # Кнопка добавления новой позиции
    buttons.append([InlineKeyboardButton(text="➕ Добавить позицию", callback_data="warehouse_add_item")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_writeoff_item_keyboard(items: List[WarehouseItem]) -> InlineKeyboardMarkup:
    """
    Получить inline клавиатуру для выбора позиции при списании со склада
    
    Args:
        items: Список позиций
    """
    buttons = []
    
    # Группируем по 2 кнопки в ряд
    for i in range(0, len(items), 2):
        row = []
        item = items[i]
        row.append(InlineKeyboardButton(
            text=f"{item.name} ({item.current_quantity} шт.)",
            callback_data=f"writeoff_item_{item.id}"
        ))
        
        if i + 1 < len(items):
            item = items[i + 1]
            row.append(InlineKeyboardButton(
                text=f"{item.name} ({item.current_quantity} шт.)",
                callback_data=f"writeoff_item_{item.id}"
            ))
        
        buttons.append(row)
    
    # Кнопка отмены
    buttons.append([InlineKeyboardButton(text="❌ Отменить", callback_data="writeoff_cancel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Получить клавиатуру с кнопкой отмены"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Отменить", callback_data="warehouse_cancel"),
            ],
        ]
    )
    return keyboard

