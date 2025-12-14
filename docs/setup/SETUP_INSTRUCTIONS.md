# Инструкция по настройке проекта

## Требования

- **Python 3.11+** (важно! Не используйте Python 3.14, так как некоторые пакеты требуют компиляции)
- PowerShell или командная строка
- Доступ в интернет для установки зависимостей

## Шаг 0: Установка Python 3.11 (если не установлен)

Если у вас установлена другая версия Python (например, 3.14), установите Python 3.11:

```powershell
# Установка Python 3.11 через winget
winget install Python.Python.3.11
```

После установки перезапустите PowerShell и проверьте версию:

```powershell
python --version
# Должно показать: Python 3.11.x
```

Если установлено несколько версий Python, можно использовать конкретную версию:

```powershell
# Создание venv с конкретной версией Python
py -3.11 -m venv venv
```

## Шаг 1: Создание виртуального окружения

Выполните в PowerShell:

```powershell
python -m venv venv
```

## Шаг 2: Активация виртуального окружения

### Вариант 1: Если возникает ошибка политики выполнения

Если вы видите ошибку `UnauthorizedAccess` или `ExecutionPolicy`, выполните:

```powershell
# Временно разрешить выполнение скриптов для текущего сеанса
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Теперь активируйте виртуальное окружение
venv\Scripts\activate
```

### Вариант 2: Альтернативный способ активации

Можно активировать окружение напрямую через Python:

```powershell
venv\Scripts\python.exe -m pip --version
```

Или использовать полный путь к pip:

```powershell
.\venv\Scripts\pip.exe install -r requirements.txt
```

### Вариант 3: Использование cmd вместо PowerShell

Откройте обычную командную строку (cmd) и выполните:

```cmd
venv\Scripts\activate.bat
```

После активации вы увидите `(venv)` в начале строки.

## Шаг 3: Установка зависимостей

```powershell
pip install -r requirements.txt
```

## Шаг 4: Настройка переменных окружения

Создайте файл `.env` в корне проекта со следующим содержимым:

```env
# Telegram Bot Token (получить у @BotFather)
BOT_TOKEN=your_bot_token_here

# Neon SQL Database URL
# ВАЖНО: Используйте ssl=true, НЕ sslmode=require
# Правильный формат: postgresql+asyncpg://user:password@host/database?ssl=true
DATABASE_URL=postgresql+asyncpg://your_user:your_password@your_host/your_database?ssl=true

# Telegram IDs для ролей
WAREHOUSEMAN_ID=468845503
MANAGER_ID=460275491

# Часовой пояс
TIMEZONE=Europe/Moscow

# Уровень логирования (опционально)
LOG_LEVEL=INFO
```

**Важно:**
- Получите BOT_TOKEN у [@BotFather](https://t.me/BotFather) в Telegram
- Создайте базу данных в [Neon SQL](https://neon.tech)
- Узнайте свои Telegram ID (можно через [@userinfobot](https://t.me/userinfobot))

## Шаг 5: Инициализация Alembic и создание первой миграции

```powershell
# Инициализация Alembic (если еще не сделано)
alembic init alembic

# Создание первой миграции
alembic revision --autogenerate -m "Initial migration"

# Применение миграции
alembic upgrade head
```

## Шаг 6: Проверка подключения

Убедитесь, что:
- Виртуальное окружение активировано
- Файл `.env` создан и заполнен
- Зависимости установлены
- База данных доступна

## Шаг 7: Применение миграций (если еще не сделано)

Убедитесь, что миграции применены к базе данных:

```powershell
alembic upgrade head
```

Вы должны увидеть сообщение о том, что миграции применены успешно.

## Шаг 8: Запуск бота

**Важно:** Убедитесь, что:
- ✅ Виртуальное окружение активировано (видите `(venv)` в начале строки)
- ✅ Файл `.env` создан и заполнен правильными значениями
- ✅ Миграции применены (`alembic upgrade head`)

Запустите бота:

```powershell
python main.py
```

**Ожидаемый вывод при успешном запуске:**
```
INFO - Запуск бота 'Завхоз'...
INFO - База данных инициализирована
INFO - Бот запущен
```

## Шаг 9: Проверка работы бота

1. **Откройте Telegram** и найдите вашего бота по имени (которое вы указали при создании через @BotFather)

2. **Отправьте команду `/start`** боту

3. **Проверьте ответ:**
   - Бот должен ответить приветственным сообщением
   - Должна появиться клавиатура с кнопками (в зависимости от вашей роли)
   - Если вы указали свой Telegram ID в `WAREHOUSEMAN_ID` или `MANAGER_ID`, бот определит вашу роль

4. **Проверьте логи в консоли:**
   - Должны появляться сообщения о полученных сообщениях
   - Не должно быть ошибок

**Если бот не отвечает:**
- Проверьте, что `BOT_TOKEN` в `.env` правильный
- Убедитесь, что бот запущен (нет ошибок в консоли)
- Проверьте, что вы пишете правильному боту в Telegram

---

## Что дальше?

После успешной настройки можно продолжать разработку:

1. **Phase 2:** Реализация системы ролей
2. **Phase 3:** Мастер создания заявок
3. И так далее по плану (см. `memory-bank/PLAN_IMPLEMENTATION.md`)

---

## Возможные проблемы

### Ошибка установки зависимостей (pydantic-core требует Rust)

**Проблема:** При установке зависимостей возникает ошибка компиляции `pydantic-core` - требуется Rust/Cargo.

**Причина:** Используется Python 3.14, для которого некоторые пакеты еще не имеют предкомпилированных wheel-файлов.

**Решение:** Установите Python 3.11:
```powershell
winget install Python.Python.3.11
```

Затем пересоздайте виртуальное окружение:
```powershell
# Удалите старое окружение
Remove-Item -Recurse -Force venv

# Создайте новое с Python 3.11
py -3.11 -m venv venv

# Активируйте и установите зависимости
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
venv\Scripts\activate
pip install -r requirements.txt
```

### Ошибка активации виртуального окружения (ExecutionPolicy)

**Проблема:** `UnauthorizedAccess` или `ExecutionPolicy` при попытке активировать venv.

**Решение:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
venv\Scripts\activate
```

Или используйте альтернативные способы из Шага 2 выше.

### Ошибка подключения к БД (TypeError: connect() got an unexpected keyword argument 'sslmode')

**Проблема:** При запуске миграций Alembic возникает ошибка `TypeError: connect() got an unexpected keyword argument 'sslmode'`.

**Причина:** В URL базы данных используется параметр `sslmode`, но `asyncpg` не поддерживает его напрямую.

**Решение:** Используйте `ssl=true` вместо `sslmode=require` в DATABASE_URL:

```env
# НЕПРАВИЛЬНО:
DATABASE_URL=postgresql+asyncpg://user:pass@host/db?sslmode=require

# ПРАВИЛЬНО:
DATABASE_URL=postgresql+asyncpg://user:pass@host/db?ssl=true
```

**Другие возможные проблемы с подключением:**
- Проверьте DATABASE_URL в `.env`
- Убедитесь, что база данных создана в Neon SQL
- Проверьте правильность формата URL

### Ошибка импорта модулей
- Убедитесь, что виртуальное окружение активировано
- Проверьте, что все зависимости установлены: `pip list`

### Ошибка токена бота
- Проверьте BOT_TOKEN в `.env`
- Убедитесь, что токен скопирован полностью (без пробелов)

---

*Следующие шаги разработки будут добавляться по мере реализации.*

