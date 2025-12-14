"""Планировщик задач для автоматических проверок"""
import asyncio
import logging
from datetime import datetime
from bot.services.automation_service import AutomationService
from bot.services.notification_service import NotificationService
from bot.config import get_config
from aiogram import Bot

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Планировщик задач для автоматических проверок"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.notification_service = NotificationService(bot)
        self.automation_service = AutomationService(self.notification_service)
        self.config = get_config()
        self.running = False
        self._task = None
        # Флаги для предотвращения повторных запусков
        self._warehouse_check_done = False
        self._daily_report_done = False
        self._old_requests_check_done = False
        self._last_hour = None
    
    async def start(self):
        """Запустить планировщик"""
        if self.running:
            logger.warning("Планировщик уже запущен")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("Планировщик задач запущен")
    
    async def stop(self):
        """Остановить планировщик"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Планировщик задач остановлен")
    
    async def _scheduler_loop(self):
        """Основной цикл планировщика"""
        while self.running:
            try:
                now = datetime.now()
                current_hour = now.hour
                current_minute = now.minute
                
                # Сброс флагов в начале нового дня
                if current_hour == 0 and current_minute == 0:
                    self._warehouse_check_done = False
                    self._daily_report_done = False
                    self._old_requests_check_done = False
                
                # Проверка минимума на складе (8:30)
                if current_hour == 8 and current_minute == 30 and not self._warehouse_check_done:
                    logger.info("Запуск проверки минимальных остатков на складе")
                    await self.automation_service.check_warehouse_minimum()
                    self._warehouse_check_done = True
                
                # Ежедневный отчет руководителю (9:00)
                if current_hour == 9 and current_minute == 0 and not self._daily_report_done:
                    logger.info("Отправка ежедневного отчета руководителю")
                    await self.automation_service.send_daily_report_to_manager()
                    self._daily_report_done = True
                
                # Проверка срочных заявок (каждый час в :00)
                if current_minute == 0 and self._last_hour != current_hour:
                    logger.info("Проверка срочных заявок")
                    await self.automation_service.check_urgent_requests()
                    self._last_hour = current_hour
                
                # Проверка заявок в работе >7 дней (каждый день в 10:00)
                if current_hour == 10 and current_minute == 0 and not self._old_requests_check_done:
                    logger.info("Проверка заявок в работе >7 дней")
                    await self.automation_service.check_old_in_progress_requests()
                    self._old_requests_check_done = True
                
                # Проверяем каждую минуту
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в планировщике задач: {e}")
                await asyncio.sleep(60)  # Ждем минуту перед следующей попыткой

