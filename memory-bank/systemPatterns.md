# System Patterns

## Architecture Patterns

### Layered Architecture (Слоистая архитектура)
```
┌─────────────────────────────────────┐
│   Presentation Layer (Handlers)     │
│   - Handlers для каждой роли        │
│   - FSM для мастеров                │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   Business Logic Layer (Services)   │
│   - Role Service                    │
│   - Request Service                 │
│   - Warehouse Service               │
│   - Technician Service              │
│   - Notification Service            │
│   - Marketing Service               │
│   - Automation Service              │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   Data Access Layer (Database)      │
│   - SQLAlchemy Models               │
│   - Repository Pattern              │
└─────────────────────────────────────┘
```

### FSM Pattern (Finite State Machine)
- Используется для пошаговых мастеров (создание заявки, рассылка)
- Состояния хранятся в aiogram FSMContext
- Переходы между состояниями через обработчики

### Repository Pattern
- Инкапсуляция доступа к данным
- Абстракция от конкретной реализации БД
- Упрощение тестирования

## Design Patterns

### Singleton Pattern
- Database connection pool
- Bot instance

### Factory Pattern
- Создание клавиатур по ролям
- Создание обработчиков

### Observer Pattern
- Уведомления о событиях (смена статуса заявки)
- Автоматические триггеры

## Coding Standards

### Python Style Guide
- PEP 8 compliance
- Type hints для функций
- Docstrings для всех функций и классов
- Максимальная длина строки: 120 символов

### Naming Conventions
- Классы: PascalCase (UserService)
- Функции: snake_case (create_request)
- Константы: UPPER_SNAKE_CASE (MAX_PHOTOS)
- Приватные методы: _leading_underscore

### File Organization
```
project/
├── bot/
│   ├── handlers/
│   ├── services/
│   ├── keyboards/
│   ├── states/
│   ├── database/
│   ├── utils/
│   └── config.py
├── migrations/
├── tests/
└── main.py
```

## Best Practices

### Error Handling
- Использование try-except блоков
- Логирование всех ошибок
- Понятные сообщения об ошибках для пользователей
- Graceful degradation при сбоях

### Database
- Использование транзакций для критичных операций
- Асинхронные запросы (asyncpg)
- Миграции через Alembic
- Индексы для часто используемых полей

### Security
- Валидация всех пользовательских данных
- Проверка прав доступа на каждом уровне
- Безопасное хранение токенов (env переменные)
- Защита от SQL injection (ORM)
- Изоляция данных через tenant_id в демо-режиме
- Ограничение тестового доступа (7 дней)

### Multi-Tenant Architecture (DEMO_MODE)
- Каждый пользователь получает свой tenant_id = Telegram ID
- Все данные (requests, complaints, warehouse_items) изолированы по tenant_id
- Техники работают с tenant_id своего руководителя
- Приоритетная логика: назначение техником отменяет статус руководителя

### Performance
- Кэширование часто используемых данных
- Пагинация для больших списков
- Асинхронная обработка задач
- Оптимизация запросов к БД

### Code Quality
- Модульность и переиспользование
- DRY (Don't Repeat Yourself)
- SOLID принципы
- Unit тесты для критичной логики
