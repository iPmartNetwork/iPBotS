"""Admin API routes for React admin panel."""

from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, desc

from bot.config import settings
from core.database.engine import get_session
from core.database.models import (
    User,
    Plan,
    Server,
    Subscription,
    SubscriptionStatus,
    Order,
    OrderStatus,
    Payment,
    PaymentStatus,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def verify_admin_key(x_api_key: str = Header(None)):
    """Verify admin API key."""
    if not x_api_key or x_api_key != settings.APP_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


# --- Dashboard ---


class DashboardStats(BaseModel):
    total_users: int
    new_users_today: int
    active_subscriptions: int
    total_revenue: int
    revenue_today: int
    total_plans: int
    total_servers: int
    online_servers: int


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(x_api_key: str = Header(None)):
    """Get dashboard statistics."""
    verify_admin_key(x_api_key)

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    async with get_session() as session:
        total_users = await session.scalar(select(func.count(User.id))) or 0

        new_users_today = await session.scalar(
            select(func.count(User.id)).where(User.created_at >= today_start)
        ) or 0

        active_subs = await session.scalar(
            select(func.count(Subscription.id)).where(
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        ) or 0

        total_revenue = await session.scalar(
            select(func.sum(Payment.amount)).where(
                Payment.status == PaymentStatus.COMPLETED
            )
        ) or 0

        revenue_today = await session.scalar(
            select(func.sum(Payment.amount)).where(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.created_at >= today_start,
            )
        ) or 0

        total_plans = await session.scalar(
            select(func.count(Plan.id)).where(Plan.is_active == True)
        ) or 0

        total_servers = await session.scalar(select(func.count(Server.id))) or 0

        online_servers = await session.scalar(
            select(func.count(Server.id)).where(Server.is_active == True)
        ) or 0

    return DashboardStats(
        total_users=total_users,
        new_users_today=new_users_today,
        active_subscriptions=active_subs,
        total_revenue=total_revenue,
        revenue_today=revenue_today,
        total_plans=total_plans,
        total_servers=total_servers,
        online_servers=online_servers,
    )


# --- Users ---


class UserListItem(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    full_name: str
    total_purchases: int
    total_spent: int
    is_banned: bool
    is_active: bool
    created_at: Optional[str]


class UserListResponse(BaseModel):
    users: List[UserListItem]
    total: int
    page: int
    per_page: int


@router.get("/users", response_model=UserListResponse)
async def get_users(
    x_api_key: str = Header(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
):
    """Get paginated user list."""
    verify_admin_key(x_api_key)

    offset = (page - 1) * per_page

    async with get_session() as session:
        base_stmt = select(User)

        if search:
            base_stmt = base_stmt.where(
                (User.username.ilike(f"%{search}%"))
                | (User.full_name.ilike(f"%{search}%"))
                | (User.telegram_id == int(search) if search.isdigit() else False)
            )

        # Count
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = await session.scalar(count_stmt) or 0

        # Fetch
        stmt = base_stmt.order_by(desc(User.id)).offset(offset).limit(per_page)
        result = await session.execute(stmt)
        users = result.scalars().all()

    return UserListResponse(
        users=[
            UserListItem(
                id=u.id,
                telegram_id=u.telegram_id,
                username=u.username,
                full_name=u.full_name,
                total_purchases=u.total_purchases,
                total_spent=u.total_spent,
                is_banned=u.is_banned,
                is_active=u.is_active,
                created_at=u.created_at.strftime("%Y/%m/%d") if u.created_at else None,
            )
            for u in users
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("/users/{user_id}/ban")
async def ban_user(user_id: int, x_api_key: str = Header(None)):
    """Ban/unban a user."""
    verify_admin_key(x_api_key)

    async with get_session() as session:
        user = await session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_banned = not user.is_banned

    return {"user_id": user_id, "is_banned": user.is_banned}


# --- Plans ---


class PlanItem(BaseModel):
    id: int
    name: str
    price: int
    data_limit_gb: float
    duration_days: int
    is_active: bool
    sort_order: int


class PlanCreateRequest(BaseModel):
    name: str
    price: int
    data_limit_gb: float
    duration_days: int
    is_active: bool = True
    sort_order: int = 0
    ip_limit: int = 1
    description: str = ""


@router.get("/plans", response_model=List[PlanItem])
async def get_plans(x_api_key: str = Header(None)):
    """Get all plans."""
    verify_admin_key(x_api_key)

    async with get_session() as session:
        stmt = select(Plan).order_by(Plan.sort_order)
        result = await session.execute(stmt)
        plans = result.scalars().all()

    return [
        PlanItem(
            id=p.id,
            name=p.name,
            price=p.price,
            data_limit_gb=p.data_limit_gb,
            duration_days=p.duration_days,
            is_active=p.is_active,
            sort_order=p.sort_order,
        )
        for p in plans
    ]


@router.post("/plans", response_model=PlanItem)
async def create_plan(body: PlanCreateRequest, x_api_key: str = Header(None)):
    """Create a new plan."""
    verify_admin_key(x_api_key)

    async with get_session() as session:
        plan = Plan(
            name=body.name,
            price=body.price,
            data_limit_gb=body.data_limit_gb,
            duration_days=body.duration_days,
            is_active=body.is_active,
            sort_order=body.sort_order,
            ip_limit=body.ip_limit,
            description=body.description,
        )
        session.add(plan)
        await session.flush()

        return PlanItem(
            id=plan.id,
            name=plan.name,
            price=plan.price,
            data_limit_gb=plan.data_limit_gb,
            duration_days=plan.duration_days,
            is_active=plan.is_active,
            sort_order=plan.sort_order,
        )


@router.put("/plans/{plan_id}", response_model=PlanItem)
async def update_plan(plan_id: int, body: PlanCreateRequest, x_api_key: str = Header(None)):
    """Update a plan."""
    verify_admin_key(x_api_key)

    async with get_session() as session:
        plan = await session.get(Plan, plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        plan.name = body.name
        plan.price = body.price
        plan.data_limit_gb = body.data_limit_gb
        plan.duration_days = body.duration_days
        plan.is_active = body.is_active
        plan.sort_order = body.sort_order
        plan.ip_limit = body.ip_limit
        plan.description = body.description

        return PlanItem(
            id=plan.id,
            name=plan.name,
            price=plan.price,
            data_limit_gb=plan.data_limit_gb,
            duration_days=plan.duration_days,
            is_active=plan.is_active,
            sort_order=plan.sort_order,
        )


# --- Servers ---


class ServerItem(BaseModel):
    id: int
    name: str
    host: str
    is_active: bool
    panel_type: str
    max_users: int
    current_users: int


@router.get("/servers", response_model=List[ServerItem])
async def get_servers(x_api_key: str = Header(None)):
    """Get all servers with status."""
    verify_admin_key(x_api_key)

    async with get_session() as session:
        stmt = select(Server).order_by(Server.id)
        result = await session.execute(stmt)
        servers = result.scalars().all()

    return [
        ServerItem(
            id=s.id,
            name=s.name,
            host=s.host,
            is_active=s.is_active,
            panel_type=s.panel_type.value if hasattr(s.panel_type, "value") else str(s.panel_type),
            max_users=s.max_users if hasattr(s, "max_users") else 0,
            current_users=s.current_users if hasattr(s, "current_users") else 0,
        )
        for s in servers
    ]


# --- Payments ---


class PaymentItem(BaseModel):
    id: int
    user_id: int
    amount: int
    method: str
    status: str
    created_at: Optional[str]


class PaymentListResponse(BaseModel):
    payments: List[PaymentItem]
    total: int
    page: int


@router.get("/payments", response_model=PaymentListResponse)
async def get_payments(
    x_api_key: str = Header(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Get payment history."""
    verify_admin_key(x_api_key)

    offset = (page - 1) * per_page

    async with get_session() as session:
        total = await session.scalar(select(func.count(Payment.id))) or 0

        stmt = (
            select(Payment)
            .order_by(desc(Payment.id))
            .offset(offset)
            .limit(per_page)
        )
        result = await session.execute(stmt)
        payments = result.scalars().all()

    return PaymentListResponse(
        payments=[
            PaymentItem(
                id=p.id,
                user_id=p.user_id,
                amount=p.amount,
                method=p.method.value if hasattr(p.method, "value") else str(p.method),
                status=p.status.value if hasattr(p.status, "value") else str(p.status),
                created_at=p.created_at.strftime("%Y/%m/%d %H:%M") if p.created_at else None,
            )
            for p in payments
        ],
        total=total,
        page=page,
    )
