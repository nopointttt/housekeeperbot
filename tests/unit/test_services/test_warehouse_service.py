"""
Unit тесты для WarehouseService

Тестируемые методы:
- get_all_items() - получение всех позиций
- get_item_by_id() - получение по ID
- get_item_by_name() - получение по названию
- create_item() - создание позиции
- add_quantity() - добавление количества
- subtract_quantity() - списание
- update_min_quantity() - обновление минимума
- get_low_stock_items() - позиции с низким остатком
"""
import pytest
from sqlalchemy import select

from bot.services.warehouse_service import WarehouseService, warehouse_service
from bot.database.models import WarehouseItem


class TestWarehouseServiceGetAll:
    """Тесты получения всех позиций"""
    
    @pytest.mark.asyncio
    async def test_get_all_items_empty(self, test_session):
        """Пустой склад возвращает пустой список"""
        service = WarehouseService()
        
        items = await service.get_all_items(test_session)
        
        assert items == []
    
    @pytest.mark.asyncio
    async def test_get_all_items_returns_all(self, test_session, test_warehouse_items):
        """Возвращает все позиции"""
        service = WarehouseService()
        
        items = await service.get_all_items(test_session)
        
        assert len(items) == 5
    
    @pytest.mark.asyncio
    async def test_get_all_items_ordered_by_name(self, test_session):
        """Позиции отсортированы по названию"""
        service = WarehouseService()
        
        # Создаем позиции в "неправильном" порядке
        test_session.add(WarehouseItem(name="Яблоки", current_quantity=10, min_quantity=5))
        test_session.add(WarehouseItem(name="Апельсины", current_quantity=20, min_quantity=5))
        test_session.add(WarehouseItem(name="Бананы", current_quantity=15, min_quantity=5))
        await test_session.flush()
        
        items = await service.get_all_items(test_session)
        
        # Должны быть отсортированы: Апельсины, Бананы, Яблоки
        assert items[0].name == "Апельсины"
        assert items[1].name == "Бананы"
        assert items[2].name == "Яблоки"


class TestWarehouseServiceGetById:
    """Тесты получения по ID"""
    
    @pytest.mark.asyncio
    async def test_get_item_by_id_exists(self, test_session, test_warehouse_item):
        """Получение существующей позиции"""
        service = WarehouseService()
        
        item = await service.get_item_by_id(test_session, test_warehouse_item.id)
        
        assert item is not None
        assert item.id == test_warehouse_item.id
        assert item.name == test_warehouse_item.name
    
    @pytest.mark.asyncio
    async def test_get_item_by_id_not_exists(self, test_session):
        """Несуществующая позиция возвращает None"""
        service = WarehouseService()
        
        item = await service.get_item_by_id(test_session, 99999)
        
        assert item is None


class TestWarehouseServiceGetByName:
    """Тесты получения по названию"""
    
    @pytest.mark.asyncio
    async def test_get_item_by_name_exists(self, test_session):
        """Получение по точному названию"""
        service = WarehouseService()
        
        # Создаем позицию
        item = WarehouseItem(name="Уникальный товар", current_quantity=10, min_quantity=5)
        test_session.add(item)
        await test_session.flush()
        
        found = await service.get_item_by_name(test_session, "Уникальный товар")
        
        assert found is not None
        assert found.name == "Уникальный товар"
    
    @pytest.mark.asyncio
    async def test_get_item_by_name_not_exists(self, test_session):
        """Несуществующее название возвращает None"""
        service = WarehouseService()
        
        found = await service.get_item_by_name(test_session, "Несуществующий товар")
        
        assert found is None
    
    @pytest.mark.asyncio
    async def test_get_item_by_name_case_sensitive(self, test_session):
        """Поиск чувствителен к регистру"""
        service = WarehouseService()
        
        item = WarehouseItem(name="Бумага А4", current_quantity=10, min_quantity=5)
        test_session.add(item)
        await test_session.flush()
        
        # Точное совпадение
        found_exact = await service.get_item_by_name(test_session, "Бумага А4")
        assert found_exact is not None
        
        # Другой регистр
        found_lower = await service.get_item_by_name(test_session, "бумага а4")
        assert found_lower is None


class TestWarehouseServiceCreate:
    """Тесты создания позиции"""
    
    @pytest.mark.asyncio
    async def test_create_item(self, test_session):
        """Создание новой позиции"""
        service = WarehouseService()
        
        item = await service.create_item(
            test_session,
            name="Новый товар",
            min_quantity=10
        )
        
        assert item is not None
        assert item.id is not None
        assert item.name == "Новый товар"
        assert item.current_quantity == 0  # По умолчанию 0
        assert item.min_quantity == 10
    
    @pytest.mark.asyncio
    async def test_create_item_default_min_quantity(self, test_session):
        """Создание с минимумом по умолчанию (0)"""
        service = WarehouseService()
        
        item = await service.create_item(test_session, name="Товар без минимума")
        
        assert item.min_quantity == 0
    
    @pytest.mark.asyncio
    async def test_create_item_saves_to_db(self, test_session):
        """Позиция сохраняется в БД"""
        service = WarehouseService()
        
        created = await service.create_item(test_session, name="Сохраненный товар")
        
        # Проверяем в БД
        result = await test_session.execute(
            select(WarehouseItem).where(WarehouseItem.id == created.id)
        )
        found = result.scalar_one_or_none()
        
        assert found is not None
        assert found.name == "Сохраненный товар"


class TestWarehouseServiceQuantity:
    """Тесты работы с количеством"""
    
    @pytest.mark.asyncio
    async def test_add_quantity(self, test_session, test_warehouse_item):
        """Добавление количества"""
        service = WarehouseService()
        initial_qty = test_warehouse_item.current_quantity
        
        updated = await service.add_quantity(test_session, test_warehouse_item.id, 50)
        
        assert updated is not None
        assert updated.current_quantity == initial_qty + 50
    
    @pytest.mark.asyncio
    async def test_add_quantity_to_nonexistent(self, test_session):
        """Добавление к несуществующей позиции возвращает None"""
        service = WarehouseService()
        
        result = await service.add_quantity(test_session, 99999, 10)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_subtract_quantity_success(self, test_session):
        """Успешное списание количества"""
        service = WarehouseService()
        
        # Создаем позицию с достаточным количеством
        item = WarehouseItem(name="Товар для списания", current_quantity=100, min_quantity=5)
        test_session.add(item)
        await test_session.flush()
        
        updated = await service.subtract_quantity(test_session, item.id, 30)
        
        assert updated is not None
        assert updated.current_quantity == 70
    
    @pytest.mark.asyncio
    async def test_subtract_quantity_insufficient(self, test_session):
        """Списание больше чем есть возвращает None"""
        service = WarehouseService()
        
        item = WarehouseItem(name="Мало товара", current_quantity=10, min_quantity=5)
        test_session.add(item)
        await test_session.flush()
        
        result = await service.subtract_quantity(test_session, item.id, 20)
        
        assert result is None
        
        # Количество не изменилось
        refreshed = await service.get_item_by_id(test_session, item.id)
        assert refreshed.current_quantity == 10
    
    @pytest.mark.asyncio
    async def test_subtract_quantity_exact(self, test_session):
        """Списание ровно столько сколько есть - успешно"""
        service = WarehouseService()
        
        item = WarehouseItem(name="Точное списание", current_quantity=50, min_quantity=5)
        test_session.add(item)
        await test_session.flush()
        
        updated = await service.subtract_quantity(test_session, item.id, 50)
        
        assert updated is not None
        assert updated.current_quantity == 0
    
    @pytest.mark.asyncio
    async def test_subtract_quantity_to_nonexistent(self, test_session):
        """Списание с несуществующей позиции возвращает None"""
        service = WarehouseService()
        
        result = await service.subtract_quantity(test_session, 99999, 10)
        
        assert result is None


class TestWarehouseServiceMinQuantity:
    """Тесты работы с минимальным остатком"""
    
    @pytest.mark.asyncio
    async def test_update_min_quantity(self, test_session, test_warehouse_item):
        """Обновление минимального остатка"""
        service = WarehouseService()
        
        updated = await service.update_min_quantity(test_session, test_warehouse_item.id, 25)
        
        assert updated is not None
        assert updated.min_quantity == 25
    
    @pytest.mark.asyncio
    async def test_update_min_quantity_nonexistent(self, test_session):
        """Обновление несуществующей позиции возвращает None"""
        service = WarehouseService()
        
        result = await service.update_min_quantity(test_session, 99999, 10)
        
        assert result is None


class TestWarehouseServiceLowStock:
    """Тесты проверки низкого остатка"""
    
    @pytest.mark.asyncio
    async def test_get_low_stock_items_empty(self, test_session):
        """Нет позиций с низким остатком"""
        service = WarehouseService()
        
        # Создаем позиции с достаточным количеством
        test_session.add(WarehouseItem(name="Много товара", current_quantity=100, min_quantity=10))
        await test_session.flush()
        
        low_stock = await service.get_low_stock_items(test_session)
        
        assert low_stock == []
    
    @pytest.mark.asyncio
    async def test_get_low_stock_items_returns_low(self, test_session, test_low_stock_items):
        """Возвращает позиции с остатком <= минимума"""
        service = WarehouseService()
        
        low_stock = await service.get_low_stock_items(test_session)
        
        # Должны быть все 3 позиции из fixture
        assert len(low_stock) == 3
    
    @pytest.mark.asyncio
    async def test_get_low_stock_items_exact_minimum(self, test_session):
        """Позиция с остатком = минимуму включается"""
        service = WarehouseService()
        
        item = WarehouseItem(name="На минимуме", current_quantity=10, min_quantity=10)
        test_session.add(item)
        await test_session.flush()
        
        low_stock = await service.get_low_stock_items(test_session)
        
        assert len(low_stock) == 1
        assert low_stock[0].name == "На минимуме"
    
    @pytest.mark.asyncio
    async def test_get_low_stock_items_zero_quantity(self, test_session):
        """Позиция с нулевым остатком включается"""
        service = WarehouseService()
        
        item = WarehouseItem(name="Закончился", current_quantity=0, min_quantity=5)
        test_session.add(item)
        await test_session.flush()
        
        low_stock = await service.get_low_stock_items(test_session)
        
        assert len(low_stock) == 1
        assert low_stock[0].current_quantity == 0


class TestWarehouseServiceEdgeCases:
    """Edge cases"""
    
    @pytest.mark.asyncio
    async def test_add_zero_quantity(self, test_session, test_warehouse_item):
        """Добавление нуля не меняет количество"""
        service = WarehouseService()
        initial_qty = test_warehouse_item.current_quantity
        
        updated = await service.add_quantity(test_session, test_warehouse_item.id, 0)
        
        assert updated.current_quantity == initial_qty
    
    @pytest.mark.asyncio
    async def test_subtract_zero_quantity(self, test_session):
        """Списание нуля - успешно, количество не меняется"""
        service = WarehouseService()
        
        item = WarehouseItem(name="Тест нуля", current_quantity=50, min_quantity=5)
        test_session.add(item)
        await test_session.flush()
        
        updated = await service.subtract_quantity(test_session, item.id, 0)
        
        assert updated is not None
        assert updated.current_quantity == 50

