"""FSM состояния для действий техника"""
from aiogram.fsm.state import State, StatesGroup


class WarehousemanActionStates(StatesGroup):
    """Состояния для действий техника"""
    waiting_for_rejection_reason = State()  # Ожидание причины отклонения
    waiting_for_message_to_employee = State()  # Ожидание сообщения пользователю

