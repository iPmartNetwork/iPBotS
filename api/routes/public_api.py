"""Public Bot API for external integrations."""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select, func

from bot.config import settings
from core.database.engine import get_session
from core.database.models import User, Plan, Subscription, SubscriptionStatus

router = APIRouter(prefix="/api/v1", tags=["public"])


def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key from header."""
    if not x_api_key or x_api_key != settings.APP_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


class StatsResponse(BaseModel):
    total_users: int
    active_subscriptions: int
    total_plans: int


class UserResponse(BaseModel):
    telegram_id: int
    username: Optional[str]
    full_name: str
    total_purchases: int
    total_spent: int
    is_banned: bool


@router.get("/stats", response_model=StatsResponse)
async def get_stats(x_api_key: str = Header(None)):
    """Get bot statistics."""
    verify_api_key(x_api_key)

    async with get_session() as session:
        total_users = await session.scalar(select(func.count(User.id))) or 0
        active_subs = await session.scalar(
            select(func.count(Subscription.id)).where(
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        ) or 0
        total_plans = await session.scalar(select(func.count(Plan.id))) or 0

    return StatsResponse(
        total_users=total_users,
        active_subscriptions=active_subs,
        total_plans=total_plans,
    )


@router.get("/user/{telegram_id}", response_model=UserResponse)
async def get_user(telegram_id: int, x_api_key: str = Header(None)):
    """Get user info by telegram ID."""
    verify_api_key(x_api_key)

    async with get_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        telegram_id=user.telegram_id,
        username=user.username,
        full_name=user.full_name,
        total_purchases=user.total_purchases,
        total_spent=user.total_spent,
        is_banned=user.is_banned,
    )


@router.get("/plans")
async def get_plans(x_api_key: str = Header(None)):
    """Get all active plans."""
    verify_api_key(x_api_key)

    async with get_session() as session:
        stmt = select(Plan).where(Plan.is_active == True).order_by(Plan.sort_order)
        result = await session.execute(stmt)
        plans = result.scalars().all()

    return [
        {
            "id": p.id,
            "name": p.name,
            "data_gb": p.data_limit_gb,
            "duration_days": p.duration_days,
            "price": p.price,
            "final_price": p.final_price,
        }
        for p in plans
    ]
