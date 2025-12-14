"""FSM состояния для связи с завхозом"""
from aiogram.fsm.state import State, StatesGroup


class ContactWarehousemanStates(StatesGroup):
    """Состояния для отправки сообщения завхозу"""
    waiting_for_message = State()

