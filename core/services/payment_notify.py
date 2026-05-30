"""Payment notification service - sends to group/topic with action buttons."""

from typing import Optional
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

from bot.config import settings


class PaymentNotifyService:
    """Send payment notifications to configured group/topic."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.group_id = settings.PAYMENT_GROUP_ID

    def _get_keyboard(self, payment_id: int) -> InlineKeyboardMarkup:
        """Get approve/reject/ban keyboard."""
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ تأیید",
                        callback_data=f"gpay:approve:{payment_id}",
                    ),
                    InlineKeyboardButton(
                        text="❌ رد",
                        callback_data=f"gpay:reject:{payment_id}",
                    ),
                    InlineKeyboardButton(
                        text="🚫 رد و بن",
                        callback_data=f"gpay:ban:{payment_id}",
                    ),
                ]
            ]
        )

    async def notify_card2card_wallet(
        self,
        payment_id: int,
        user_name: str,
        user_id: int,
        amount: int,
        file_id: Optional[str] = None,
    ):
        """Notify card2card payment for wallet charge."""
        if not self.group_id:
            return

        topic_id = settings.PAYMENT_TOPIC_CARD2CARD_WALLET or None
        text = (
            f"🏦 <b>شارژ کیف پول (کارت به کارت)</b>\n\n"
            f"👤 کاربر: {user_name}\n"
            f"🆔 شناسه: <code>{user_id}</code>\n"
            f"💰 مبلغ: <b>{amount:,}</b> تومان\n"
            f"📌 شماره پرداخت: #{payment_id}"
        )

        try:
            if file_id:
                await self.bot.send_photo(
                    self.group_id,
                    photo=file_id,
                    caption=text,
                    reply_markup=self._get_keyboard(payment_id),
                    message_thread_id=topic_id,
                )
            else:
                await self.bot.send_message(
                    self.group_id,
                    text,
                    reply_markup=self._get_keyboard(payment_id),
                    message_thread_id=topic_id,
                )
        except Exception as e:
            logger.error(f"Payment notify (wallet card2card) failed: {e}")

    async def notify_card2card_purchase(
        self,
        payment_id: int,
        user_name: str,
        user_id: int,
        amount: int,
        plan_name: str = "",
        file_id: Optional[str] = None,
    ):
        """Notify card2card payment for direct purchase."""
        if not self.group_id:
            return

        topic_id = settings.PAYMENT_TOPIC_CARD2CARD_PURCHASE or None
        text = (
            f"🛒 <b>خرید مستقیم (کارت به کارت)</b>\n\n"
            f"👤 کاربر: {user_name}\n"
            f"🆔 شناسه: <code>{user_id}</code>\n"
            f"💰 مبلغ: <b>{amount:,}</b> تومان\n"
            f"📋 پلن: {plan_name}\n"
            f"📌 شماره پرداخت: #{payment_id}"
        )

        try:
            if file_id:
                await self.bot.send_photo(
                    self.group_id,
                    photo=file_id,
                    caption=text,
                    reply_markup=self._get_keyboard(payment_id),
                    message_thread_id=topic_id,
                )
            else:
                await self.bot.send_message(
                    self.group_id,
                    text,
                    reply_markup=self._get_keyboard(payment_id),
                    message_thread_id=topic_id,
                )
        except Exception as e:
            logger.error(f"Payment notify (purchase card2card) failed: {e}")

    async def notify_online_payment(
        self,
        payment_id: int,
        user_name: str,
        user_id: int,
        amount: int,
        method: str,
        status: str,
        ref_id: str = "",
    ):
        """Notify online payment result (success/fail)."""
        if not self.group_id:
            return

        topic_id = settings.PAYMENT_TOPIC_ONLINE or None
        status_icon = "✅" if status == "success" else "❌"
        text = (
            f"{status_icon} <b>پرداخت آنلاین ({method})</b>\n\n"
            f"👤 کاربر: {user_name}\n"
            f"🆔 شناسه: <code>{user_id}</code>\n"
            f"💰 مبلغ: <b>{amount:,}</b> تومان\n"
            f"📊 وضعیت: {'موفق' if status == 'success' else 'ناموفق'}\n"
        )
        if ref_id:
            text += f"🔗 شماره پیگیری: <code>{ref_id}</code>\n"
        text += f"📌 شماره پرداخت: #{payment_id}"

        try:
            await self.bot.send_message(
                self.group_id,
                text,
                message_thread_id=topic_id,
            )
        except Exception as e:
            logger.error(f"Payment notify (online) failed: {e}")
