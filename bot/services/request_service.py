"""Сервис для работы с заявками"""
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from bot.database.models import Request, RequestPhoto, User
from bot.utils.request_helpers import generate_request_number


class RequestService:
    """Сервис для управления заявками"""
    
    async def generate_request_number(self, session: AsyncSession) -> str:
        """
        Сгенерировать уникальный номер заявки ЗХ-ДДММГГ-№№№
        
        Глобально уникальный номер (не зависит от пользователя).
        При конфликте (одновременные запросы) повторяет генерацию.
        
        Args:
            session: Сессия БД
            
        Returns:
            Полный номер заявки (например, ЗХ-271125-001)
        """
        from sqlalchemy.exc import IntegrityError
        
        today = datetime.now()
        date_prefix = generate_request_number(today)
        today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Пытаемся сгенерировать номер до 10 раз (на случай конфликтов)
        max_attempts = 10
        for attempt in range(max_attempts):
            # Найти все заявки за сегодня с таким префиксом
            result = await session.execute(
                select(func.count(Request.id))
                .where(Request.created_at >= today_start)
                .where(Request.number.like(f"{date_prefix}-%"))
            )
            
            count = result.scalar() or 0
            sequence_number = count + 1
            number = f"{date_prefix}-{sequence_number:03d}"
            
            # Проверяем, что такого номера еще нет (на случай race condition)
            existing = await session.execute(
                select(Request.id).where(Request.number == number)
            )
            if existing.scalar_one_or_none() is None:
                # Номер свободен, возвращаем
                return number
            
            # Номер занят (race condition), пробуем еще раз
            # Сначала делаем flush чтобы увидеть последние изменения
            await session.flush()
        
        # Если все попытки неудачны, используем timestamp для гарантированной уникальности
        import time
        timestamp_suffix = str(int(time.time()))[-6:]  # Последние 6 цифр timestamp
        return f"{date_prefix}-{timestamp_suffix}"
    
    async def create_request(
        self,
        session: AsyncSession,
        user_id: int,
        category: str,
        description: str,
        priority: str,
        quantity: Optional[int] = None,
        photo_file_ids: Optional[list[str]] = None
    ) -> Request:
        """
        Создать новую заявку
        
        Args:
            session: Сессия БД
            user_id: Telegram ID пользователя
            category: Категория заявки
            description: Описание
            priority: Приоритет ('normal' or 'urgent')
            quantity: Количество (опционально)
            photo_file_ids: Список Telegram file_id фото (опционально)
            
        Returns:
            Созданная заявка
        """
        # Генерируем номер
        number = await self.generate_request_number(session)
        
        # Создаем заявку
        request = Request(
            number=number,
            user_id=user_id,
            category=category,
            description=description,
            quantity=quantity,
            priority=priority,
            status="new"
        )
        
        session.add(request)
        await session.flush()  # Получаем ID заявки
        
        # Добавляем фото если есть
        photos_count = 0
        if photo_file_ids:
            photos_count = len(photo_file_ids)
            for file_id in photo_file_ids:
                photo = RequestPhoto(
                    request_id=request.id,
                    file_id=file_id
                )
                session.add(photo)
            await session.flush()  # Сохраняем фото, но не коммитим
        
        # Загружаем фото ДО коммита, пока сессия активна, чтобы извлечь file_ids
        photo_file_ids = []
        if photos_count > 0:
            # Обновляем request с photos в текущей сессии
            await session.refresh(request, ['photos'])
            # Извлекаем file_ids пока сессия активна
            photo_file_ids = [photo.file_id for photo in request.photos] if request.photos else []
        
        await session.commit()
        
        # Сохраняем file_ids в объекте request для использования после коммита
        # Это безопасный способ избежать lazy loading после закрытия сессии
        if photo_file_ids:
            request._cached_photo_file_ids = photo_file_ids
        
        return request
    
    async def get_user_requests(
        self,
        session: AsyncSession,
        user_id: int,
        limit: Optional[int] = None
    ) -> list[Request]:
        """
        Получить заявки пользователя
        
        Args:
            session: Сессия БД
            user_id: Telegram ID пользователя
            limit: Максимальное количество заявок
            
        Returns:
            Список заявок пользователя
        """
        query = (
            select(Request)
            .where(Request.user_id == user_id)
            .options(selectinload(Request.photos))
            .order_by(Request.created_at.desc())
        )
        
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        return list(result.scalars().all())
    
    async def get_request_by_id(
        self,
        session: AsyncSession,
        request_id: int,
        load_user: bool = True,
        load_photos: bool = True
    ) -> Optional[Request]:
        """
        Получить заявку по ID
        
        Args:
            session: Сессия БД
            request_id: ID заявки
            load_user: Загружать связанного пользователя (по умолчанию True)
            load_photos: Загружать фото (по умолчанию True)
        """
        query = select(Request).where(Request.id == request_id)
        
        # Оптимизация: загружаем только то, что нужно
        options = []
        if load_photos:
            options.append(selectinload(Request.photos))
        if load_user:
            options.append(selectinload(Request.user))
        
        if options:
            query = query.options(*options)
        
        result = await session.execute(query)
        return result.scalar_one_or_none()


# Глобальный экземпляр сервиса
request_service = RequestService()

