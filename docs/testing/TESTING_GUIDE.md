# Руководство по тестированию бота "Завхоз"

## 📋 Содержание

1. [Структура тестов](#структура-тестов)
2. [Установка зависимостей](#установка-зависимостей)
3. [Запуск тестов](#запуск-тестов)
4. [Покрытие кода](#покрытие-кода)
5. [Написание новых тестов](#написание-новых-тестов)
6. [Fixtures](#fixtures)
7. [Troubleshooting](#troubleshooting)

---

## 📁 Структура тестов

```
tests/
├── conftest.py              # Общие fixtures для всех тестов
├── fixtures/                # Модули с fixtures
│   ├── database.py          # Fixtures для БД
│   ├── bot.py               # Fixtures для Telegram Bot
│   └── data.py              # Тестовые данные
├── unit/                    # Unit тесты
│   ├── test_services/       # Тесты сервисов
│   ├── test_utils/          # Тесты утилит
│   └── test_models/         # Тесты моделей
├── integration/             # Интеграционные тесты
│   ├── test_handlers/       # Тесты handlers
│   ├── test_fsm/            # Тесты FSM состояний
│   ├── test_middleware/     # Тесты middleware
│   └── test_database/       # Тесты БД
└── e2e/                     # End-to-end тесты
    └── test_scenarios/      # Полные сценарии
```

---

## 🔧 Установка зависимостей

```bash
# Активировать виртуальное окружение
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
```

### Тестовые зависимости

- `pytest==8.0.0` - основной фреймворк
- `pytest-asyncio==0.23.0` - поддержка async тестов
- `pytest-mock==3.12.0` - моки
- `pytest-cov==4.1.0` - покрытие кода
- `faker==22.0.0` - генерация тестовых данных
- `aiosqlite==0.19.0` - SQLite для тестов

---

## 🚀 Запуск тестов

### Быстрые команды

```bash
# Все тесты
pytest

# Только unit тесты
pytest tests/unit/

# Только интеграционные
pytest tests/integration/

# Только e2e
pytest tests/e2e/

# Конкретный файл
pytest tests/unit/test_services/test_request_service.py

# Конкретный тест
pytest tests/unit/test_services/test_request_service.py::TestRequestServiceCreate::test_create_request_without_photos
```

### Через скрипты

```bash
# Windows:
scripts\run_tests.bat all      # все тесты
scripts\run_tests.bat unit     # unit тесты
scripts\run_tests.bat int      # интеграционные
scripts\run_tests.bat e2e      # e2e тесты
scripts\run_tests.bat cov      # с покрытием
scripts\run_tests.bat html     # с HTML отчетом

# Linux/Mac:
chmod +x scripts/run_tests.sh
./scripts/run_tests.sh all
./scripts/run_tests.sh cov
```

### Полезные флаги pytest

```bash
# Подробный вывод
pytest -v

# Показать print()
pytest -s

# Остановиться на первой ошибке
pytest -x

# Показать последние N провалившихся
pytest --lf

# Запуск в параллели (нужен pytest-xdist)
pytest -n auto
```

---

## 📊 Покрытие кода

### Запуск с покрытием

```bash
# Вывод в консоль
pytest --cov=bot --cov-report=term-missing

# HTML отчет
pytest --cov=bot --cov-report=html

# Открыть отчет (Windows)
start htmlcov\index.html

# Открыть отчет (Linux/Mac)
open htmlcov/index.html
```

### Интерпретация отчета

- **Stmts** - количество строк кода
- **Miss** - количество непокрытых строк
- **Cover** - процент покрытия
- **Missing** - номера непокрытых строк

### Минимальное покрытие

В `.coveragerc` можно установить минимальное покрытие:

```ini
[report]
fail_under = 70
```

---

## ✍️ Написание новых тестов

### Структура теста

```python
"""
Docstring с описанием модуля
"""
import pytest
from bot.services.my_service import MyService


class TestMyService:
    """Тесты для MyService"""
    
    @pytest.mark.asyncio
    async def test_my_method(self, test_session):
        """Описание теста"""
        # Arrange - подготовка
        service = MyService()
        
        # Act - действие
        result = await service.my_method(test_session)
        
        # Assert - проверка
        assert result is not None
```

### Правила именования

- Файлы: `test_*.py`
- Классы: `Test*`
- Методы: `test_*`
- Fixtures: описательные имена (`test_user`, `mock_bot`)

### Маркеры

```python
@pytest.mark.asyncio        # для async функций
@pytest.mark.unit           # unit тест
@pytest.mark.integration    # интеграционный
@pytest.mark.e2e            # end-to-end
@pytest.mark.slow           # медленный тест
```

---

## 🔌 Fixtures

### Fixtures для БД

```python
# Тестовая сессия (автоматический откат)
async def test_example(test_session):
    user = User(id=123, role="employee")
    test_session.add(user)
    await test_session.flush()
    # После теста все откатится
```

### Fixtures для Telegram

```python
# Мок бота
async def test_send(mock_bot):
    await mock_bot.send_message(chat_id=123, text="test")
    mock_bot.send_message.assert_called_once()

# Мок сообщения
async def test_message(mock_message):
    await mock_message.answer("Ответ")
    mock_message.answer.assert_called_with("Ответ")
```

### Fixtures для данных

```python
# Готовый пользователь в БД
async def test_with_user(test_session, test_user):
    assert test_user.role == "employee"

# Готовая заявка в БД
async def test_with_request(test_session, test_request):
    assert test_request.status == "new"
```

### Создание своих fixtures

```python
@pytest.fixture
async def my_fixture(test_session):
    """Мой fixture"""
    # Setup
    data = await create_something(test_session)
    
    yield data
    
    # Teardown (опционально)
    await cleanup(data)
```

---

## 🔍 Troubleshooting

### Ошибка: "Module not found"

```bash
# Убедитесь что проект в PYTHONPATH
export PYTHONPATH=$PYTHONPATH:.

# Или установите проект
pip install -e .
```

### Ошибка: "Event loop is closed"

Добавьте в `pytest.ini`:
```ini
asyncio_mode = auto
```

### Ошибка: "Database error"

```bash
# Очистите кеш
rm -rf .pytest_cache/
rm -rf __pycache__/
```

### Тесты медленные

```bash
# Запуск только быстрых тестов
pytest -m "not slow"

# Параллельный запуск
pip install pytest-xdist
pytest -n auto
```

### Отладка теста

```python
# Добавьте breakpoint
def test_debug(test_session):
    import pdb; pdb.set_trace()
    # или
    breakpoint()
```

---

## 📚 Полезные ресурсы

- [pytest документация](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Faker](https://faker.readthedocs.io/)

---

## ✅ Чеклист перед коммитом

- [ ] Все тесты проходят: `pytest`
- [ ] Покрытие не упало: `pytest --cov=bot`
- [ ] Новые функции покрыты тестами
- [ ] Нет print() в тестах (кроме отладки)
- [ ] Docstrings актуальны

