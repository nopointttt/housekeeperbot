"""FSM состояния для создания заявки"""
from aiogram.fsm.state import State, StatesGroup


class RequestCreationStates(StatesGroup):
    """Состояния для создания заявки"""
    waiting_for_category = State()      # Шаг 1: Выбор категории
    waiting_for_description = State()   # Шаг 2: Ввод описания
    waiting_for_quantity = State()      # Шаг 3: Ввод количества (условно)
    waiting_for_priority = State()      # Шаг 4: Выбор приоритета
    waiting_for_photos = State()        # Шаг 5: Загрузка фото
    waiting_for_confirmation = State()  # Шаг 6: Подтверждение

