"""Утилиты для работы с заявками"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class RequestCreationData:
    """Данные создаваемой заявки"""
    category: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    priority: Optional[str] = None  # 'normal' or 'urgent'
    photos: List[str] = field(default_factory=list)  # Telegram file_id
    
    # Материальные категории (требуют указания количества)
    MATERIAL_CATEGORIES = [
        "Канцелярия",
        "Чай, кофе, сахар, вода",
        "Хозтовары и уборка",
        "ИТ-оборудование и расходники"
    ]
    
    def is_material_category(self) -> bool:
        """Проверка, является ли категория материалом"""
        return self.category in self.MATERIAL_CATEGORIES
    
    def is_complete(self) -> bool:
        """Проверка полноты данных"""
        required = [
            self.category,
            self.description,
            self.priority
        ]
        
        # Если категория - материал, то количество обязательно
        if self.is_material_category() and not self.quantity:
            return False
            
        return all(required)
    
    def to_preview_text(self) -> str:
        """Форматирование для предпросмотра"""
        text = f"📋 <b>Предпросмотр заявки</b>\n\n"
        text += f"📂 <b>Категория:</b> {self.category}\n"
        text += f"📝 <b>Описание:</b> {self.description}\n"
        
        if self.quantity:
            text += f"🔢 <b>Количество:</b> {self.quantity} шт.\n"
            
        priority_emoji = "🚨" if self.priority == "urgent" else "⏰"
        priority_text = "Срочно" if self.priority == "urgent" else "Обычная"
        text += f"{priority_emoji} <b>Приоритет:</b> {priority_text}\n"
        
        if self.photos:
            text += f"📷 <b>Фото:</b> {len(self.photos)} шт.\n"
            
        return text
    
    @classmethod
    def from_dict(cls, data: dict) -> "RequestCreationData":
        """Создать объект из словаря (для восстановления из FSM state)"""
        return cls(
            category=data.get("category"),
            description=data.get("description"),
            quantity=data.get("quantity"),
            priority=data.get("priority"),
            photos=data.get("photos", [])
        )
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь (для сохранения в FSM state)"""
        return {
            "category": self.category,
            "description": self.description,
            "quantity": self.quantity,
            "priority": self.priority,
            "photos": self.photos
        }


def generate_request_number(date: Optional[datetime] = None) -> str:
    """
    Генерировать номер заявки в формате ЗХ-ДДММГГ-№№№
    
    Args:
        date: Дата для номера (если None - текущая дата)
        
    Returns:
        Номер заявки без порядкового номера (только префикс даты)
    """
    if date is None:
        date = datetime.now()
    
    day = date.day
    month = date.month
    year = date.year % 100  # Последние 2 цифры года
    
    return f"ЗХ-{day:02d}{month:02d}{year:02d}"

