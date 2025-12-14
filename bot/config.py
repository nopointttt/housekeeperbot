"""Конфигурация бота"""
import os
from dataclasses import dataclass
from typing import Optional, List
from dotenv import load_dotenv

# Если Render "загружает env", то переменные будут в окружении.
# load_dotenv() оставляем как fallback для локального запуска (override=False по умолчанию).
load_dotenv()


def _get_env_str(name: str, default: str | None = None) -> str | None:
    """Получить строковую переменную окружения и аккуратно нормализовать.

    Нормализация нужна потому что .env-файлы часто содержат:
    - пробелы после '='
    - кавычки вокруг значения
    """
    raw = os.getenv(name, default)
    if raw is None:
        return None
    value = raw.strip()
    # убрать одинарные/двойные кавычки по краям, если они есть
    if len(value) >= 2 and ((value[0] == value[-1] == "'") or (value[0] == value[-1] == '"')):
        value = value[1:-1].strip()
    return value


def _get_env_int(name: str) -> int:
    value = _get_env_str(name)
    if not value:
        raise ValueError(f"{name} не установлен в переменных окружения")
    try:
        return int(value)
    except ValueError as e:
        raise ValueError(f"{name} должен быть числом (Telegram ID). Получено: '{value}'") from e


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
        bot_token = _get_env_str("BOT_TOKEN")
        if not bot_token:
            raise ValueError("BOT_TOKEN не установлен в переменных окружения")
        
        database_url = _get_env_str("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL не установлен в переменных окружения")
        
        warehouseman_id = _get_env_int("WAREHOUSEMAN_ID")
        manager_id = _get_env_int("MANAGER_ID")
        
        # Загружаем список ID сотрудников из конфига (через запятую)
        allowed_employees_str = _get_env_str("ALLOWED_EMPLOYEE_IDS", "") or ""
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
            warehouseman_id=warehouseman_id,
            manager_id=manager_id,
            allowed_employee_ids=allowed_employee_ids,
            timezone=_get_env_str("TIMEZONE", "Europe/Moscow") or "Europe/Moscow",
            log_level=_get_env_str("LOG_LEVEL", "INFO") or "INFO",
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

