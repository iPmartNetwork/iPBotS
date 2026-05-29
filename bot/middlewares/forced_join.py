"""Forced channel join middleware."""
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    TelegramObject,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from core.database.engine import get_session
from core.database.models.forced_join import ForcedChannel


class ForcedJoinMiddleware(BaseMiddleware):
    """Check if user has joined required channels."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Skip for callbacks that check membership
        if isinstance(event, CallbackQuery) and event.data and event.data.startswith("check_join"):
            return await handler(event, data)

        bot: Bot = data.get("bot")
        user_id = None

        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            # Skip /start command to allow registration
            if event.text and event.text.startswith("/start"):
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None

        if not user_id or not bot:
            return await handler(event, data)

        # Get forced channels
        try:
            async with get_session() as session:
                stmt = select(ForcedChannel).where(ForcedChannel.is_active == True)
                result = await session.execute(stmt)
                channels = result.scalars().all()
        except Exception:
            return await handler(event, data)

        if not channels:
            return await handler(event, data)

        # Check membership
        not_joined = []
        for channel in channels:
            try:
                member = await bot.get_chat_member(channel.channel_id, user_id)
                if member.status in ("left", "kicked"):
                    not_joined.append(channel)
            except Exception:
                pass  # Skip if can't check

        if not_joined:
            builder = InlineKeyboardBuilder()
            for ch in not_joined:
                builder.row(InlineKeyboardButton(
                    text=f"📢 {ch.channel_name}",
                    url=ch.channel_url,
                ))
            builder.row(InlineKeyboardButton(
                text="✅ عضو شدم",
                callback_data="check_join",
            ))

            text = "⚠️ <b>عضویت اجباری</b>\n\nبرای استفاده از ربات، ابتدا در کانال‌های زیر عضو شوید:"

            if isinstance(event, Message):
                await event.answer(text, reply_markup=builder.as_markup())
            elif isinstance(event, CallbackQuery):
                await event.answer("⚠️ ابتدا در کانال‌ها عضو شوید.", show_alert=True)
            return

        return await handler(event, data)
