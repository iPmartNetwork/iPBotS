"""Automated marketing messages service."""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import List

from sqlalchemy import select, func, and_
from loguru import logger

from core.database.engine import get_session
from core.database.models import User, Subscription, SubscriptionStatus, Order, OrderStatus


class MarketingService:
    """Service for automated marketing messages."""

    async def get_inactive_users(self, days: int = 7) -> List[User]:
        """Get users who haven't been active for X days."""
        threshold = datetime.now(timezone.utc) - timedelta(days=days)

        async with get_session() as session:
            stmt = (
                select(User)
                .where(
                    User.is_active == True,
                    User.is_banned == False,
                    User.last_activity < threshold,
                )
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_expired_no_renew_users(self) -> List[User]:
        """Get users whose subscription expired but didn't renew."""
        now = datetime.now(timezone.utc)
        three_days_ago = now - timedelta(days=3)

        async with get_session() as session:
            # Users with recently expired subs who haven't bought new ones
            stmt = (
                select(User)
                .join(Subscription, Subscription.user_id == User.id)
                .where(
                    Subscription.status == SubscriptionStatus.EXPIRED,
                    Subscription.expire_date >= three_days_ago,
                    Subscription.expire_date < now,
                    User.is_banned == False,
                )
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_users_never_purchased(self, days_since_join: int = 3) -> List[User]:
        """Get users who joined X days ago but never purchased."""
        threshold = datetime.now(timezone.utc) - timedelta(days=days_since_join)

        async with get_session() as session:
            stmt = (
                select(User)
                .where(
                    User.is_active == True,
                    User.is_banned == False,
                    User.total_purchases == 0,
                    User.created_at <= threshold,
                )
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_high_value_users(self, min_spent: int = 500000) -> List[User]:
        """Get high-value users for VIP offers."""
        async with get_session() as session:
            stmt = (
                select(User)
                .where(
                    User.is_active == True,
                    User.is_banned == False,
                    User.total_spent >= min_spent,
                )
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def send_inactive_reminder(self):
        """Send reminder to inactive users."""
        users = await self.get_inactive_users(days=7)
        if not users:
            return

        from bot.loader import bot

        message = (
            "👋 سلام! مدتیه ندیدیمت.\n\n"
            "🎁 یه تخفیف ویژه برات داریم!\n"
            "با کد <code>COMEBACK20</code> روی خرید بعدیت 20% تخفیف بگیر.\n\n"
            "⏰ این کد فقط تا 48 ساعت آینده معتبره."
        )

        sent = 0
        for user in users:
            try:
                await bot.send_message(user.telegram_id, message)
                sent += 1
                if sent % 25 == 0:
                    await asyncio.sleep(1)
            except Exception:
                pass

        logger.info(f"Sent inactive reminder to {sent}/{len(users)} users")

    async def send_expired_offer(self):
        """Send special offer to users with expired subscriptions."""
        users = await self.get_expired_no_renew_users()
        if not users:
            return

        from bot.loader import bot

        message = (
            "⚠️ سرویس شما منقضی شده!\n\n"
            "🔥 پیشنهاد ویژه تمدید:\n"
            "همین الان تمدید کنید و <b>15% تخفیف</b> بگیرید!\n\n"
            "💡 از منوی «سرویس‌های من» اقدام کنید.\n"
            "کد تخفیف: <code>RENEW15</code>"
        )

        sent = 0
        for user in users:
            try:
                await bot.send_message(user.telegram_id, message)
                sent += 1
                if sent % 25 == 0:
                    await asyncio.sleep(1)
            except Exception:
                pass

        logger.info(f"Sent expired offer to {sent}/{len(users)} users")

    async def send_first_purchase_nudge(self):
        """Nudge users who joined but never purchased."""
        users = await self.get_users_never_purchased(days_since_join=3)
        if not users:
            return

        from bot.loader import bot

        message = (
            "👋 هنوز سرویسی نخریدی؟\n\n"
            "🎁 <b>تست رایگان</b> رو امتحان کن!\n"
            "1 گیگ / 24 ساعت کاملاً رایگان.\n\n"
            "یا با کد <code>FIRST30</code> روی اولین خریدت "
            "<b>30% تخفیف</b> بگیر!\n\n"
            "🛒 از منوی «خرید سرویس» شروع کن."
        )

        sent = 0
        for user in users:
            try:
                await bot.send_message(user.telegram_id, message)
                sent += 1
                if sent % 25 == 0:
                    await asyncio.sleep(1)
            except Exception:
                pass

        logger.info(f"Sent first purchase nudge to {sent}/{len(users)} users")

    async def send_vip_offer(self):
        """Send exclusive offer to high-value users."""
        users = await self.get_high_value_users(min_spent=500000)
        if not users:
            return

        from bot.loader import bot

        message = (
            "⭐ <b>مشتری ویژه!</b>\n\n"
            "به خاطر خریدهای قبلیت، یه پیشنهاد اختصاصی داریم:\n\n"
            "💎 <b>پلن VIP نامحدود</b>\n"
            "ترافیک نامحدود | 90 روز | 3 کاربر همزمان\n"
            "با <b>25% تخفیف ویژه</b>\n\n"
            "کد: <code>VIP25</code>\n\n"
            "🙏 ممنون که همراه ما هستی!"
        )

        sent = 0
        for user in users:
            try:
                await bot.send_message(user.telegram_id, message)
                sent += 1
                if sent % 25 == 0:
                    await asyncio.sleep(1)
            except Exception:
                pass

        logger.info(f"Sent VIP offer to {sent}/{len(users)} users")

    async def send_traffic_warning(self):
        """Notify users who used 80%+ of their traffic."""
        async with get_session() as session:
            stmt = (
                select(Subscription)
                .where(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.data_limit_bytes > 0,
                )
            )
            result = await session.execute(stmt)
            subs = result.scalars().all()

        from bot.loader import bot

        sent = 0
        for sub in subs:
            if sub.traffic_percent >= 80 and sub.traffic_percent < 95:
                try:
                    await bot.send_message(
                        sub.user_id,
                        f"⚠️ <b>هشدار ترافیک</b>\n\n"
                        f"شما {sub.traffic_percent}% از ترافیک خود را مصرف کرده‌اید.\n"
                        f"📊 باقیمانده: {sub.remaining_traffic_gb} GB\n\n"
                        f"💡 برای جلوگیری از قطع سرویس، ارتقا دهید یا پلن جدید بخرید."
                    )
                    sent += 1
                except Exception:
                    pass

                if sent % 25 == 0:
                    await asyncio.sleep(1)

        logger.info(f"Sent traffic warnings to {sent} users")


# Singleton
marketing_service = MarketingService()
