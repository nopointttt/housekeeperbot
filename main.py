"""Точка входа в приложение"""
import asyncio
import logging
import traceback
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from bot.config import config
from bot.database.engine import init_db, close_db

# Настройка логирования с полными трейсбеками
log_level = getattr(logging, config.log_level.upper())
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Включаем дебаг для aiogram только в DEBUG режиме
if log_level == logging.DEBUG:
    logging.getLogger('aiogram').setLevel(logging.DEBUG)
    logging.getLogger('aiogram.event').setLevel(logging.DEBUG)
else:
    # В production режиме уменьшаем уровень логирования aiogram
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('aiogram.event').setLevel(logging.WARNING)


async def main():
    """Основная функция запуска бота"""
    logger.info("Запуск бота 'Завхоз'...")
    
    # Инициализация бота и диспетчера
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Инициализация базы данных
    try:
        await init_db()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        return
    
    # Регистрация middleware
    from bot.middlewares.role_middleware import RoleMiddleware
    dp.message.middleware(RoleMiddleware())
    dp.callback_query.middleware(RoleMiddleware())
    
    # Регистрация routers (handlers)
    from bot.handlers import start, common, settings, request_creation, employee, complaints, warehouseman, warehouse, warehouse_writeoff, broadcast, manager, technicians
    
    dp.include_router(start.router)
    dp.include_router(common.router)
    dp.include_router(settings.router)
    dp.include_router(request_creation.router)
    dp.include_router(employee.router)
    dp.include_router(complaints.router)
    dp.include_router(warehouseman.router)
    dp.include_router(warehouse.router)
    dp.include_router(warehouse_writeoff.router)
    dp.include_router(broadcast.router)
    dp.include_router(manager.router)
    dp.include_router(technicians.router)
    
    # Запуск планировщика задач
    from bot.services.scheduler import TaskScheduler
    scheduler = TaskScheduler(bot)
    await scheduler.start()
    
    # Запуск polling
    try:
        logger.info("Бот запущен")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
        logger.error(f"Трейсбек: {traceback.format_exc()}")
    finally:
        await scheduler.stop()
        await close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

