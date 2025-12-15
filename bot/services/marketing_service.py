"""Сервис для маркетингового трекинга (onboarding, аналитика)"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from aiogram.types import Message, User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.database.models import User, UserEvent


class MarketingService:
    """Сервис для трекинга /start и профиля пользователя."""

    async def track_start(
        self,
        session: AsyncSession,
        tenant_id: int,
        telegram_user: TelegramUser,
        message: Message,
    ) -> None:
        """Сохранить максимум доступной информации о пользователе и событие /start."""

        user_id = telegram_user.id

        # Upsert пользователя
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        now = datetime.now()

        if user is None:
            # В обычном потоке пользователя уже создаёт RoleMiddleware,
            # но на всякий случай делаем fallback.
            user = User(id=user_id, role="employee")
            session.add(user)
            await session.flush()

        # Обновляем профиль
        user.username = telegram_user.username
        user.first_name = telegram_user.first_name
        user.last_name = telegram_user.last_name
        user.language_code = getattr(telegram_user, "language_code", None)
        user.is_premium = bool(getattr(telegram_user, "is_premium", False))
        user.last_seen_at = now
        if user.first_seen_at is None:
            user.first_seen_at = now

        # Парсим payload (/start <payload>)
        start_payload: str | None = None
        try:
            text = (message.text or "").strip()
            if text.startswith("/start"):
                parts = text.split(maxsplit=1)
                if len(parts) == 2:
                    start_payload = parts[1].strip() or None
        except Exception:
            start_payload = None

        payload: dict[str, Any] = {
            "start_payload": start_payload,
            "chat_id": message.chat.id if message.chat else None,
            "chat_type": getattr(message.chat, "type", None) if message.chat else None,
            "chat_title": getattr(message.chat, "title", None) if message.chat else None,
        }

        session.add(
            UserEvent(
                tenant_id=tenant_id,
                user_id=user_id,
                event_type="start",
                payload=payload,
            )
        )


marketing_service = MarketingService()


