"""Stripe payment gateway service."""
from typing import Optional
import aiohttp
from loguru import logger
from bot.config import settings
from core.services.payment.base import BasePaymentService, PaymentResult, VerifyResult


class StripeService(BasePaymentService):
    """Stripe payment gateway for international payments."""

    BASE_URL = "https://api.stripe.com/v1"

    def __init__(self):
        self.secret_key = getattr(settings, "STRIPE_SECRET_KEY", "")
        self.callback_url = getattr(settings, "STRIPE_CALLBACK_URL", "")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    async def create_payment(self, amount, description, order_id, user_email=None, user_phone=None) -> PaymentResult:
        """Create Stripe checkout session."""
        if not self.secret_key:
            return PaymentResult(success=False, error="Stripe not configured")

        try:
            payload = {
                "payment_method_types[]": "card",
                "line_items[0][price_data][currency]": "usd",
                "line_items[0][price_data][unit_amount]": str(amount),  # cents
                "line_items[0][price_data][product_data][name]": description,
                "line_items[0][quantity]": "1",
                "mode": "payment",
                "success_url": f"{self.callback_url}?session_id={{CHECKOUT_SESSION_ID}}&order_id={order_id}",
                "cancel_url": f"{self.callback_url}?cancelled=true",
                "metadata[order_id]": order_id,
            }
            if user_email:
                payload["customer_email"] = user_email

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/checkout/sessions",
                    headers=self._headers(),
                    data=payload,
                ) as resp:
                    data = await resp.json()
                    if "url" in data:
                        return PaymentResult(
                            success=True,
                            payment_url=data["url"],
                            transaction_id=data.get("id", ""),
                        )
                    return PaymentResult(success=False, error=data.get("error", {}).get("message", "Unknown"))
        except Exception as e:
            logger.error(f"Stripe create error: {e}")
            return PaymentResult(success=False, error=str(e))

    async def verify_payment(self, authority: str, amount: int) -> VerifyResult:
        """Verify Stripe payment by session ID."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/checkout/sessions/{authority}",
                    headers=self._headers(),
                ) as resp:
                    data = await resp.json()
                    if data.get("payment_status") == "paid":
                        return VerifyResult(
                            success=True,
                            ref_id=data.get("payment_intent", ""),
                            amount=amount,
                        )
                    return VerifyResult(success=False, error=f"Status: {data.get('payment_status')}")
        except Exception as e:
            return VerifyResult(success=False, error=str(e))
