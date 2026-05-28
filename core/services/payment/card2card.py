"""Card to Card (manual) payment service."""

from typing import Optional

from loguru import logger

from bot.config import settings
from core.services.payment.base import BasePaymentService, PaymentResult, VerifyResult


class Card2CardService(BasePaymentService):
    """Card to Card manual payment (requires admin verification)."""

    def __init__(self):
        self.card_number = settings.CARD2CARD_NUMBER
        self.card_holder = settings.CARD2CARD_HOLDER
        self.enabled = settings.CARD2CARD_ENABLED

    async def create_payment(
        self,
        amount: int,
        description: str,
        order_id: str,
        user_email: Optional[str] = None,
        user_phone: Optional[str] = None,
    ) -> PaymentResult:
        """Create card2card payment request (returns card info for user)."""
        if not self.enabled:
            return PaymentResult(success=False, error="Card2Card is disabled")

        # No URL needed - user will send receipt image
        return PaymentResult(
            success=True,
            payment_url=None,
            transaction_id=order_id,
        )

    async def verify_payment(self, authority: str, amount: int) -> VerifyResult:
        """
        Card2Card verification is manual (admin confirms).
        This method is called after admin approval.
        """
        return VerifyResult(
            success=True,
            ref_id=f"card2card_{authority}",
            amount=amount,
        )

    def get_payment_info(self, amount: int) -> str:
        """Get formatted payment info for user."""
        return (
            f"💳 <b>اطلاعات کارت:</b>\n\n"
            f"شماره کارت: <code>{self.card_number}</code>\n"
            f"به نام: {self.card_holder}\n"
            f"مبلغ: <b>{amount:,}</b> تومان\n\n"
            f"⚠️ پس از واریز، تصویر رسید را ارسال کنید."
        )
