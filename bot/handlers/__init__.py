"""Handlers registration."""

from aiogram import Dispatcher

from bot.handlers.user import register_user_handlers
from bot.handlers.admin import register_admin_handlers


def register_all_handlers(dp: Dispatcher):
    """Register all handlers."""
    register_user_handlers(dp)
    register_admin_handlers(dp)
