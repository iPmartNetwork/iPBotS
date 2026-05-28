"""Admin filter."""

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery, TelegramObject

from bot.config import settings


class AdminFilter(BaseFilter):
    """Filter to check if user is admin."""

    async def __call__(self, event: TelegramObject) -> bool:
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else 0
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else 0
        else:
            return False

        return user_id in settings.ADMIN_IDS
