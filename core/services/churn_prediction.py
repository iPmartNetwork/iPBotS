"""Churn prediction service - identify users likely to leave."""
from datetime import datetime, timezone, timedelta
from typing import List, Dict
from sqlalchemy import select, func
from loguru import logger

from core.database.engine import get_session
from core.database.models import User, Subscription, SubscriptionStatus, Order


class ChurnPredictionService:
    """Predict which users are likely to churn (not renew)."""

    # Risk factors and weights
    WEIGHTS = {
        "no_activity_7d": 20,
        "no_activity_14d": 35,
        "no_activity_30d": 50,
        "expired_no_renew": 40,
        "low_usage": 15,
        "no_referrals": 5,
        "single_purchase": 10,
    }

    async def calculate_churn_risk(self, user_id: int) -> Dict:
        """Calculate churn risk score for a user (0-100).
        
        Returns: {"score": int, "risk_level": str, "factors": list}
        """
        score = 0
        factors = []

        async with get_session() as session:
            user = await session.get(User, user_id)
            if not user:
                return {"score": 0, "risk_level": "unknown", "factors": []}

            now = datetime.now(timezone.utc)

            # Activity check
            if user.last_activity:
                days_inactive = (now - user.last_activity).days
                if days_inactive >= 30:
                    score += self.WEIGHTS["no_activity_30d"]
                    factors.append(f"غیرفعال {days_inactive} روز")
                elif days_inactive >= 14:
                    score += self.WEIGHTS["no_activity_14d"]
                    factors.append(f"غیرفعال {days_inactive} روز")
                elif days_inactive >= 7:
                    score += self.WEIGHTS["no_activity_7d"]
                    factors.append(f"غیرفعال {days_inactive} روز")

            # Expired without renewal
            expired_stmt = (
                select(func.count(Subscription.id))
                .where(Subscription.user_id == user_id)
                .where(Subscription.status == SubscriptionStatus.EXPIRED)
            )
            expired_count = await session.scalar(expired_stmt) or 0
            if expired_count > 0:
                active_stmt = (
                    select(func.count(Subscription.id))
                    .where(Subscription.user_id == user_id)
                    .where(Subscription.status == SubscriptionStatus.ACTIVE)
                )
                active_count = await session.scalar(active_stmt) or 0
                if active_count == 0:
                    score += self.WEIGHTS["expired_no_renew"]
                    factors.append("سرویس منقضی بدون تمدید")

            # Single purchase only
            if user.total_purchases == 1:
                score += self.WEIGHTS["single_purchase"]
                factors.append("فقط یک خرید")

        # Cap at 100
        score = min(score, 100)

        # Risk level
        if score >= 70:
            risk_level = "high"
        elif score >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "score": score,
            "risk_level": risk_level,
            "factors": factors,
        }

    async def get_at_risk_users(self, min_score: int = 50) -> List[Dict]:
        """Get all users with high churn risk."""
        async with get_session() as session:
            stmt = select(User).where(User.is_active == True, User.is_banned == False)
            result = await session.execute(stmt)
            users = result.scalars().all()

        at_risk = []
        for user in users:
            risk = await self.calculate_churn_risk(user.id)
            if risk["score"] >= min_score:
                at_risk.append({
                    "user_id": user.id,
                    "telegram_id": user.telegram_id,
                    "name": user.full_name,
                    **risk,
                })

        return sorted(at_risk, key=lambda x: x["score"], reverse=True)


churn_service = ChurnPredictionService()
