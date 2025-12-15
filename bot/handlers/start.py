"""Обработчики команды /start"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from bot.keyboards.employee import get_employee_keyboard
from bot.keyboards.warehouseman import get_warehouseman_keyboard
from bot.keyboards.manager import get_manager_keyboard
from bot.config import get_config
from bot.services.marketing_service import marketing_service

router = Router(name="start")

def _build_test_link_line() -> str:
    """Вернуть строку с призывом протестировать бота, если задан BOT_PUBLIC_URL."""
    current_config = get_config()
    url = (current_config.bot_public_url or "").strip()
    if not url:
        return ""
    # Пытаемся сделать кликабельную ссылку, если это URL.
    if url.startswith("http://") or url.startswith("https://"):
        return f'\n\n🔗 <b><a href="{url}">Протестируйте бота</a></b>'
    # Иначе показываем как текст (@username тоже кликабелен в Telegram)
    return f"\n\n🔗 <b>Протестируйте бота:</b> {url}"


def get_welcome_message(role: str, name: str, is_demo: bool = False, days_left: int | None = None) -> str:
    """Получить приветственное сообщение в зависимости от роли"""
    
    # Демо-режим: добавляем информацию о тестовом периоде
    demo_info = ""
    if is_demo:
        if days_left is not None:
            if days_left > 0:
                demo_info = f"\n\n⏱️ <b>Тестовый период:</b> осталось {days_left} {_pluralize_days(days_left)}"
            else:
                demo_info = "\n\n⏱️ <b>Тестовый период истек</b>"
        else:
            demo_info = "\n\n⏱️ <b>Тестовый период:</b> 7 дней с момента первого входа"
    
    if role == "warehouseman":
        base_msg = (
            f"👋 Здравствуйте, {name}!\n\n"
            "Вы вошли как <b>Техник</b>.\n\n"
            "Вы можете:\n"
            "• Управлять заявками\n"
            "• Работать со складом\n"
            "• Делать рассылки пользователям\n\n"
            "Выберите действие из меню:"
        )
        return base_msg + demo_info
    elif role == "manager":
        base_msg = (
            f"👋 Здравствуйте, {name}!\n\n"
            "Добро пожаловать в <b>Housekeeper</b>!\n\n"
            "Вы вошли как <b>Руководитель</b>.\n\n"
            "<b>Что вы можете делать:</b>\n"
            "• Просматривать все заявки и отчеты\n"
            "• Назначать техников через «Управление техниками»\n"
            "• Переключаться между ролями (техник/пользователь/руководитель)\n"
            "• Управлять складом\n\n"
            "💡 <b>Совет:</b> добавьте техника, чтобы он мог обрабатывать ваши заявки.\n\n"
            "Выберите действие из меню:"
        )
        return base_msg + demo_info
    else:  # employee
        base_msg = (
            f"👋 Здравствуйте, {name}!\n\n"
            "Добро пожаловать в <b>Housekeeper</b>!\n\n"
            "Я помогу вам:\n"
            "• Создать заявку на материалы или работы\n"
            "• Отслеживать статус ваших заявок\n"
            "• Связаться с техником\n\n"
            "Выберите действие из меню:"
        )
        return base_msg + demo_info


def _pluralize_days(days: int) -> str:
    """Склонение слова 'день'"""
    if days % 10 == 1 and days % 100 != 11:
        return "день"
    elif days % 10 in [2, 3, 4] and days % 100 not in [12, 13, 14]:
        return "дня"
    else:
        return "дней"


@router.message(Command("start"))
async def cmd_start(message: Message, user_role: str, base_role: str, telegram_user, tenant_id: int, db_session):
    """Обработчик команды /start"""
    from datetime import datetime, timedelta
    from bot.database.models import User
    from sqlalchemy import select
    
    user_name = telegram_user.first_name or "Пользователь"

    # Маркетинговый трекинг + обновление профиля пользователя
    await marketing_service.track_start(db_session, tenant_id=tenant_id, telegram_user=telegram_user, message=message)
    
    # Определяем количество оставшихся дней (для демо-режима)
    current_config = get_config()
    days_left = None
    if current_config.demo_mode:
        result = await db_session.execute(
            select(User).where(User.id == telegram_user.id)
        )
        user = result.scalar_one_or_none()
        if user and user.first_seen_at:
            days_since = (datetime.now(user.first_seen_at.tzinfo) - user.first_seen_at).days
            days_left = max(0, 7 - days_since)
    
    # Получаем приветственное сообщение
    welcome_text = get_welcome_message(
        user_role, 
        user_name, 
        is_demo=current_config.demo_mode,
        days_left=days_left
    ) + _build_test_link_line()
    
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

