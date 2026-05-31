"""Tests for ZarinPal payment service."""

import pytest
from unittest.mock import patch, MagicMock
from aioresponses import aioresponses


class TestZarinPalService:
    """Test ZarinPal payment operations."""

    def setup_method(self):
        with patch(
            "core.services.payment.zarinpal.settings"
        ) as mock_settings:
            mock_settings.ZARINPAL_MERCHANT_ID = "test-merchant-id"
            mock_settings.ZARINPAL_SANDBOX = True
            mock_settings.ZARINPAL_CALLBACK_URL = (
                "http://localhost/api/payment/zarinpal/callback"
            )

            from core.services.payment.zarinpal import ZarinPalService
            self.service = ZarinPalService()

    @pytest.mark.asyncio
    async def test_create_payment_success(self):
        """Successful payment creation."""
        sandbox_url = (
            "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
        )

        with aioresponses() as mocked:
            mocked.post(
                sandbox_url,
                payload={
                    "data": {
                        "authority": "A00000000000000000000000000123456",
                        "code": 100,
                    },
                    "errors": [],
                },
            )

            result = await self.service.create_payment(
                amount=50000,
                description="Test Plan",
                order_id="1",
            )

        assert result.success is True
        assert result.payment_url is not None
        assert "zarinpal" in result.payment_url.lower()

    @pytest.mark.asyncio
    async def test_create_payment_failure(self):
        """Failed payment creation."""
        sandbox_url = (
            "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
        )

        with aioresponses() as mocked:
            mocked.post(
                sandbox_url,
                payload={
                    "data": [],
                    "errors": {
                        "code": -9,
                        "message": "Invalid merchant",
                    },
                },
            )

            result = await self.service.create_payment(
                amount=50000,
                description="Test",
                order_id="1",
            )

        assert result.success is False

    @pytest.mark.asyncio
    async def test_create_payment_network_error(self):
        """Handles network errors gracefully."""
        sandbox_url = (
            "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
        )

        with aioresponses() as mocked:
            mocked.post(
                sandbox_url,
                exception=Exception("Connection refused"),
            )

            result = await self.service.create_payment(
                amount=50000,
                description="Test",
                order_id="1",
            )

        assert result.success is False
        assert result.error is not None
