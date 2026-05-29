"""IDPay payment gateway service."""
from typing import Optional
import aiohttp
from loguru import logger
from bot.config import settings
from core.services.payment.base import BasePaymentService, PaymentResult, VerifyResult


class IDPayService(BasePaymentService):
    """IDPay.ir payment gateway."""

    BASE_URL = "https://api.idpay.ir/v1.1"

    def __init__(self):
        self.api_key = getattr(settings, "IDPAY_API_KEY", "")
        self.sandbox = getattr(settings, "IDPAY_SANDBOX", False)
        self.callback_url = getattr(settings, "IDPAY_CALLBACK_URL", "")

    def _headers(self) -> dict:
        headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key,
        }
        if self.sandbox:
            headers["X-SANDBOX"] = "1"
        return headers

    async def create_payment(self, amount, description, order_id, user_email=None, user_phone=None) -> PaymentResult:
        try:
            payload = {
                "order_id": order_id,
                "amount": amount * 10,  # Toman to Rial
                "desc": description,
                "callback": f"{self.callback_url}?order_id={order_id}",
            }
            if user_phone:
                payload["phone"] = user_phone
            if user_email:
                payload["mail"] = user_email

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/payment",
                    headers=self._headers(),
                    json=payload,
                ) as resp:
                    data = await resp.json()
                    if "link" in data:
                        return PaymentResult(
                            success=True,
                            payment_url=data["link"],
                            transaction_id=data.get("id", ""),
                        )
                    return PaymentResult(success=False, error=str(data.get("error_message", "Unknown")))
        except Exception as e:
            return PaymentResult(success=False, error=str(e))

    async def verify_payment(self, authority: str, amount: int) -> VerifyResult:
        try:
            payload = {"id": authority, "order_id": ""}
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/payment/verify",
                    headers=self._headers(),
                    json=payload,
                ) as resp:
                    data = await resp.json()
                    if data.get("status") in (100, 101, 200):
                        return VerifyResult(success=True, ref_id=str(data.get("track_id", "")), amount=amount)
                    return VerifyResult(success=False, error=str(data.get("error_message", "")))
        except Exception as e:
            return VerifyResult(success=False, error=str(e))
