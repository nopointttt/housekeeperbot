"""Конфигурация бота"""
import os
from dataclasses import dataclass
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Конфигурация приложения"""
    
    # Telegram Bot
    bot_token: str
    
    # Database
    database_url: str
    
    # Roles (Telegram IDs)
    warehouseman_id: int
    manager_id: int
    allowed_employee_ids: List[int]  # Список ID сотрудников из конфига
    
    # Timezone
    timezone: str = "Europe/Moscow"
    
    # Logging
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Загрузка конфигурации из переменных окружения"""
        bot_token = os.getenv("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN не установлен в переменных окружения")
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL не установлен в переменных окружения")
        
        warehouseman_id = os.getenv("WAREHOUSEMAN_ID")
        if not warehouseman_id:
            raise ValueError("WAREHOUSEMAN_ID не установлен в переменных окружения")
        
        manager_id = os.getenv("MANAGER_ID")
        if not manager_id:
            raise ValueError("MANAGER_ID не установлен в переменных окружения")
        
        # Загружаем список ID сотрудников из конфига (через запятую)
        allowed_employees_str = os.getenv("ALLOWED_EMPLOYEE_IDS", "")
        allowed_employee_ids: List[int] = []
        if allowed_employees_str:
            try:
                allowed_employee_ids = [
                    int(emp_id.strip()) 
                    for emp_id in allowed_employees_str.split(",") 
                    if emp_id.strip()
                ]
            except ValueError as e:
                raise ValueError(f"Ошибка парсинга ALLOWED_EMPLOYEE_IDS: {e}. Ожидается список чисел через запятую.")
        
        return cls(
            bot_token=bot_token,
            database_url=database_url,
            warehouseman_id=int(warehouseman_id),
            manager_id=int(manager_id),
            allowed_employee_ids=allowed_employee_ids,
            timezone=os.getenv("TIMEZONE", "Europe/Moscow"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
    
    def is_allowed_user(self, user_id: int) -> bool:
        """
        Проверить, есть ли у пользователя доступ (из конфига или роли)
        
        Args:
            user_id: Telegram ID пользователя
            
        Returns:
            True если пользователь имеет доступ
        """
        # Завхоз и руководитель всегда имеют доступ
        if user_id == self.warehouseman_id or user_id == self.manager_id:
            return True
        
        # Проверяем в списке разрешенных сотрудников из конфига
        if user_id in self.allowed_employee_ids:
            return True
        
        return False
    
    def get_role_by_id(self, user_id: int) -> str:
        """Определить роль пользователя по Telegram ID"""
        if user_id == self.warehouseman_id:
            return "warehouseman"
        elif user_id == self.manager_id:
            return "manager"
        else:
            return "employee"


# Глобальный экземпляр конфигурации (инициализируется при первом использовании)
_config_instance: Config | None = None


def get_config() -> Config:
    """Получить экземпляр конфигурации (singleton)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config.from_env()
    return _config_instance


# Для удобства доступа
config = get_config()

