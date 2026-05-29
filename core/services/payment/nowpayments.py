"""NowPayments crypto payment service."""

import hashlib
import hmac
import json
from typing import Optional

import aiohttp
from loguru import logger

from bot.config import settings
from core.services.payment.base import BasePaymentService, PaymentResult, VerifyResult


class NowPaymentsService(BasePaymentService):
    """NowPayments cryptocurrency payment service."""

    BASE_URL = "https://api.nowpayments.io/v1"

    def __init__(self):
        self.api_key = settings.NOWPAYMENTS_API_KEY
        self.ipn_secret = settings.NOWPAYMENTS_IPN_SECRET
        self.callback_url = settings.NOWPAYMENTS_CALLBACK_URL

    def _headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    async def create_payment(
        self,
        amount: int,
        description: str,
        order_id: str,
        user_email: Optional[str] = None,
        user_phone: Optional[str] = None,
    ) -> PaymentResult:
        """Create NowPayments invoice."""
        try:
            payload = {
                "price_amount": amount,
                "price_currency": "usd",
                "order_id": order_id,
                "order_description": description,
                "ipn_callback_url": self.callback_url,
                "success_url": f"{self.callback_url}?status=success",
                "cancel_url": f"{self.callback_url}?status=cancel",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/invoice",
                    headers=self._headers(),
                    json=payload,
                ) as resp:
                    data = await resp.json()

                    if "invoice_url" in data:
                        return PaymentResult(
                            success=True,
                            payment_url=data["invoice_url"],
                            transaction_id=str(data.get("id", "")),
                        )
                    else:
                        error = data.get("message", "Unknown error")
                        logger.error(f"NowPayments create error: {error}")
                        return PaymentResult(success=False, error=error)

        except Exception as e:
            logger.error(f"NowPayments create error: {e}")
            return PaymentResult(success=False, error=str(e))

    async def verify_payment(self, authority: str, amount: int) -> VerifyResult:
        """Verify NowPayments payment status."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/payment/{authority}",
                    headers=self._headers(),
                ) as resp:
                    data = await resp.json()

                    status = data.get("payment_status", "")
                    if status in ("finished", "confirmed"):
                        return VerifyResult(
                            success=True,
                            ref_id=str(data.get("payment_id", "")),
                            amount=amount,
                        )
                    else:
                        return VerifyResult(
                            success=False,
                            error=f"Payment status: {status}",
                        )

        except Exception as e:
            logger.error(f"NowPayments verify error: {e}")
            return VerifyResult(success=False, error=str(e))

    def verify_ipn_signature(self, payload: dict, signature: str) -> bool:
        """Verify IPN callback signature."""
        sorted_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        computed = hmac.HMAC(
            self.ipn_secret.encode(),
            sorted_payload.encode(),
            hashlib.sha512,
        ).hexdigest()
        return hmac.compare_digest(computed, signature)
