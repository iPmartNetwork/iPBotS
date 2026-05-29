"""Middlewares."""

from aiogram import Dispatcher

from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.throttle import ThrottleMiddleware
from bot.middlewares.locale import LocaleMiddleware
from bot.middlewares.forced_join import ForcedJoinMiddleware
from bot.middlewares.antispam import AntiSpamMiddleware


def register_all_middlewares(dp: Dispatcher):
    """Register all middlewares."""
    dp.message.middleware(AntiSpamMiddleware(max_messages=5, window_seconds=10))
    dp.message.middleware(ForcedJoinMiddleware())
    dp.message.middleware(ThrottleMiddleware())
    dp.message.middleware(AuthMiddleware())
    dp.message.middleware(LocaleMiddleware())
    dp.callback_query.middleware(ForcedJoinMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.callback_query.middleware(LocaleMiddleware())
