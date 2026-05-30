"""Admin handlers."""

from aiogram import Dispatcher

from bot.handlers.admin.dashboard import router as dashboard_router
from bot.handlers.admin.users import router as users_router
from bot.handlers.admin.servers import router as servers_router
from bot.handlers.admin.plans import router as plans_router
from bot.handlers.admin.payments import router as payments_router
from bot.handlers.admin.broadcast import router as broadcast_router
from bot.handlers.admin.settings import router as settings_router
from bot.handlers.admin.export import router as export_router
from bot.handlers.admin.texts import router as texts_router


def register_admin_handlers(dp: Dispatcher):
    """Register all admin handlers."""
    dp.include_router(dashboard_router)
    dp.include_router(users_router)
    dp.include_router(servers_router)
    dp.include_router(plans_router)
    dp.include_router(payments_router)
    dp.include_router(broadcast_router)
    dp.include_router(settings_router)
    dp.include_router(export_router)
    dp.include_router(texts_router)
