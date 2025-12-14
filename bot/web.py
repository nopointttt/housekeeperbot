"""
HTTP wrapper for Render Web Service.

Render free tier works best when your process listens on $PORT.
This module starts a small FastAPI app for health checks and runs
the Telegram bot polling loop in the background.
"""

import asyncio
import contextlib
import logging
import sys
import traceback
from typing import Optional

from fastapi import FastAPI

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import config
from bot.database.engine import init_db, close_db


app = FastAPI(title="Housekeeper Bot")

logger = logging.getLogger(__name__)

_polling_task: Optional[asyncio.Task] = None
_startup_error: Optional[str] = None


async def _run_bot_polling() -> None:
    """Run aiogram polling loop (background)."""
    global _startup_error

    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    if log_level == logging.DEBUG:
        logging.getLogger("aiogram").setLevel(logging.DEBUG)
        logging.getLogger("aiogram.event").setLevel(logging.DEBUG)
    else:
        logging.getLogger("aiogram").setLevel(logging.WARNING)
        logging.getLogger("aiogram.event").setLevel(logging.WARNING)

    logger.info("Starting Telegram bot (polling) in background...")

    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        _startup_error = f"DB init failed: {e}"
        logger.error(_startup_error)
        await bot.session.close()
        return

    # Middlewares
    from bot.middlewares.role_middleware import RoleMiddleware

    dp.message.middleware(RoleMiddleware())
    dp.callback_query.middleware(RoleMiddleware())

    # Routers
    from bot.handlers import (
        start,
        common,
        settings,
        request_creation,
        employee,
        complaints,
        warehouseman,
        warehouse,
        warehouse_writeoff,
        broadcast,
        manager,
    )

    dp.include_router(start.router)
    dp.include_router(common.router)
    dp.include_router(settings.router)
    dp.include_router(request_creation.router)
    dp.include_router(employee.router)
    dp.include_router(complaints.router)
    dp.include_router(warehouseman.router)
    dp.include_router(warehouse.router)
    dp.include_router(warehouse_writeoff.router)
    dp.include_router(broadcast.router)
    dp.include_router(manager.router)

    # Scheduler
    from bot.services.scheduler import TaskScheduler

    scheduler = TaskScheduler(bot)
    await scheduler.start()

    try:
        logger.info("Bot polling started")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot runtime error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        try:
            await scheduler.stop()
        except Exception:
            pass
        try:
            await close_db()
        except Exception:
            pass
        try:
            await bot.session.close()
        except Exception:
            pass


@app.on_event("startup")
async def _startup() -> None:
    global _polling_task
    # Launch polling in background so we can still serve /health for Render.
    _polling_task = asyncio.create_task(_run_bot_polling())


@app.on_event("shutdown")
async def _shutdown() -> None:
    global _polling_task
    if _polling_task and not _polling_task.done():
        _polling_task.cancel()
        with contextlib.suppress(Exception):
            await _polling_task


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok" if _startup_error is None else "error",
        "startup_error": _startup_error,
    }


@app.get("/")
async def root() -> dict:
    return {"service": "housekeeper-bot", "health": "/health"}


