"""User handlers."""

from aiogram import Dispatcher, Router

from bot.handlers.user.start import router as start_router
from bot.handlers.user.shop import router as shop_router
from bot.handlers.user.wallet import router as wallet_router
from bot.handlers.user.services import router as services_router
from bot.handlers.user.support import router as support_router
from bot.handlers.user.referral import router as referral_router
from bot.handlers.user.trial import router as trial_router
from bot.handlers.user.custom_plan import router as custom_plan_router
from bot.handlers.user.loyalty import router as loyalty_router
from bot.handlers.user.server_select import router as server_select_router
from bot.handlers.user.reseller import router as reseller_router
from bot.handlers.user.auto_renew import router as auto_renew_router
from bot.handlers.user.traffic_stats import router as traffic_stats_router
from bot.handlers.user.tutorial import router as tutorial_router
from bot.handlers.user.bundle import router as bundle_router
from bot.handlers.user.ai_chat import router as ai_chat_router


def register_user_handlers(dp: Dispatcher):
    """Register all user handlers."""
    dp.include_router(start_router)
    dp.include_router(shop_router)
    dp.include_router(wallet_router)
    dp.include_router(services_router)
    dp.include_router(support_router)
    dp.include_router(referral_router)
    dp.include_router(trial_router)
    dp.include_router(custom_plan_router)
    dp.include_router(loyalty_router)
    dp.include_router(server_select_router)
    dp.include_router(reseller_router)
    dp.include_router(auto_renew_router)
    dp.include_router(traffic_stats_router)
    dp.include_router(tutorial_router)
    dp.include_router(bundle_router)
    dp.include_router(ai_chat_router)
