"""Subscription repository."""

from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database.models import Subscription, SubscriptionStatus


class SubscriptionRepository:
    """Repository for Subscription model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, sub_id: int) -> Optional[Subscription]:
        """Get subscription by ID with relations."""
        stmt = (
            select(Subscription)
            .where(Subscription.id == sub_id)
            .options(
                selectinload(Subscription.plan),
                selectinload(Subscription.server),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_subscriptions(
        self, user_id: int, active_only: bool = False
    ) -> List[Subscription]:
        """Get user's subscriptions."""
        stmt = (
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .options(selectinload(Subscription.plan))
            .order_by(Subscription.id.desc())
        )
        if active_only:
            stmt = stmt.where(Subscription.status == SubscriptionStatus.ACTIVE)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_active_subscriptions(self) -> List[Subscription]:
        """Get all active subscriptions."""
        stmt = (
            select(Subscription)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .options(
                selectinload(Subscription.server),
                selectinload(Subscription.plan),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_subscription(self, **kwargs) -> Subscription:
        """Create a new subscription."""
        sub = Subscription(**kwargs)
        self.session.add(sub)
        await self.session.flush()
        return sub

    async def update_status(
        self, sub_id: int, status: SubscriptionStatus
    ) -> bool:
        """Update subscription status."""
        sub = await self.session.get(Subscription, sub_id)
        if sub:
            sub.status = status
            sub.is_active = status == SubscriptionStatus.ACTIVE
            return True
        return False

    async def update_traffic(self, sub_id: int, used_bytes: int) -> bool:
        """Update subscription traffic usage."""
        sub = await self.session.get(Subscription, sub_id)
        if sub:
            sub.used_traffic_bytes = used_bytes
            return True
        return False
