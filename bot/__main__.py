"""Entry point for the bot."""

import asyncio
import sys

from loguru import logger

from bot.config import settings
from bot.loader import bot, dp
from bot.handlers import register_all_handlers
from bot.middlewares import register_all_middlewares
from core.database.engine import create_db_engine, create_tables
from core.scheduler.jobs import start_scheduler


async def on_startup():
    """Actions on bot startup."""
    logger.info("Starting V2Ray Shop Bot (iPmart Network)...")

    # Create database tables
    await create_tables()
    logger.info("Database tables ready.")

    # Start scheduler
    start_scheduler()
    logger.info("Scheduler started.")

    # Set webhook or start polling
    if settings.WEBHOOK_ENABLED:
        webhook_url = f"{settings.WEBHOOK_HOST}{settings.WEBHOOK_PATH}"
        await bot.set_webhook(webhook_url, drop_pending_updates=True)
        logger.info(f"Webhook set: {webhook_url}")
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Polling mode enabled.")

    # Notify admins
    for admin_id in settings.admin_ids_list:
        try:
            await bot.send_message(admin_id, "✅ ربات iPBotS با موفقیت راه‌اندازی شد!\n© iPmart Network")
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

    logger.info("Bot started successfully!")


async def on_shutdown():
    """Actions on bot shutdown."""
    logger.info("Shutting down...")
    await bot.session.close()


async def main():
    """Main function."""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        level="DEBUG" if settings.APP_DEBUG else "INFO",
    )
    logger.add(
        "logs/bot_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        level="INFO",
    )

    # Register middlewares and handlers BEFORE starting
    register_all_middlewares(dp)
    logger.info("Middlewares registered.")

    register_all_handlers(dp)
    logger.info("Handlers registered.")

    # Register lifecycle hooks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    if not settings.WEBHOOK_ENABLED:
        # Polling mode
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    else:
        # Webhook mode - run startup manually then start server
        await on_startup()

        from api.app import run_webhook_server
        await run_webhook_server()


if __name__ == "__main__":
    asyncio.run(main())
