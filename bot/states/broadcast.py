"""FSM состояния для рассылок"""
from aiogram.fsm.state import State, StatesGroup


class BroadcastStates(StatesGroup):
    """Состояния для создания рассылки"""
    waiting_for_message = State()      # Ожидание текста сообщения
    waiting_for_confirmation = State() # Ожидание подтверждения

