"""ZarinPal payment service."""

from typing import Optional

import aiohttp
from loguru import logger

from bot.config import settings
from core.services.payment.base import BasePaymentService, PaymentResult, VerifyResult


class ZarinPalService(BasePaymentService):
    """ZarinPal payment gateway service."""

    SANDBOX_URL = "https://sandbox.zarinpal.com/pg/v4/payment"
    PRODUCTION_URL = "https://api.zarinpal.com/pg/v4/payment"
    SANDBOX_STARTPAY = "https://sandbox.zarinpal.com/pg/StartPay"
    PRODUCTION_STARTPAY = "https://www.zarinpal.com/pg/StartPay"

    def __init__(self):
        self.merchant_id = settings.ZARINPAL_MERCHANT_ID
        self.sandbox = settings.ZARINPAL_SANDBOX
        self.callback_url = settings.ZARINPAL_CALLBACK_URL
        self.base_url = self.SANDBOX_URL if self.sandbox else self.PRODUCTION_URL
        self.startpay_url = self.SANDBOX_STARTPAY if self.sandbox else self.PRODUCTION_STARTPAY

    async def create_payment(
        self,
        amount: int,
        description: str,
        order_id: str,
        user_email: Optional[str] = None,
        user_phone: Optional[str] = None,
    ) -> PaymentResult:
        """Create ZarinPal payment request."""
        try:
            payload = {
                "merchant_id": self.merchant_id,
                "amount": amount * 10,  # Convert Toman to Rial
                "description": description,
                "callback_url": f"{self.callback_url}?order_id={order_id}",
                "metadata": {"order_id": order_id},
            }
            if user_email:
                payload["metadata"]["email"] = user_email
            if user_phone:
                payload["metadata"]["mobile"] = user_phone

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/request.json",
                    json=payload,
                ) as resp:
                    data = await resp.json()

                    if data.get("data", {}).get("code") == 100:
                        authority = data["data"]["authority"]
                        payment_url = f"{self.startpay_url}/{authority}"
                        return PaymentResult(
                            success=True,
                            payment_url=payment_url,
                            transaction_id=authority,
                        )
                    else:
                        error_msg = str(data.get("errors", "Unknown error"))
                        logger.error(f"ZarinPal create error: {error_msg}")
                        return PaymentResult(success=False, error=error_msg)

        except Exception as e:
            logger.error(f"ZarinPal create payment error: {e}")
            return PaymentResult(success=False, error=str(e))

    async def verify_payment(self, authority: str, amount: int) -> VerifyResult:
        """Verify ZarinPal payment."""
        try:
            payload = {
                "merchant_id": self.merchant_id,
                "amount": amount * 10,  # Rial
                "authority": authority,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/verify.json",
                    json=payload,
                ) as resp:
                    data = await resp.json()

                    code = data.get("data", {}).get("code")
                    if code in (100, 101):
                        ref_id = str(data["data"].get("ref_id", ""))
                        return VerifyResult(
                            success=True,
                            ref_id=ref_id,
                            amount=amount,
                        )
                    else:
                        error_msg = str(data.get("errors", "Verification failed"))
                        return VerifyResult(success=False, error=error_msg)

        except Exception as e:
            logger.error(f"ZarinPal verify error: {e}")
            return VerifyResult(success=False, error=str(e))
