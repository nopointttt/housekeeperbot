"""FSM состояния для создания жалобы"""
from aiogram.fsm.state import State, StatesGroup


class ComplaintCreationStates(StatesGroup):
    """Состояния для создания жалобы"""
    waiting_for_reason = State()      # Шаг 1: Выбор причины
    waiting_for_text = State()        # Шаг 2: Ввод текста жалобы

