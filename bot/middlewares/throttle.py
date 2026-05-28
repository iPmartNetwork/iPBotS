"""Rate limiting middleware."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from redis.asyncio import Redis

from bot.loader import redis


class ThrottleMiddleware(BaseMiddleware):
    """Rate limiting middleware using Redis."""

    def __init__(self, rate_limit: float = 0.5):
        """
        Args:
            rate_limit: Minimum seconds between messages per user.
        """
        self.rate_limit = rate_limit

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id if event.from_user else None
        if not user_id:
            return await handler(event, data)

        key = f"throttle:{user_id}"

        # Check if user is rate limited
        exists = await redis.exists(key)
        if exists:
            # User is sending too fast, ignore
            return

        # Set rate limit key
        await redis.setex(key, int(self.rate_limit * 1000) // 1000 or 1, "1")

        return await handler(event, data)
