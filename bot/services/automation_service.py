"""Сервис для автоматических проверок и уведомлений"""
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from bot.services.warehouse_service import warehouse_service
from bot.services.manager_service import manager_service
from bot.services.notification_service import NotificationService
from bot.database.engine import async_session_maker


class AutomationService:
    """Сервис для автоматических проверок и уведомлений"""
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
    
    async def check_warehouse_minimum(self):
        """
        Проверить минимальные остатки на складе и уведомить завхоза
        
        Вызывается ежедневно в 8:30
        """
        async with async_session_maker() as session:
            try:
                low_stock_items = await warehouse_service.get_low_stock_items(session)
                
                if not low_stock_items:
                    return  # Нет позиций с низким остатком
                
                from bot.config import get_config
                config = get_config()
                
                text = "⚠️ <b>Напоминание: низкие остатки на складе</b>\n\n"
                text += "Следующие позиции требуют пополнения:\n\n"
                
                for item in low_stock_items:
                    text += f"📦 <b>{item.name}</b>\n"
                    text += f"   Текущий остаток: {item.current_quantity}\n"
                    text += f"   Минимальный: {item.min_quantity}\n\n"
                
                try:
                    await self.notification_service.bot.send_message(
                        chat_id=config.warehouseman_id,
                        text=text,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"Ошибка отправки уведомления о низких остатках: {e}")
            except Exception as e:
                print(f"Ошибка проверки минимальных остатков: {e}")
    
    async def send_daily_report_to_manager(self):
        """
        Отправить ежедневный отчет руководителю за предыдущий день
        
        Вызывается ежедневно в 9:00
        """
        async with async_session_maker() as session:
            try:
                # Получаем вчерашний день
                yesterday = datetime.now() - timedelta(days=1)
                start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                # Получаем отчет за вчера
                report = await manager_service.get_period_report(session, start_date, end_date)
                
                from bot.config import get_config
                config = get_config()
                
                date_str = yesterday.strftime("%d.%m.%Y")
                
                text = f"📊 <b>Ежедневный отчет за {date_str}</b>\n\n"
                text += f"📋 <b>Статистика:</b>\n"
                text += f"• Новые: {report['new']}\n"
                text += f"• В работе: {report['in_progress']}\n"
                text += f"• Выполнено: {report['completed']}\n"
                text += f"• Отклонено: {report['rejected']}\n"
                text += f"• <b>Всего:</b> {report['total']}\n"
                
                try:
                    await self.notification_service.bot.send_message(
                        chat_id=config.manager_id,
                        text=text,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"Ошибка отправки ежедневного отчета: {e}")
            except Exception as e:
                print(f"Ошибка генерации ежедневного отчета: {e}")
    
    async def check_urgent_requests(self):
        """
        Проверить срочные заявки, которые висят "Новая" > 2 часов
        
        Уведомляет руководителя
        """
        async with async_session_maker() as session:
            try:
                # Получаем все новые срочные заявки
                from sqlalchemy import select, and_
                from sqlalchemy.orm import selectinload
                from bot.database.models import Request
                
                two_hours_ago = datetime.now() - timedelta(hours=2)
                
                result = await session.execute(
                    select(Request)
                    .where(
                        and_(
                            Request.status == "new",
                            Request.priority == "urgent",
                            Request.created_at <= two_hours_ago
                        )
                    )
                    .options(selectinload(Request.user))
                    .order_by(Request.created_at.asc())
                )
                
                urgent_requests = list(result.scalars().all())
                
                if not urgent_requests:
                    return  # Нет срочных заявок старше 2 часов
                
                from bot.config import get_config
                config = get_config()
                
                text = "🚨 <b>Внимание: срочные заявки без обработки</b>\n\n"
                text += f"Найдено {len(urgent_requests)} срочных заявок, которые не обработаны более 2 часов:\n\n"
                
                for request in urgent_requests:
                    hours_ago = (datetime.now() - request.created_at).total_seconds() / 3600
                    text += f"📋 <b>{request.number}</b>\n"
                    text += f"   Категория: {request.category}\n"
                    text += f"   Создана: {request.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    text += f"   Прошло: {int(hours_ago)} ч.\n\n"
                
                try:
                    await self.notification_service.bot.send_message(
                        chat_id=config.manager_id,
                        text=text,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"Ошибка отправки уведомления о срочных заявках: {e}")
            except Exception as e:
                print(f"Ошибка проверки срочных заявок: {e}")
    
    async def check_old_in_progress_requests(self):
        """
        Проверить заявки в работе > 7 дней
        
        Уведомляет руководителя
        """
        async with async_session_maker() as session:
            try:
                old_requests = await manager_service.get_requests_in_work_over_days(session, days=7)
                
                if not old_requests:
                    return  # Нет заявок в работе более 7 дней
                
                from bot.config import get_config
                config = get_config()
                
                text = "⏰ <b>Внимание: заявки в работе более 7 дней</b>\n\n"
                text += f"Найдено {len(old_requests)} заявок, которые находятся в работе более 7 дней:\n\n"
                
                for request in old_requests:
                    days_ago = (datetime.now() - request.updated_at).days
                    text += f"📋 <b>{request.number}</b>\n"
                    text += f"   Категория: {request.category}\n"
                    text += f"   Взята в работу: {request.updated_at.strftime('%d.%m.%Y %H:%M')}\n"
                    text += f"   Прошло: {days_ago} дн.\n\n"
                
                try:
                    await self.notification_service.bot.send_message(
                        chat_id=config.manager_id,
                        text=text,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    print(f"Ошибка отправки уведомления о старых заявках: {e}")
            except Exception as e:
                print(f"Ошибка проверки старых заявок: {e}")

