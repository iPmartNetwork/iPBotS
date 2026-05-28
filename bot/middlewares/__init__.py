"""Middlewares."""

from aiogram import Dispatcher

from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.throttle import ThrottleMiddleware
from bot.middlewares.locale import LocaleMiddleware


def register_all_middlewares(dp: Dispatcher):
    """Register all middlewares."""
    dp.message.middleware(ThrottleMiddleware())
    dp.message.middleware(AuthMiddleware())
    dp.message.middleware(LocaleMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.callback_query.middleware(LocaleMiddleware())
