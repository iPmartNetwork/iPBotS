"""Locale middleware for multi-language support."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from bot.config import settings


class LocaleMiddleware(BaseMiddleware):
    """Middleware to set user locale."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Get user language from db_user if available
        db_user = data.get("db_user")
        if db_user:
            data["locale"] = db_user.language
        else:
            data["locale"] = settings.DEFAULT_LANGUAGE

        return await handler(event, data)
