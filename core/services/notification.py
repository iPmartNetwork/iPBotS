"""Notification service for sending messages to users and admins."""

from typing import List, Optional

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from loguru import logger

from bot.config import settings


class NotificationService:
    """Service for sending notifications."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def notify_admins(
        self,
        message: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ):
        """Send notification to all admins."""
        for admin_id in settings.ADMIN_IDS:
            try:
                await self.bot.send_message(
                    admin_id, message, reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

    async def notify_user(
        self,
        user_id: int,
        message: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> bool:
        """Send notification to a user."""
        try:
            await self.bot.send_message(
                user_id, message, reply_markup=reply_markup
            )
            return True
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")
            return False

    async def broadcast(
        self,
        user_ids: List[int],
        message: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None,
    ) -> dict:
        """Broadcast message to multiple users."""
        results = {"success": 0, "failed": 0, "blocked": 0}

        for user_id in user_ids:
            try:
                await self.bot.send_message(
                    user_id, message, reply_markup=reply_markup
                )
                results["success"] += 1
            except Exception as e:
                error_msg = str(e).lower()
                if "blocked" in error_msg or "deactivated" in error_msg:
                    results["blocked"] += 1
                else:
                    results["failed"] += 1

        return results

    async def notify_new_order(self, user_id: int, order_info: str):
        """Notify admins about new order."""
        message = f"🛒 <b>سفارش جدید</b>\n\n{order_info}"
        await self.notify_admins(message)

    async def notify_payment_received(self, user_id: int, amount: int, method: str):
        """Notify admins about received payment."""
        message = (
            f"💰 <b>پرداخت جدید</b>\n\n"
            f"کاربر: <code>{user_id}</code>\n"
            f"مبلغ: {amount:,} تومان\n"
            f"روش: {method}"
        )
        await self.notify_admins(message)

    async def notify_subscription_expiring(self, user_id: int, days_left: int):
        """Notify user about expiring subscription."""
        message = (
            f"⚠️ <b>اخطار انقضا</b>\n\n"
            f"سرویس شما تا {days_left} روز دیگر منقضی می‌شود.\n"
            f"برای تمدید از منوی «سرویس‌های من» اقدام کنید."
        )
        await self.notify_user(user_id, message)

    async def notify_subscription_created(self, user_id: int, sub_info: str):
        """Notify user about new subscription."""
        message = f"✅ <b>سرویس فعال شد!</b>\n\n{sub_info}"
        await self.notify_user(user_id, message)

    async def notify_ticket_reply(self, user_id: int, ticket_id: int):
        """Notify user about ticket reply."""
        message = (
            f"📩 <b>پاسخ جدید</b>\n\n"
            f"تیکت #{ticket_id} پاسخ جدیدی دریافت کرد."
        )
        await self.notify_user(user_id, message)
