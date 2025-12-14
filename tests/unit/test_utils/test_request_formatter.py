"""
Unit тесты для request_formatter

Тестируемые функции:
- format_request_short() - краткое форматирование
- format_request_full() - полное форматирование
- format_request_list() - форматирование списка
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from bot.utils.request_formatter import (
    format_request_short,
    format_request_full,
    format_request_list
)
from bot.database.models import Request


def create_mock_request(
    number="ЗХ-010125-001",
    status="new",
    category="Канцелярия",
    description="Тестовое описание",
    quantity=10,
    priority="normal",
    created_at=None,
    updated_at=None,
    completed_at=None,
    rejection_reason=None,
    photos=None
):
    """Создать мок заявки для тестов"""
    request = MagicMock(spec=Request)
    request.id = 1
    request.number = number
    request.status = status
    request.category = category
    request.description = description
    request.quantity = quantity
    request.priority = priority
    request.created_at = created_at or datetime.now()
    request.updated_at = updated_at or request.created_at
    request.completed_at = completed_at
    request.rejection_reason = rejection_reason
    request.photos = photos or []
    return request


class TestFormatRequestShort:
    """Тесты краткого форматирования"""
    
    def test_format_request_short_new(self):
        """Форматирование новой заявки"""
        request = create_mock_request(status="new")
        
        result = format_request_short(request)
        
        assert "🆕" in result
        assert request.number in result
        assert "Новая" in result
        assert request.category in result
    
    def test_format_request_short_in_progress(self):
        """Форматирование заявки в работе"""
        request = create_mock_request(status="in_progress")
        
        result = format_request_short(request)
        
        assert "🔄" in result
        assert "В работе" in result
    
    def test_format_request_short_completed(self):
        """Форматирование выполненной заявки"""
        request = create_mock_request(status="completed")
        
        result = format_request_short(request)
        
        assert "✅" in result
        assert "Выполнено" in result
    
    def test_format_request_short_rejected(self):
        """Форматирование отклоненной заявки"""
        request = create_mock_request(status="rejected")
        
        result = format_request_short(request)
        
        assert "❌" in result
        assert "Отклонено" in result
    
    def test_format_request_short_truncates_long_description(self):
        """Длинное описание обрезается"""
        long_description = "A" * 100
        request = create_mock_request(description=long_description)
        
        result = format_request_short(request)
        
        # Описание обрезается до 47 символов + "..."
        assert "..." in result
        assert "A" * 47 + "..." in result
    
    def test_format_request_short_keeps_short_description(self):
        """Короткое описание не обрезается"""
        short_description = "Нужны ручки"
        request = create_mock_request(description=short_description)
        
        result = format_request_short(request)
        
        assert short_description in result
        assert "..." not in short_description  # В описании нет троеточия
    
    def test_format_request_short_includes_date(self):
        """Включает дату создания"""
        date = datetime(2025, 1, 15, 10, 30)
        request = create_mock_request(created_at=date)
        
        result = format_request_short(request)
        
        assert "15.01.2025 10:30" in result
    
    def test_format_request_short_unknown_status(self):
        """Неизвестный статус показывается как есть"""
        request = create_mock_request(status="unknown_status")
        
        result = format_request_short(request)
        
        assert "unknown_status" in result
        assert "📋" in result  # Дефолтный emoji


class TestFormatRequestFull:
    """Тесты полного форматирования"""
    
    def test_format_request_full_basic(self):
        """Базовое полное форматирование"""
        request = create_mock_request()
        
        result = format_request_full(request)
        
        assert f"Заявка {request.number}" in result
        assert "Статус:" in result
        assert "Категория:" in result
        assert "Описание:" in result
        assert "Приоритет:" in result
        assert "Создана:" in result
    
    def test_format_request_full_with_quantity(self):
        """Показывает количество если указано"""
        request = create_mock_request(quantity=25)
        
        result = format_request_full(request)
        
        assert "Количество:" in result
        assert "25 шт." in result
    
    def test_format_request_full_without_quantity(self):
        """Не показывает количество если не указано"""
        request = create_mock_request(quantity=None)
        
        result = format_request_full(request)
        
        assert "Количество:" not in result
    
    def test_format_request_full_urgent_priority(self):
        """Показывает срочный приоритет"""
        request = create_mock_request(priority="urgent")
        
        result = format_request_full(request)
        
        assert "🚨" in result
        assert "Срочно" in result
    
    def test_format_request_full_normal_priority(self):
        """Показывает обычный приоритет"""
        request = create_mock_request(priority="normal")
        
        result = format_request_full(request)
        
        assert "⏰" in result
        assert "Обычная" in result
    
    def test_format_request_full_shows_updated_if_different(self):
        """Показывает дату обновления если отличается от создания"""
        created = datetime(2025, 1, 15, 10, 0)
        updated = datetime(2025, 1, 16, 15, 30)
        request = create_mock_request(created_at=created, updated_at=updated)
        
        result = format_request_full(request)
        
        assert "Обновлена:" in result
        assert "16.01.2025 15:30" in result
    
    def test_format_request_full_hides_updated_if_same(self):
        """Не показывает дату обновления если совпадает с созданием"""
        date = datetime(2025, 1, 15, 10, 0)
        request = create_mock_request(created_at=date, updated_at=date)
        
        result = format_request_full(request)
        
        assert "Обновлена:" not in result
    
    def test_format_request_full_shows_completed_at(self):
        """Показывает дату завершения"""
        completed = datetime(2025, 1, 17, 12, 0)
        request = create_mock_request(completed_at=completed)
        
        result = format_request_full(request)
        
        assert "Завершена:" in result
        assert "17.01.2025 12:00" in result
    
    def test_format_request_full_shows_rejection_reason(self):
        """Показывает причину отклонения"""
        request = create_mock_request(
            status="rejected",
            rejection_reason="Нет в наличии"
        )
        
        result = format_request_full(request)
        
        assert "Причина отклонения:" in result
        assert "Нет в наличии" in result
    
    def test_format_request_full_without_photos(self):
        """Без фото - информация о фото не показывается"""
        request = create_mock_request(photos=[])
        
        # Мокаем sqlalchemy.inspect (импортируется внутри функции)
        with patch('sqlalchemy.inspect') as mock_inspect:
            mock_insp = MagicMock()
            mock_attrs = MagicMock()
            mock_attrs.loaded_value = []  # пустой список фото
            mock_insp.attrs = {'photos': mock_attrs}
            mock_inspect.return_value = mock_insp
            
            result = format_request_full(request, include_photos=True)
        
        # Фото: 0 шт. не должно показываться (пустой список)
        assert "📷" not in result
    
    def test_format_request_full_include_photos_false(self):
        """include_photos=False - не показывает информацию о фото"""
        photos = [MagicMock(), MagicMock()]
        request = create_mock_request(photos=photos)
        
        result = format_request_full(request, include_photos=False)
        
        assert "Фото:" not in result


class TestFormatRequestList:
    """Тесты форматирования списка заявок"""
    
    def test_format_request_list_empty(self):
        """Пустой список заявок"""
        text, ids = format_request_list([])
        
        assert "Заявок пока нет" in text
        assert ids == []
    
    def test_format_request_list_with_requests(self):
        """Список с заявками"""
        requests = [
            create_mock_request(number="ЗХ-010125-001"),
            create_mock_request(number="ЗХ-010125-002"),
        ]
        requests[0].id = 1
        requests[1].id = 2
        
        text, ids = format_request_list(requests)
        
        assert "1." in text
        assert "2." in text
        assert "ЗХ-010125-001" in text
        assert "ЗХ-010125-002" in text
        assert ids == [1, 2]
    
    def test_format_request_list_custom_title(self):
        """Кастомный заголовок"""
        requests = [create_mock_request()]
        requests[0].id = 1
        
        text, ids = format_request_list(requests, title="Все заявки")
        
        assert "Все заявки" in text
    
    def test_format_request_list_default_title(self):
        """Заголовок по умолчанию"""
        requests = [create_mock_request()]
        requests[0].id = 1
        
        text, ids = format_request_list(requests)
        
        assert "Ваши заявки" in text
    
    def test_format_request_list_returns_correct_ids(self):
        """Возвращает правильные ID заявок"""
        requests = []
        for i in range(5):
            req = create_mock_request()
            req.id = i + 10  # ID: 10, 11, 12, 13, 14
            requests.append(req)
        
        text, ids = format_request_list(requests)
        
        assert ids == [10, 11, 12, 13, 14]


class TestFormatRequestEdgeCases:
    """Edge cases"""
    
    def test_format_request_short_special_characters(self):
        """Спецсимволы в описании"""
        request = create_mock_request(description="<b>HTML</b> & символы")
        
        result = format_request_short(request)
        
        # Текст должен быть включен (HTML теги сохраняются для parse_mode=HTML)
        assert "HTML" in result
    
    def test_format_request_full_empty_description(self):
        """Пустое описание"""
        request = create_mock_request(description="")
        
        result = format_request_full(request)
        
        assert "Описание:" in result
    
    def test_format_request_short_unicode(self):
        """Unicode символы в описании"""
        request = create_mock_request(description="Нужны 📝 ручки ✏️")
        
        result = format_request_short(request)
        
        assert "📝" in result
        assert "✏️" in result

