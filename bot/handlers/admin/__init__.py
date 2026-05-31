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
from bot.handlers.admin.group_payments import router as group_payments_router
from bot.handlers.admin.leaderboard import router as leaderboard_router
from bot.handlers.admin.test_connection import router as test_connection_router
from bot.handlers.admin.ab_testing import router as ab_testing_router
from bot.handlers.admin.dynamic_pricing import router as dynamic_pricing_router


def register_admin_handlers(dp: Dispatcher):
    """Register all admin handlers."""
    dp.include_router(group_payments_router)
    dp.include_router(dashboard_router)
    dp.include_router(users_router)
    dp.include_router(servers_router)
    dp.include_router(plans_router)
    dp.include_router(payments_router)
    dp.include_router(broadcast_router)
    dp.include_router(settings_router)
    dp.include_router(export_router)
    dp.include_router(texts_router)
    dp.include_router(leaderboard_router)
    dp.include_router(test_connection_router)
    dp.include_router(ab_testing_router)
    dp.include_router(dynamic_pricing_router)
