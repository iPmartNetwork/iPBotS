"""Tests for DynamicPricingService."""

import pytest
from unittest.mock import patch
from datetime import datetime, timezone

from core.services.dynamic_pricing import DynamicPricingService


class TestDynamicPricing:
    """Test dynamic pricing calculations."""

    def setup_method(self):
        self.service = DynamicPricingService()

    def test_no_discount_during_peak(self):
        """No discount during peak hours on non-low-demand days."""
        # Wednesday at 12:00 UTC (peak hour, not low-demand day)
        mock_dt = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)  # Wednesday
        with patch("core.services.dynamic_pricing.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

            result = self.service.calculate_discount(100000, user_purchases=0)

        assert result["discount_percent"] == 0
        assert result["final_price"] == 100000
        assert result["reason"] == ""

    def test_off_peak_discount(self):
        """Discount applied during off-peak hours (1-6 AM)."""
        # 3 AM UTC on Wednesday
        mock_dt = datetime(2026, 5, 27, 3, 0, tzinfo=timezone.utc)
        with patch("core.services.dynamic_pricing.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

            result = self.service.calculate_discount(100000, user_purchases=0)

        assert result["discount_percent"] == 10
        assert result["final_price"] == 90000
        assert "کم‌ترافیک" in result["reason"]

    def test_low_demand_day_discount(self):
        """Discount on Monday/Tuesday."""
        # Monday at 12:00 UTC
        mock_dt = datetime(2026, 5, 25, 12, 0, tzinfo=timezone.utc)  # Monday
        with patch("core.services.dynamic_pricing.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

            result = self.service.calculate_discount(100000, user_purchases=0)

        assert result["discount_percent"] == 5
        assert result["final_price"] == 95000
        assert "کم‌تقاضا" in result["reason"]

    def test_loyalty_discount(self):
        """Loyalty discount for returning customers (5+ purchases)."""
        # Wednesday at 12:00 (no time/day discount)
        mock_dt = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
        with patch("core.services.dynamic_pricing.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

            result = self.service.calculate_discount(100000, user_purchases=5)

        assert result["discount_percent"] == 5
        assert result["final_price"] == 95000
        assert "وفادار" in result["reason"]

    def test_combined_discounts(self):
        """Multiple discounts stack up."""
        # Monday at 3 AM + loyal customer = 10 + 5 + 5 = 20%
        mock_dt = datetime(2026, 5, 25, 3, 0, tzinfo=timezone.utc)  # Monday 3AM
        with patch("core.services.dynamic_pricing.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

            result = self.service.calculate_discount(100000, user_purchases=5)

        assert result["discount_percent"] == 20
        assert result["final_price"] == 80000

    def test_max_discount_cap(self):
        """Discount capped at 25%."""
        # Tuesday at 3 AM + loyal = 10 + 5 + 5 = 20% (under cap)
        mock_dt = datetime(2026, 5, 26, 3, 0, tzinfo=timezone.utc)  # Tuesday 3AM
        with patch("core.services.dynamic_pricing.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

            result = self.service.calculate_discount(100000, user_purchases=10)

        assert result["discount_percent"] <= 25

    def test_original_price_preserved(self):
        """Original price is always returned."""
        mock_dt = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
        with patch("core.services.dynamic_pricing.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)

            result = self.service.calculate_discount(75000, user_purchases=0)

        assert result["original_price"] == 75000

    def test_is_off_peak(self):
        """is_off_peak returns correct value."""
        mock_dt = datetime(2026, 5, 27, 3, 0, tzinfo=timezone.utc)
        with patch("core.services.dynamic_pricing.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            assert self.service.is_off_peak() is True

    def test_is_not_off_peak(self):
        """is_off_peak returns False during peak."""
        mock_dt = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
        with patch("core.services.dynamic_pricing.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            assert self.service.is_off_peak() is False
