"""Состояния FSM для управления техниками"""
from aiogram.fsm.state import State, StatesGroup


class TechnicianManagementStates(StatesGroup):
    """Состояния для управления техниками"""
    waiting_for_technician_id = State()  # Ожидание ID или username техника

