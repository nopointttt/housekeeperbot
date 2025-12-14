"""
Unit тесты для request_helpers

Тестируемые функции и классы:
- generate_request_number() - генерация префикса номера заявки
- RequestCreationData - dataclass для данных создания заявки
"""
import pytest
from datetime import datetime
from bot.utils.request_helpers import generate_request_number, RequestCreationData


class TestGenerateRequestNumber:
    """Тесты генерации номера заявки"""
    
    def test_generate_request_number_format(self):
        """Проверка формата ЗХ-ДДММГГ"""
        date = datetime(2025, 1, 15)
        
        result = generate_request_number(date)
        
        assert result == "ЗХ-150125"
    
    def test_generate_request_number_with_current_date(self):
        """Генерация с текущей датой"""
        result = generate_request_number()
        
        today = datetime.now()
        expected = f"ЗХ-{today.day:02d}{today.month:02d}{today.year % 100:02d}"
        
        assert result == expected
    
    def test_generate_request_number_single_digit_day(self):
        """Дни с одной цифрой дополняются нулем"""
        date = datetime(2025, 3, 5)
        
        result = generate_request_number(date)
        
        assert result == "ЗХ-050325"
    
    def test_generate_request_number_single_digit_month(self):
        """Месяцы с одной цифрой дополняются нулем"""
        date = datetime(2025, 1, 15)
        
        result = generate_request_number(date)
        
        assert result == "ЗХ-150125"
    
    def test_generate_request_number_december(self):
        """Декабрь (месяц 12)"""
        date = datetime(2025, 12, 25)
        
        result = generate_request_number(date)
        
        assert result == "ЗХ-251225"
    
    def test_generate_request_number_year_2025(self):
        """Год 2025 -> 25"""
        date = datetime(2025, 6, 15)
        
        result = generate_request_number(date)
        
        assert result.endswith("25")
    
    def test_generate_request_number_year_2030(self):
        """Год 2030 -> 30"""
        date = datetime(2030, 6, 15)
        
        result = generate_request_number(date)
        
        assert result.endswith("30")


class TestRequestCreationData:
    """Тесты dataclass RequestCreationData"""
    
    def test_request_creation_data_defaults(self):
        """Значения по умолчанию"""
        data = RequestCreationData()
        
        assert data.category is None
        assert data.description is None
        assert data.quantity is None
        assert data.priority is None
        assert data.photos == []
    
    def test_request_creation_data_with_values(self):
        """Создание с значениями"""
        data = RequestCreationData(
            category="Канцелярия",
            description="Нужны ручки",
            quantity=10,
            priority="normal",
            photos=["photo_1", "photo_2"]
        )
        
        assert data.category == "Канцелярия"
        assert data.description == "Нужны ручки"
        assert data.quantity == 10
        assert data.priority == "normal"
        assert len(data.photos) == 2


class TestRequestCreationDataIsMaterialCategory:
    """Тесты определения материальной категории"""
    
    def test_is_material_category_true(self):
        """Материальные категории"""
        material_categories = [
            "Канцелярия",
            "Чай, кофе, сахар, вода",
            "Хозтовары и уборка",
            "ИТ-оборудование и расходники"
        ]
        
        for category in material_categories:
            data = RequestCreationData(category=category)
            assert data.is_material_category() is True, f"Категория {category} должна быть материальной"
    
    def test_is_material_category_false(self):
        """Нематериальные категории"""
        non_material_categories = [
            "Ремонт мебели",
            "Ремонт сантехники",
            "Ремонт электрики",
            "Другое"
        ]
        
        for category in non_material_categories:
            data = RequestCreationData(category=category)
            assert data.is_material_category() is False, f"Категория {category} не должна быть материальной"
    
    def test_is_material_category_none(self):
        """Категория не выбрана"""
        data = RequestCreationData()
        
        assert data.is_material_category() is False


class TestRequestCreationDataIsComplete:
    """Тесты проверки полноты данных"""
    
    def test_is_complete_true_material(self):
        """Полные данные для материальной категории"""
        data = RequestCreationData(
            category="Канцелярия",
            description="Нужны ручки",
            quantity=10,
            priority="normal"
        )
        
        assert data.is_complete() is True
    
    def test_is_complete_true_non_material(self):
        """Полные данные для нематериальной категории (без количества)"""
        data = RequestCreationData(
            category="Ремонт мебели",
            description="Сломан стол",
            priority="urgent"
        )
        
        assert data.is_complete() is True
    
    def test_is_complete_false_missing_category(self):
        """Не заполнена категория"""
        data = RequestCreationData(
            description="Описание",
            priority="normal"
        )
        
        assert data.is_complete() is False
    
    def test_is_complete_false_missing_description(self):
        """Не заполнено описание"""
        data = RequestCreationData(
            category="Канцелярия",
            quantity=10,
            priority="normal"
        )
        
        assert data.is_complete() is False
    
    def test_is_complete_false_missing_priority(self):
        """Не заполнен приоритет"""
        data = RequestCreationData(
            category="Канцелярия",
            description="Описание",
            quantity=10
        )
        
        assert data.is_complete() is False
    
    def test_is_complete_false_material_without_quantity(self):
        """Материальная категория без количества"""
        data = RequestCreationData(
            category="Канцелярия",
            description="Нужны ручки",
            priority="normal"
            # quantity не указано
        )
        
        assert data.is_complete() is False


class TestRequestCreationDataPreview:
    """Тесты текста предпросмотра"""
    
    def test_to_preview_text_basic(self):
        """Базовый предпросмотр"""
        data = RequestCreationData(
            category="Канцелярия",
            description="Нужны ручки синие",
            priority="normal"
        )
        
        result = data.to_preview_text()
        
        assert "Предпросмотр заявки" in result
        assert "Канцелярия" in result
        assert "Нужны ручки синие" in result
        assert "Обычная" in result
    
    def test_to_preview_text_with_quantity(self):
        """Предпросмотр с количеством"""
        data = RequestCreationData(
            category="Канцелярия",
            description="Нужны ручки",
            quantity=50,
            priority="normal"
        )
        
        result = data.to_preview_text()
        
        assert "Количество:" in result
        assert "50 шт." in result
    
    def test_to_preview_text_urgent_priority(self):
        """Предпросмотр со срочным приоритетом"""
        data = RequestCreationData(
            category="Ремонт сантехники",
            description="Течет кран",
            priority="urgent"
        )
        
        result = data.to_preview_text()
        
        assert "🚨" in result
        assert "Срочно" in result
    
    def test_to_preview_text_with_photos(self):
        """Предпросмотр с фото"""
        data = RequestCreationData(
            category="Ремонт мебели",
            description="Сломан стол",
            priority="normal",
            photos=["photo_1", "photo_2", "photo_3"]
        )
        
        result = data.to_preview_text()
        
        assert "Фото:" in result
        assert "3 шт." in result


class TestRequestCreationDataSerialization:
    """Тесты сериализации/десериализации"""
    
    def test_to_dict(self):
        """Преобразование в словарь"""
        data = RequestCreationData(
            category="Канцелярия",
            description="Тест",
            quantity=5,
            priority="normal",
            photos=["photo_1"]
        )
        
        result = data.to_dict()
        
        assert result == {
            "category": "Канцелярия",
            "description": "Тест",
            "quantity": 5,
            "priority": "normal",
            "photos": ["photo_1"]
        }
    
    def test_from_dict(self):
        """Создание из словаря"""
        dict_data = {
            "category": "Канцелярия",
            "description": "Тест",
            "quantity": 5,
            "priority": "normal",
            "photos": ["photo_1"]
        }
        
        data = RequestCreationData.from_dict(dict_data)
        
        assert data.category == "Канцелярия"
        assert data.description == "Тест"
        assert data.quantity == 5
        assert data.priority == "normal"
        assert data.photos == ["photo_1"]
    
    def test_from_dict_partial(self):
        """Создание из неполного словаря"""
        dict_data = {
            "category": "Канцелярия"
        }
        
        data = RequestCreationData.from_dict(dict_data)
        
        assert data.category == "Канцелярия"
        assert data.description is None
        assert data.quantity is None
        assert data.priority is None
        assert data.photos == []
    
    def test_roundtrip(self):
        """to_dict -> from_dict сохраняет данные"""
        original = RequestCreationData(
            category="Ремонт электрики",
            description="Не работает розетка",
            priority="urgent",
            photos=["photo_1", "photo_2"]
        )
        
        dict_data = original.to_dict()
        restored = RequestCreationData.from_dict(dict_data)
        
        assert restored.category == original.category
        assert restored.description == original.description
        assert restored.quantity == original.quantity
        assert restored.priority == original.priority
        assert restored.photos == original.photos

