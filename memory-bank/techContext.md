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

