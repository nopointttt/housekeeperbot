"""FSM состояния для управления складом"""
from aiogram.fsm.state import State, StatesGroup


class WarehouseManagementStates(StatesGroup):
    """Состояния для управления складом"""
    waiting_for_item_name = State()           # Ожидание названия позиции
    waiting_for_min_quantity = State()        # Ожидание минимального остатка
    waiting_for_add_quantity = State()        # Ожидание количества для добавления
    waiting_for_subtract_quantity = State()   # Ожидание количества для списания
    waiting_for_new_min_quantity = State()    # Ожидание нового минимального остатка
    waiting_for_writeoff_item = State()       # Ожидание выбора позиции для списания
    waiting_for_writeoff_quantity = State()   # Ожидание количества для списания при закрытии заявки

