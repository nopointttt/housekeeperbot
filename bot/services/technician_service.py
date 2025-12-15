"""Сервис для управления техниками (назначение техников руководителям)"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from bot.database.models import TechnicianAssignment, User
from aiogram import Bot
from bot.services.role_service import role_service


class TechnicianService:
    """Сервис для управления назначением техников руководителям"""
    
    async def add_technician(
        self,
        session: AsyncSession,
        manager_id: int,
        technician_id: int,
        bot: Bot
    ) -> tuple[bool, str]:
        """
        Назначить техника руководителю
        
        Args:
            session: Сессия БД
            manager_id: ID руководителя (Telegram ID, используется как tenant_id)
            technician_id: ID техника (Telegram ID)
            bot: Экземпляр бота для получения информации о пользователе
            
        Returns:
            Tuple (успех, сообщение)
        """
        # Проверяем, что техник существует
        result = await session.execute(
            select(User).where(User.id == technician_id)
        )
        technician = result.scalar_one_or_none()
        
        if not technician:
            return False, "Пользователь не найден в системе"
        
        # Проверяем, что техник не является самим руководителем
        if technician_id == manager_id:
            return False, "Нельзя назначить себя техником"
        
        # Проверяем, что назначение еще не существует
        result = await session.execute(
            select(TechnicianAssignment).where(
                and_(
                    TechnicianAssignment.manager_id == manager_id,
                    TechnicianAssignment.technician_id == technician_id
                )
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return False, "Этот техник уже назначен вам"
        
        # Создаем назначение
        assignment = TechnicianAssignment(
            manager_id=manager_id,
            technician_id=technician_id
        )
        session.add(assignment)
        await session.flush()
        
        # Обновляем роль пользователя на warehouseman (приоритетно)
        # Это отменяет предыдущий статус руководителя
        tech_user = await role_service.get_or_create_user(session, technician_id)
        if tech_user.role != "warehouseman":
            tech_user.role = "warehouseman"
            tech_user.active_role = None  # Сбрасываем active_role, т.к. техник не может быть менеджером
            await session.flush()
        
        # Получаем имя техника для сообщения
        try:
            chat = await bot.get_chat(technician_id)
            tech_name = chat.first_name or chat.username or f"ID: {technician_id}"
        except:
            tech_name = f"ID: {technician_id}"
        
        return True, f"Техник {tech_name} успешно назначен. Он теперь работает с вашими заявками и складом."
    
    async def remove_technician(
        self,
        session: AsyncSession,
        manager_id: int,
        technician_id: int,
        bot: Bot
    ) -> tuple[bool, str]:
        """
        Удалить назначение техника
        
        Args:
            session: Сессия БД
            manager_id: ID руководителя
            technician_id: ID техника
            bot: Экземпляр бота для получения информации о пользователе
            
        Returns:
            Tuple (успех, сообщение)
        """
        result = await session.execute(
            select(TechnicianAssignment).where(
                and_(
                    TechnicianAssignment.manager_id == manager_id,
                    TechnicianAssignment.technician_id == technician_id
                )
            )
        )
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            return False, "Назначение не найдено"
        
        # Получаем имя техника для сообщения
        try:
            chat = await bot.get_chat(technician_id)
            tech_name = chat.first_name or chat.username or f"ID: {technician_id}"
        except:
            tech_name = f"ID: {technician_id}"
        
        await session.delete(assignment)
        await session.flush()
        
        return True, f"Техник {tech_name} удален из списка"
    
    async def get_technicians(
        self,
        session: AsyncSession,
        manager_id: int,
        bot: Bot
    ) -> List[tuple[int, str]]:
        """
        Получить список техников руководителя
        
        Args:
            session: Сессия БД
            manager_id: ID руководителя
            bot: Экземпляр бота для получения информации о пользователях
            
        Returns:
            Список tuple (technician_id, name)
        """
        result = await session.execute(
            select(TechnicianAssignment).where(
                TechnicianAssignment.manager_id == manager_id
            )
        )
        assignments = list(result.scalars().all())
        
        technicians = []
        for assignment in assignments:
            try:
                chat = await bot.get_chat(assignment.technician_id)
                name = chat.first_name or chat.username or f"ID: {assignment.technician_id}"
            except:
                name = f"ID: {assignment.technician_id}"
            technicians.append((assignment.technician_id, name))
        
        return technicians
    
    async def is_technician_assigned(
        self,
        session: AsyncSession,
        technician_id: int,
        manager_id: int
    ) -> bool:
        """
        Проверить, назначен ли техник руководителю
        
        Args:
            session: Сессия БД
            technician_id: ID техника
            manager_id: ID руководителя
            
        Returns:
            True если назначен
        """
        result = await session.execute(
            select(TechnicianAssignment).where(
                and_(
                    TechnicianAssignment.manager_id == manager_id,
                    TechnicianAssignment.technician_id == technician_id
                )
            )
        )
        return result.scalar_one_or_none() is not None


# Глобальный экземпляр сервиса
technician_service = TechnicianService()

