"""FSM состояния для отчета за период"""
from aiogram.fsm.state import State, StatesGroup


class PeriodReportStates(StatesGroup):
    """Состояния для создания отчета за период"""
    waiting_for_start_date = State()  # Ожидание начальной даты
    waiting_for_end_date = State()    # Ожидание конечной даты

