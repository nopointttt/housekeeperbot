"""Настройка подключения к базе данных"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from bot.config import config
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def normalize_database_url(url: str) -> str:
    """Нормализовать URL базы данных для asyncpg.

    - Приводит схему Render `postgres://` / `postgresql://` к `postgresql+asyncpg://`
    - Убирает SSL query-параметры (asyncpg не принимает sslmode как keyword argument)
    """
    # Парсим URL
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    # Render часто выдаёт postgres://... или postgresql://...
    # SQLAlchemy async engine ожидает dialect+driver: postgresql+asyncpg://...
    scheme = parsed.scheme.lower()
    if scheme in {"postgres", "postgresql"}:
        parsed = parsed._replace(scheme="postgresql+asyncpg")
    
    # Удаляем SSL параметры из URL (они будут переданы через connect_args)
    # asyncpg не принимает sslmode как keyword argument в connect()
    if 'sslmode' in query_params:
        query_params.pop('sslmode')
    if 'ssl' in query_params:
        query_params.pop('ssl')
    if 'channel_binding' in query_params:
        query_params.pop('channel_binding')
    
    # Собираем URL обратно без SSL параметров
    new_query = urlencode(query_params, doseq=True)
    fixed_url = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment,
        )
    )
    
    return fixed_url


def get_connect_args():
    """Получить параметры подключения для asyncpg"""
    url = config.database_url
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    connect_args = {}
    
    # Определяем, нужен ли SSL
    needs_ssl = False
    if 'sslmode' in query_params:
        sslmode = query_params['sslmode'][0].lower()
        needs_ssl = sslmode in ['require', 'verify-ca', 'verify-full']
    elif 'ssl' in query_params:
        ssl_value = query_params['ssl'][0].lower()
        needs_ssl = ssl_value in ['true', '1', 'yes']
    
    # Для asyncpg используем SSL контекст
    if needs_ssl:
        import ssl
        connect_args['ssl'] = ssl.create_default_context()
    
    return connect_args


# Создание async engine
# echo=False для production - SQL запросы не логируются
# Для отладки можно установить echo=True в .env через LOG_LEVEL=DEBUG
engine = create_async_engine(
    normalize_database_url(config.database_url),
    echo=config.log_level.upper() == "DEBUG",  # Логирование SQL только в DEBUG режиме
    future=True,
    connect_args=get_connect_args(),
)

# Создание session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base класс для моделей
Base = declarative_base()


async def get_session() -> AsyncSession:
    """Dependency для получения сессии БД"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Инициализация базы данных (создание таблиц)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Закрытие подключений к БД"""
    await engine.dispose()

