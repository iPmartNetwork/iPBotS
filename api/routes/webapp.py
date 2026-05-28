"""WebApp API routes for Telegram Mini App."""

import hashlib
import hmac
import json
from urllib.parse import parse_qs, unquote

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy import select, func

from bot.config import settings
from core.database.engine import get_session
from core.database.models import (
    User,
    Plan,
    PlanCategory,
    Subscription,
    SubscriptionStatus,
    Wallet,
    WalletTransaction,
)

router = APIRouter(prefix="/api/webapp", tags=["webapp"])


async def verify_telegram_data(request: Request) -> dict:
    """Verify Telegram WebApp init data and extract user info."""
    init_data = request.headers.get("X-Telegram-Init-Data", "")

    if not init_data:
        raise HTTPException(status_code=401, detail="Missing init data")

    # Parse init data
    parsed = parse_qs(init_data)

    # Verify hash
    data_check_string = "\n".join(
        sorted(
            f"{k}={unquote(v[0])}"
            for k, v in parsed.items()
            if k != "hash"
        )
    )

    secret_key = hmac.new(
        b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    received_hash = parsed.get("hash", [""])[0]

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=401, detail="Invalid hash")

    # Extract user
    user_data = json.loads(unquote(parsed.get("user", ["{}"])[0]))
    return user_data


@router.get("/user")
async def get_user_info(user_data: dict = Depends(verify_telegram_data)):
    """Get user information."""
    telegram_id = user_data.get("id")

    async with get_session() as session:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return {"error": "User not found"}

        # Get wallet
        wallet_stmt = select(Wallet).where(Wallet.user_id == user.id)
        wallet_result = await session.execute(wallet_stmt)
        wallet = wallet_result.scalar_one_or_none()

        # Count referrals
        ref_count = await session.scalar(
            select(func.count(User.id)).where(User.referred_by_id == user.id)
        )

    return {
        "id": user.telegram_id,
        "name": user.full_name,
        "username": user.username,
        "balance": wallet.balance if wallet else 0,
        "total_purchases": user.total_purchases,
        "total_spent": user.total_spent,
        "referral_code": user.referral_code,
        "referral_count": ref_count or 0,
        "language": user.language,
    }


@router.get("/categories")
async def get_categories(user_data: dict = Depends(verify_telegram_data)):
    """Get plan categories."""
    async with get_session() as session:
        stmt = (
            select(PlanCategory)
            .where(PlanCategory.is_active == True)
            .order_by(PlanCategory.sort_order)
        )
        result = await session.execute(stmt)
        categories = result.scalars().all()

    return [
        {"id": cat.id, "name": cat.name, "icon": cat.icon}
        for cat in categories
    ]


@router.get("/plans")
async def get_plans(category: int = None, user_data: dict = Depends(verify_telegram_data)):
    """Get plans, optionally filtered by category."""
    async with get_session() as session:
        stmt = select(Plan).where(Plan.is_active == True)
        if category:
            stmt = stmt.where(Plan.category_id == category)
        stmt = stmt.order_by(Plan.sort_order)
        result = await session.execute(stmt)
        plans = result.scalars().all()

    return [
        {
            "id": plan.id,
            "name": plan.name,
            "data": plan.display_data,
            "duration": plan.display_duration,
            "price": plan.price,
            "discount": plan.discount_percent,
            "ip_limit": plan.ip_limit,
            "description": plan.description,
        }
        for plan in plans
    ]


@router.get("/services")
async def get_services(user_data: dict = Depends(verify_telegram_data)):
    """Get user's subscriptions."""
    telegram_id = user_data.get("id")

    async with get_session() as session:
        user_stmt = select(User).where(User.telegram_id == telegram_id)
        user_result = await session.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user:
            return []

        from sqlalchemy.orm import selectinload

        stmt = (
            select(Subscription)
            .where(Subscription.user_id == user.id)
            .options(selectinload(Subscription.plan))
            .order_by(Subscription.id.desc())
        )
        result = await session.execute(stmt)
        subs = result.scalars().all()

    return [
        {
            "id": sub.id,
            "plan_name": sub.plan.name if sub.plan else "نامشخص",
            "is_active": sub.is_active,
            "used_gb": sub.used_traffic_gb,
            "total_gb": sub.data_limit_gb if sub.data_limit_gb > 0 else "♾️",
            "traffic_percent": sub.traffic_percent,
            "remaining_days": sub.remaining_days,
            "expire_date": sub.expire_date.strftime("%Y/%m/%d"),
            "sub_url": sub.subscription_url,
        }
        for sub in subs
    ]


@router.get("/wallet")
async def get_wallet(user_data: dict = Depends(verify_telegram_data)):
    """Get wallet info."""
    telegram_id = user_data.get("id")

    async with get_session() as session:
        user_stmt = select(User).where(User.telegram_id == telegram_id)
        user_result = await session.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user:
            return {"balance": 0, "transactions": []}

        wallet_stmt = select(Wallet).where(Wallet.user_id == user.id)
        wallet_result = await session.execute(wallet_stmt)
        wallet = wallet_result.scalar_one_or_none()

        if not wallet:
            return {"balance": 0, "transactions": []}

        tx_stmt = (
            select(WalletTransaction)
            .where(WalletTransaction.wallet_id == wallet.id)
            .order_by(WalletTransaction.id.desc())
            .limit(20)
        )
        tx_result = await session.execute(tx_stmt)
        transactions = tx_result.scalars().all()

    return {
        "balance": wallet.balance,
        "total_deposited": wallet.total_deposited,
        "total_spent": wallet.total_spent,
        "transactions": [
            {
                "type": tx.transaction_type.value,
                "amount": tx.amount,
                "description": tx.description,
                "date": tx.created_at.strftime("%Y/%m/%d %H:%M"),
            }
            for tx in transactions
        ],
    }
