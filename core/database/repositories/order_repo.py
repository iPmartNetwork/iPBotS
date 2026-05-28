"""Order repository."""

from typing import Optional, List
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Order, OrderStatus


class OrderRepository:
    """Repository for Order model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID."""
        return await self.session.get(Order, order_id)

    async def get_user_orders(self, user_id: int, limit: int = 20) -> List[Order]:
        """Get user's orders."""
        stmt = (
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(Order.id.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_today_revenue(self) -> int:
        """Get today's total revenue."""
        today = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        result = await self.session.scalar(
            select(func.coalesce(func.sum(Order.amount), 0)).where(
                Order.status == OrderStatus.COMPLETED,
                Order.created_at >= today,
            )
        )
        return result or 0

    async def create_order(self, **kwargs) -> Order:
        """Create a new order."""
        order = Order(**kwargs)
        self.session.add(order)
        await self.session.flush()
        return order

    async def update_status(self, order_id: int, status: OrderStatus) -> bool:
        """Update order status."""
        order = await self.get_by_id(order_id)
        if order:
            order.status = status
            return True
        return False
