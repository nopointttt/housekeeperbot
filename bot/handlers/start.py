"""Обработчики команды /start"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from bot.keyboards.employee import get_employee_keyboard
from bot.keyboards.warehouseman import get_warehouseman_keyboard
from bot.keyboards.manager import get_manager_keyboard

router = Router(name="start")


def get_welcome_message(role: str, name: str) -> str:
    """Получить приветственное сообщение в зависимости от роли"""
    
    if role == "warehouseman":
        return (
            f"👋 Здравствуйте, {name}!\n\n"
            "Вы вошли как <b>Завхоз</b>.\n\n"
            "Вы можете:\n"
            "• Управлять заявками\n"
            "• Работать со складом\n"
            "• Делать рассылки сотрудникам\n"
            "• Настраивать бота\n\n"
            "Выберите действие из меню:"
        )
    elif role == "manager":
        return (
            f"👋 Здравствуйте, {name}!\n\n"
            "Вы вошли как <b>Руководитель</b>.\n\n"
            "Вы можете:\n"
            "• Просматривать заявки и отчеты\n"
            "• Читать жалобы на завхоза\n"
            "• Получать автоматические уведомления\n\n"
            "Выберите действие из меню:"
        )
    else:  # employee
        return (
            f"👋 Здравствуйте, {name}!\n\n"
            "Добро пожаловать в бота <b>Завхоз</b>!\n\n"
            "Я помогу вам:\n"
            "• Создать заявку на материалы или работы\n"
            "• Отслеживать статус ваших заявок\n"
            "• Связаться с завхозом\n\n"
            "Выберите действие из меню:"
        )


@router.message(Command("start"))
async def cmd_start(message: Message, user_role: str, base_role: str, telegram_user, db_session):
    """Обработчик команды /start"""
    user_name = telegram_user.first_name or "Пользователь"
    
    # Получаем приветственное сообщение
    welcome_text = get_welcome_message(user_role, user_name)
    
    # Получаем клавиатуру в зависимости от роли
    # Если менеджер переключился на другую роль, показываем соответствующую клавиатуру с кнопкой возврата
    if user_role == "warehouseman":
        keyboard = get_warehouseman_keyboard(is_manager=(base_role == "manager"))
    elif user_role == "manager":
        keyboard = get_manager_keyboard()
    else:  # employee
        keyboard = get_employee_keyboard(is_manager=(base_role == "manager"))
    
    await message.answer(
        welcome_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

