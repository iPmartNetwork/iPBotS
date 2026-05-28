"""Plan repository."""

from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import Plan, PlanCategory


class PlanRepository:
    """Repository for Plan model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, plan_id: int) -> Optional[Plan]:
        """Get plan by ID."""
        return await self.session.get(Plan, plan_id)

    async def get_active_plans(self, category_id: Optional[int] = None) -> List[Plan]:
        """Get all active plans, optionally filtered by category."""
        stmt = select(Plan).where(Plan.is_active == True)
        if category_id:
            stmt = stmt.where(Plan.category_id == category_id)
        stmt = stmt.order_by(Plan.sort_order)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_categories(self) -> List[PlanCategory]:
        """Get all active categories."""
        stmt = (
            select(PlanCategory)
            .where(PlanCategory.is_active == True)
            .order_by(PlanCategory.sort_order)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_plan(self, **kwargs) -> Plan:
        """Create a new plan."""
        plan = Plan(**kwargs)
        self.session.add(plan)
        await self.session.flush()
        return plan

    async def update_plan(self, plan_id: int, **kwargs) -> Optional[Plan]:
        """Update a plan."""
        plan = await self.get_by_id(plan_id)
        if plan:
            for key, value in kwargs.items():
                if hasattr(plan, key):
                    setattr(plan, key, value)
        return plan

    async def toggle_plan(self, plan_id: int) -> Optional[bool]:
        """Toggle plan active status."""
        plan = await self.get_by_id(plan_id)
        if plan:
            plan.is_active = not plan.is_active
            return plan.is_active
        return None
