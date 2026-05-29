"""Anti-spam middleware."""
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from bot.loader import redis


class AntiSpamMiddleware(BaseMiddleware):
    """Prevent spam by limiting message rate per user."""

    def __init__(self, max_messages: int = 5, window_seconds: int = 10):
        self.max_messages = max_messages
        self.window = window_seconds

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        key = f"antispam:{user_id}"

        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, self.window)

            if count > self.max_messages:
                # User is spamming
                if count == self.max_messages + 1:
                    await event.answer("🚫 <b>ضد اسپم</b>\n\nلطفاً کمی صبر کنید و دوباره تلاش کنید.")
                return  # Drop message
        except Exception:
            pass

        return await handler(event, data)
