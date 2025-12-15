"""Сервис для работы со складом"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.database.models import WarehouseItem


class WarehouseService:
    """Сервис для управления складом"""
    
    async def get_all_items(self, session: AsyncSession, tenant_id: int) -> List[WarehouseItem]:
        """
        Получить все позиции на складе
        
        Args:
            session: Сессия БД
            
        Returns:
            Список всех позиций
        """
        result = await session.execute(
            select(WarehouseItem)
            .where(WarehouseItem.tenant_id == tenant_id)
            .order_by(WarehouseItem.name)
        )
        return list(result.scalars().all())
    
    async def get_item_by_id(
        self,
        session: AsyncSession,
        tenant_id: int,
        item_id: int
    ) -> Optional[WarehouseItem]:
        """
        Получить позицию по ID
        
        Args:
            session: Сессия БД
            item_id: ID позиции
            
        Returns:
            Позиция или None
        """
        result = await session.execute(
            select(WarehouseItem)
            .where(WarehouseItem.id == item_id)
            .where(WarehouseItem.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()
    
    async def get_item_by_name(
        self,
        session: AsyncSession,
        tenant_id: int,
        name: str
    ) -> Optional[WarehouseItem]:
        """
        Получить позицию по названию
        
        Args:
            session: Сессия БД
            name: Название позиции
            
        Returns:
            Позиция или None
        """
        result = await session.execute(
            select(WarehouseItem)
            .where(WarehouseItem.tenant_id == tenant_id)
            .where(WarehouseItem.name == name)
        )
        return result.scalar_one_or_none()
    
    async def create_item(
        self,
        session: AsyncSession,
        tenant_id: int,
        name: str,
        min_quantity: int = 0
    ) -> WarehouseItem:
        """
        Создать новую позицию на складе
        
        Args:
            session: Сессия БД
            name: Название позиции
            min_quantity: Минимальный остаток
            
        Returns:
            Созданная позиция
        """
        item = WarehouseItem(
            tenant_id=tenant_id,
            name=name,
            current_quantity=0,
            min_quantity=min_quantity
        )
        
        session.add(item)
        await session.commit()
        await session.refresh(item)
        
        return item
    
    async def add_quantity(
        self,
        session: AsyncSession,
        tenant_id: int,
        item_id: int,
        quantity: int
    ) -> Optional[WarehouseItem]:
        """
        Добавить количество к позиции
        
        Args:
            session: Сессия БД
            item_id: ID позиции
            quantity: Количество для добавления
            
        Returns:
            Обновленная позиция или None
        """
        item = await self.get_item_by_id(session, tenant_id=tenant_id, item_id=item_id)
        
        if not item:
            return None
        
        item.current_quantity += quantity
        
        await session.commit()
        await session.refresh(item)
        
        return item
    
    async def subtract_quantity(
        self,
        session: AsyncSession,
        tenant_id: int,
        item_id: int,
        quantity: int
    ) -> Optional[WarehouseItem]:
        """
        Списать количество с позиции
        
        Args:
            session: Сессия БД
            item_id: ID позиции
            quantity: Количество для списания
            
        Returns:
            Обновленная позиция или None (если недостаточно товара)
        """
        item = await self.get_item_by_id(session, tenant_id=tenant_id, item_id=item_id)
        
        if not item:
            return None
        
        if item.current_quantity < quantity:
            return None  # Недостаточно товара
        
        item.current_quantity -= quantity
        
        await session.commit()
        await session.refresh(item)
        
        return item
    
    async def update_min_quantity(
        self,
        session: AsyncSession,
        tenant_id: int,
        item_id: int,
        min_quantity: int
    ) -> Optional[WarehouseItem]:
        """
        Обновить минимальный остаток
        
        Args:
            session: Сессия БД
            item_id: ID позиции
            min_quantity: Новый минимальный остаток
            
        Returns:
            Обновленная позиция или None
        """
        item = await self.get_item_by_id(session, tenant_id=tenant_id, item_id=item_id)
        
        if not item:
            return None
        
        item.min_quantity = min_quantity
        
        await session.commit()
        await session.refresh(item)
        
        return item
    
    async def get_low_stock_items(self, session: AsyncSession, tenant_id: int) -> List[WarehouseItem]:
        """
        Получить позиции с остатком <= минимального
        
        Args:
            session: Сессия БД
            
        Returns:
            Список позиций с низким остатком
        """
        result = await session.execute(
            select(WarehouseItem)
            .where(WarehouseItem.tenant_id == tenant_id)
            .where(WarehouseItem.current_quantity <= WarehouseItem.min_quantity)
            .order_by(WarehouseItem.name)
        )
        return list(result.scalars().all())


# Глобальный экземпляр сервиса
warehouse_service = WarehouseService()

