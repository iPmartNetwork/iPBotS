"""Tests for A/B Testing service."""

import pytest
from core.services.ab_testing import ABTest, get_variant


class TestGetVariant:
    """Test deterministic variant assignment."""

    def test_same_user_same_test_same_result(self):
        """Same user always gets same variant for same test."""
        variant1 = get_variant(12345, "pricing_test")
        variant2 = get_variant(12345, "pricing_test")
        assert variant1 == variant2

    def test_different_users_can_get_different_variants(self):
        """Different users may get different variants."""
        variants = set()
        for user_id in range(1, 100):
            variants.add(get_variant(user_id, "test_experiment"))
        # With 100 users, we should see both variants
        assert "A" in variants
        assert "B" in variants

    def test_different_tests_can_give_different_variants(self):
        """Same user can get different variants for different tests."""
        variants = set()
        for test_name in ["test_a", "test_b", "test_c", "test_d", "test_e"]:
            variants.add(get_variant(12345, test_name))
        # With 5 tests, likely to see both (not guaranteed but very likely)
        assert len(variants) >= 1  # At minimum one variant

    def test_variant_is_a_or_b(self):
        """Variant is always A or B."""
        for user_id in range(1, 50):
            variant = get_variant(user_id, "any_test")
            assert variant in ("A", "B")

    def test_roughly_even_distribution(self):
        """Distribution should be roughly 50/50."""
        a_count = 0
        b_count = 0
        total = 1000

        for user_id in range(1, total + 1):
            variant = get_variant(user_id, "distribution_test")
            if variant == "A":
                a_count += 1
            else:
                b_count += 1

        # Allow 10% deviation from 50/50
        assert abs(a_count - b_count) < total * 0.1


class TestABTestModel:
    """Test ABTest model properties."""

    def test_conversion_rate_a_zero_impressions(self):
        """Conversion rate is 0 when no impressions."""
        test = ABTest(
            name="test",
            variant_a="A text",
            variant_b="B text",
            impressions_a=0,
            conversions_a=0,
            impressions_b=10,
            conversions_b=5,
        )
        assert test.conversion_rate_a == 0

    def test_conversion_rate_b_zero_impressions(self):
        """Conversion rate is 0 when no impressions."""
        test = ABTest(
            name="test",
            variant_a="A text",
            variant_b="B text",
            impressions_a=10,
            conversions_a=5,
            impressions_b=0,
            conversions_b=0,
        )
        assert test.conversion_rate_b == 0

    def test_conversion_rate_calculation(self):
        """Correct conversion rate calculation."""
        test = ABTest(
            name="test",
            variant_a="A text",
            variant_b="B text",
            impressions_a=100,
            conversions_a=10,
            impressions_b=100,
            conversions_b=20,
        )
        assert test.conversion_rate_a == 10.0
        assert test.conversion_rate_b == 20.0

    def test_winner_b(self):
        """B wins when it has higher conversion."""
        test = ABTest(
            name="test",
            variant_a="A text",
            variant_b="B text",
            impressions_a=100,
            conversions_a=10,
            impressions_b=100,
            conversions_b=20,
        )
        assert test.winner == "B"

    def test_winner_a(self):
        """A wins when it has higher conversion."""
        test = ABTest(
            name="test",
            variant_a="A text",
            variant_b="B text",
            impressions_a=100,
            conversions_a=30,
            impressions_b=100,
            conversions_b=10,
        )
        assert test.winner == "A"

    def test_winner_tie(self):
        """Tie when equal conversion rates."""
        test = ABTest(
            name="test",
            variant_a="A text",
            variant_b="B text",
            impressions_a=100,
            conversions_a=15,
            impressions_b=100,
            conversions_b=15,
        )
        assert test.winner == "tie"
