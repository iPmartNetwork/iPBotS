"""Tests for Stripe payment service."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from aioresponses import aioresponses

from core.services.payment.stripe_pay import StripeService


class TestStripeService:
    """Test Stripe payment operations."""

    def setup_method(self):
        with patch("core.services.payment.stripe_pay.settings") as mock_settings:
            mock_settings.STRIPE_SECRET_KEY = "sk_test_123"
            mock_settings.STRIPE_CALLBACK_URL = "http://localhost/stripe/callback"
            self.service = StripeService()
            self.service.secret_key = "sk_test_123"
            self.service.callback_url = "http://localhost/stripe/callback"

    @pytest.mark.asyncio
    async def test_create_payment_success(self):
        """Successful checkout session creation."""
        with aioresponses() as mocked:
            mocked.post(
                "https://api.stripe.com/v1/checkout/sessions",
                payload={
                    "id": "cs_test_123",
                    "url": "https://checkout.stripe.com/pay/cs_test_123",
                },
            )

            result = await self.service.create_payment(
                amount=1000,  # $10.00 in cents
                description="Test Plan",
                order_id="order_1",
                user_email="test@example.com",
            )

        assert result.success is True
        assert result.payment_url == "https://checkout.stripe.com/pay/cs_test_123"
        assert result.transaction_id == "cs_test_123"

    @pytest.mark.asyncio
    async def test_create_payment_failure(self):
        """Failed checkout session creation."""
        with aioresponses() as mocked:
            mocked.post(
                "https://api.stripe.com/v1/checkout/sessions",
                payload={
                    "error": {
                        "message": "Invalid API key",
                        "type": "authentication_error",
                    }
                },
            )

            result = await self.service.create_payment(
                amount=1000,
                description="Test Plan",
                order_id="order_1",
            )

        assert result.success is False
        assert "Invalid API key" in result.error

    @pytest.mark.asyncio
    async def test_create_payment_no_key(self):
        """Returns error when no secret key configured."""
        self.service.secret_key = ""

        result = await self.service.create_payment(
            amount=1000,
            description="Test",
            order_id="1",
        )

        assert result.success is False
        assert "not configured" in result.error

    @pytest.mark.asyncio
    async def test_verify_payment_success(self):
        """Successful payment verification."""
        with aioresponses() as mocked:
            mocked.get(
                "https://api.stripe.com/v1/checkout/sessions/cs_test_123",
                payload={
                    "payment_status": "paid",
                    "payment_intent": "pi_test_456",
                },
            )

            result = await self.service.verify_payment("cs_test_123", 1000)

        assert result.success is True
        assert result.ref_id == "pi_test_456"

    @pytest.mark.asyncio
    async def test_verify_payment_unpaid(self):
        """Verification fails for unpaid session."""
        with aioresponses() as mocked:
            mocked.get(
                "https://api.stripe.com/v1/checkout/sessions/cs_test_123",
                payload={
                    "payment_status": "unpaid",
                },
            )

            result = await self.service.verify_payment("cs_test_123", 1000)

        assert result.success is False

    @pytest.mark.asyncio
    async def test_verify_payment_network_error(self):
        """Handles network errors gracefully."""
        with aioresponses() as mocked:
            mocked.get(
                "https://api.stripe.com/v1/checkout/sessions/cs_test_123",
                exception=Exception("Connection timeout"),
            )

            result = await self.service.verify_payment("cs_test_123", 1000)

        assert result.success is False
        assert "timeout" in result.error.lower() or "Connection" in result.error
