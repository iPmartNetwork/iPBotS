"""Authentication middleware - registers users and checks bans."""

import secrets
import string
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from sqlalchemy import select

from core.database.engine import get_session
from core.database.models import User, Wallet


def generate_referral_code(length: int = 8) -> str:
    """Generate a unique referral code."""
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


class AuthMiddleware(BaseMiddleware):
    """Middleware to authenticate users and register new ones."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Get user from event
        if isinstance(event, Message):
            telegram_user = event.from_user
        elif isinstance(event, CallbackQuery):
            telegram_user = event.from_user
        else:
            return await handler(event, data)

        if not telegram_user:
            return await handler(event, data)

        try:
            async with get_session() as session:
                # Find or create user
                stmt = select(User).where(User.telegram_id == telegram_user.id)
                result = await session.execute(stmt)
                user = result.scalar_one_or_none()

                if user is None:
                    # Register new user
                    # Check for referral
                    referrer_id = None
                    if isinstance(event, Message) and event.text:
                        parts = event.text.split()
                        if len(parts) > 1 and parts[0] == "/start":
                            ref_code = parts[1]
                            ref_stmt = select(User).where(User.referral_code == ref_code)
                            ref_result = await session.execute(ref_stmt)
                            referrer = ref_result.scalar_one_or_none()
                            if referrer:
                                referrer_id = referrer.id

                    user = User(
                        telegram_id=telegram_user.id,
                        username=telegram_user.username,
                        first_name=telegram_user.first_name or "",
                        last_name=telegram_user.last_name,
                        referral_code=generate_referral_code(),
                        referred_by_id=referrer_id,
                        last_activity=datetime.now(timezone.utc),
                    )
                    session.add(user)
                    await session.flush()

                    # Create wallet
                    wallet = Wallet(user_id=user.id)
                    session.add(wallet)

                else:
                    # Update user info
                    user.username = telegram_user.username
                    user.first_name = telegram_user.first_name or user.first_name
                    user.last_name = telegram_user.last_name
                    user.last_activity = datetime.now(timezone.utc)

                    # Check if banned
                    if user.is_banned:
                        if isinstance(event, Message):
                            await event.answer(
                                f"⛔ حساب شما مسدود شده است.\n"
                                f"دلیل: {user.ban_reason or 'نامشخص'}\n\n"
                                f"برای پیگیری با پشتیبانی تماس بگیرید."
                            )
                        elif isinstance(event, CallbackQuery):
                            await event.answer("⛔ حساب شما مسدود شده است.", show_alert=True)
                        return

                # Pass user to handler
                data["db_user"] = user
        except Exception as e:
            from loguru import logger
            logger.error(f"Auth middleware DB error: {e}")
            # Let the request through without db_user
            data["db_user"] = None
            return await handler(event, data)

        return await handler(event, data)
