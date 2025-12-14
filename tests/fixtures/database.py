"""Fixtures для работы с тестовой базой данных"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool

# Используем собственный Base для тестов
TestBase = declarative_base()


def get_test_database_url() -> str:
    """URL для тестовой базы данных (SQLite в памяти)"""
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Создать event loop для всех тестов в сессии"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    """
    Создать тестовый engine для БД (SQLite в памяти)
    
    Создается новый для каждого теста для изоляции
    """
    # Импортируем модели для создания таблиц
    from bot.database.engine import Base
    
    engine = create_async_engine(
        get_test_database_url(),
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Удаляем таблицы после теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session_maker(test_engine):
    """Создать session maker для тестов"""
    session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    return session_maker


@pytest.fixture(scope="function")
async def test_session(test_session_maker) -> AsyncGenerator[AsyncSession, None]:
    """
    Создать тестовую сессию БД
    
    Каждый тест получает чистую сессию с автоматическим откатом
    """
    async with test_session_maker() as session:
        try:
            yield session
        finally:
            # Откатываем все изменения после теста
            await session.rollback()
            await session.close()


@pytest.fixture(scope="function")
async def test_session_with_commit(test_session_maker) -> AsyncGenerator[AsyncSession, None]:
    """
    Тестовая сессия с возможностью коммита
    
    Используется когда нужно проверить реальное сохранение данных
    """
    async with test_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

