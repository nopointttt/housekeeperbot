"""FSM состояния для связи с техником"""
from aiogram.fsm.state import State, StatesGroup


class ContactWarehousemanStates(StatesGroup):
    """Состояния для отправки сообщения технику"""
    waiting_for_message = State()

