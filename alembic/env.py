"""Alembic environment configuration"""
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
import asyncio
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Import Base and models
from bot.database.engine import Base
from bot.database.models import User, Request, RequestPhoto, WarehouseItem, Complaint
from bot.config import config

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
alembic_cfg = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if alembic_cfg.config_file_name is not None:
    fileConfig(alembic_cfg.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_url():
    """Получить URL базы данных из конфигурации и исправить параметры для asyncpg"""
    url = config.database_url
    
    # Парсим URL
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
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
    fixed_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))
    
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


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine"""
    # Используем create_async_engine напрямую, как в bot/database/engine.py
    # SSL параметры передаем через connect_args, а не через URL
    connectable = create_async_engine(
        get_url(),
        poolclass=pool.NullPool,
        echo=False,
        connect_args=get_connect_args(),
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

