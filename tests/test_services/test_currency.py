"""Tests for CurrencyService."""

import pytest
from core.services.currency import CurrencyService, FALLBACK_RATES, CURRENCY_SYMBOLS


class TestCurrencyService:
    """Test currency conversion and formatting."""

    def setup_method(self):
        self.service = CurrencyService()

    def test_same_currency_no_conversion(self):
        """Same currency returns same amount."""
        assert self.service.convert(100000, "IRT", "IRT") == 100000
        assert self.service.convert(50, "USD", "USD") == 50

    def test_irt_to_usd(self):
        """Convert Toman to USD."""
        # 62,000 Toman = ~1 USD
        result = self.service.get_price_in_currency(62000, "USD")
        assert result == pytest.approx(1.0, abs=0.1)

    def test_format_price_toman(self):
        """Format price in Toman."""
        formatted = self.service.format_price(50000, "IRT")
        assert "50,000" in formatted
        assert "تومان" in formatted

    def test_format_price_usd(self):
        """Format price in USD."""
        formatted = self.service.format_price(10, "USD")
        assert "$" in formatted

    def test_format_price_eur(self):
        """Format price in EUR."""
        formatted = self.service.format_price(10, "EUR")
        assert "€" in formatted

    def test_format_price_try(self):
        """Format price in Turkish Lira."""
        formatted = self.service.format_price(100, "TRY")
        assert "₺" in formatted

    def test_get_price_in_currency_irt(self):
        """IRT returns same price."""
        assert self.service.get_price_in_currency(50000, "IRT") == 50000

    def test_get_price_in_currency_usd(self):
        """USD conversion from Toman."""
        result = self.service.get_price_in_currency(620000, "USD")
        assert result == pytest.approx(10.0, abs=0.5)

    def test_convert_zero_amount(self):
        """Zero amount stays zero."""
        assert self.service.convert(0, "IRT", "USD") == 0

    def test_fallback_rates_exist(self):
        """All expected currencies have fallback rates."""
        expected = ["IRR", "IRT", "USD", "EUR", "TRY", "RUB", "AED"]
        for currency in expected:
            assert currency in FALLBACK_RATES

    def test_currency_symbols_exist(self):
        """All display currencies have symbols."""
        expected = ["IRT", "USD", "EUR", "TRY", "RUB", "AED"]
        for currency in expected:
            assert currency in CURRENCY_SYMBOLS
