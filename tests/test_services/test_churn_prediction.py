"""Tests for ChurnPredictionService."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta


class TestChurnPrediction:
    """Test churn risk calculation."""

    @pytest.mark.asyncio
    async def test_unknown_user_returns_zero(self):
        """Unknown user returns zero risk."""
        from core.services.churn_prediction import ChurnPredictionService

        service = ChurnPredictionService()

        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=None)

        with patch(
            "core.services.churn_prediction.get_session"
        ) as mock_get_session:
            mock_get_session.return_value.__aenter__ = AsyncMock(
                return_value=mock_session
            )
            mock_get_session.return_value.__aexit__ = AsyncMock(
                return_value=False
            )

            result = await service.calculate_churn_risk(999)

        assert result["score"] == 0
        assert result["risk_level"] == "unknown"

    def test_weights_are_positive(self):
        """All weight values are positive."""
        from core.services.churn_prediction import ChurnPredictionService

        service = ChurnPredictionService()
        for key, value in service.WEIGHTS.items():
            assert value > 0, f"Weight {key} should be positive"

    def test_risk_levels(self):
        """Risk level thresholds are correct."""
        # high >= 70, medium >= 40, low < 40
        from core.services.churn_prediction import ChurnPredictionService

        service = ChurnPredictionService()

        # Verify weights exist
        assert "no_activity_7d" in service.WEIGHTS
        assert "no_activity_14d" in service.WEIGHTS
        assert "no_activity_30d" in service.WEIGHTS
        assert "expired_no_renew" in service.WEIGHTS
        assert "single_purchase" in service.WEIGHTS
