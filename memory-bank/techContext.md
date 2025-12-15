# Technical Context

## Technology Stack
- **Language:** Python 3.11+
- **Framework:** aiogram 3.x (Telegram Bot API)
- **Database:** Neon SQL (PostgreSQL)
- **File Storage:** Cloudflare R2 (или ссылки на файлы Telegram)
- **Deployment:** Cloudflare Workers/Pages (webhook) или Railway.app/Render (fallback)
- **Scheduler:** Cloudflare Cron Triggers (для автоматических уведомлений)

## Dependencies
- aiogram 3.x - Telegram Bot framework
- asyncpg - PostgreSQL async driver
- python-dotenv - Environment variables
- aiosqlite - для локальной разработки (опционально)
- pytz - работа с часовыми поясами

## Development Environment
- Python 3.11+
- Virtual environment (venv)
- .env файл для конфигурации
- Локальная разработка: SQLite или Neon SQL
- Telegram Bot Token от @BotFather

## Deployment
- **Основной вариант:** Cloudflare Workers/Pages с webhook
- **Fallback:** Railway.app или Render (если Workers не подойдёт)
- **Database:** Neon SQL (PostgreSQL) - облачная база
- **Environment Variables:** Все настройки через env переменные
- **Bot Mode:** Webhook (для Cloudflare) или Polling (для других платформ)

## Environment Variables
- `BOT_TOKEN` - Telegram Bot Token от @BotFather
- `DATABASE_URL` - строка подключения к PostgreSQL
- `WAREHOUSEMAN_ID` - Telegram ID техника (в продакшн режиме)
- `MANAGER_ID` - Telegram ID руководителя (в продакшн режиме)
- `ALLOWED_EMPLOYEE_IDS` - список разрешенных Telegram ID (через запятую, в продакшн режиме)
- `DEMO_MODE` - демо-режим (true/false), включает публичный доступ и изоляцию данных
- `PUBLIC_ACCESS` - публичный доступ без allowlist (true/false)
- `BOT_PUBLIC_URL` - публичная ссылка на бота для отображения в /start (например: https://t.me/housekeeperrrrrbot)

## Demo Mode Features
- Публичный доступ без allowlist (`DEMO_MODE=true`)
- Изоляция данных через `tenant_id` (каждый пользователь = свой tenant_id)
- Ограничение тестового доступа 7 днями
- Управление техниками (назначение техников руководителям)
- Приоритетная логика: техники работают с tenant_id руководителя

