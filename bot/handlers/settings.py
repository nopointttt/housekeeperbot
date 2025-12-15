"""Обработчики настроек (для техника)"""
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from bot.keyboards.warehouseman import get_warehouseman_keyboard
from bot.config import get_config

router = Router(name="settings")


@router.message(Command("settings"))
@router.message(F.text == "Настройки")
async def cmd_settings(message: Message, user_role: str, base_role: str):
    """Обработчик команды /settings (только для техника)"""
    
    if user_role != "warehouseman":
        await message.answer("❌ У вас нет доступа к настройкам. Эта функция доступна только технику.")
        return
    
    config = get_config()
    
    settings_text = (
        "<b>⚙️ Настройки бота</b>\n\n"
        f"<b>ID техника:</b> {config.warehouseman_id}\n"
        f"<b>ID руководителя:</b> {config.manager_id}\n"
        f"<b>Часовой пояс:</b> {config.timezone}\n"
        f"<b>Уровень логирования:</b> {config.log_level}\n\n"
        "<b>Как изменить настройки:</b>\n"
        "1. Откройте файл <code>.env</code> в корне проекта\n"
        "2. Измените нужные значения:\n"
        "   • <code>WAREHOUSEMAN_ID</code> - ID техника\n"
        "   • <code>MANAGER_ID</code> - ID руководителя\n"
        "   • <code>TIMEZONE</code> - часовой пояс\n"
        "   • <code>LOG_LEVEL</code> - уровень логирования\n"
        "3. Перезапустите бота\n\n"
        "<i>Примечание: Для изменения ID ролей требуется перезапуск бота.</i>"
    )
    
    await message.answer(
        settings_text,
        reply_markup=get_warehouseman_keyboard(is_manager=(base_role == "manager")),
        parse_mode="HTML",
    )

