"""Daily/weekly automated report service."""

from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import select, func
from loguru import logger

from core.database.engine import get_session
from core.database.models import (
    User,
    Order,
    OrderStatus,
    Payment,
    PaymentStatus,
    Subscription,
    SubscriptionStatus,
)


class ReportService:
    """Service for generating automated reports."""

    async def generate_daily_report(self) -> str:
        """Generate daily report text."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)

        async with get_session() as session:
            # Today's stats
            today_revenue = await session.scalar(
                select(func.coalesce(func.sum(Payment.amount), 0)).where(
                    Payment.status == PaymentStatus.COMPLETED,
                    Payment.created_at >= today_start,
                )
            ) or 0

            today_orders = await session.scalar(
                select(func.count(Order.id)).where(
                    Order.created_at >= today_start,
                    Order.status.in_([OrderStatus.COMPLETED, OrderStatus.PAID]),
                )
            ) or 0

            today_new_users = await session.scalar(
                select(func.count(User.id)).where(User.created_at >= today_start)
            ) or 0

            # Yesterday's stats for comparison
            yesterday_revenue = await session.scalar(
                select(func.coalesce(func.sum(Payment.amount), 0)).where(
                    Payment.status == PaymentStatus.COMPLETED,
                    Payment.created_at >= yesterday_start,
                    Payment.created_at < today_start,
                )
            ) or 0

            yesterday_orders = await session.scalar(
                select(func.count(Order.id)).where(
                    Order.created_at >= yesterday_start,
                    Order.created_at < today_start,
                    Order.status.in_([OrderStatus.COMPLETED, OrderStatus.PAID]),
                )
            ) or 0

            yesterday_new_users = await session.scalar(
                select(func.count(User.id)).where(
                    User.created_at >= yesterday_start,
                    User.created_at < today_start,
                )
            ) or 0

            # Total stats
            total_users = await session.scalar(select(func.count(User.id))) or 0
            active_subs = await session.scalar(
                select(func.count(Subscription.id)).where(
                    Subscription.status == SubscriptionStatus.ACTIVE
                )
            ) or 0

            # Expiring soon (next 3 days)
            expiring_soon = await session.scalar(
                select(func.count(Subscription.id)).where(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.expire_date <= now + timedelta(days=3),
                    Subscription.expire_date > now,
                )
            ) or 0

            # Expired today
            expired_today = await session.scalar(
                select(func.count(Subscription.id)).where(
                    Subscription.status == SubscriptionStatus.EXPIRED,
                    Subscription.updated_at >= today_start,
                )
            ) or 0

            # Pending payments
            pending_payments = await session.scalar(
                select(func.count(Payment.id)).where(
                    Payment.status == PaymentStatus.PENDING
                )
            ) or 0

        # Calculate changes
        revenue_change = _calc_change(today_revenue, yesterday_revenue)
        orders_change = _calc_change(today_orders, yesterday_orders)
        users_change = _calc_change(today_new_users, yesterday_new_users)

        report = (
            f"📊 <b>گزارش روزانه</b>\n"
            f"📅 {now.strftime('%Y/%m/%d')} | {now.strftime('%H:%M')}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 <b>درآمد امروز:</b>\n"
            f"   {today_revenue:,} تومان {revenue_change}\n\n"
            f"🛒 <b>سفارشات امروز:</b>\n"
            f"   {today_orders} سفارش {orders_change}\n\n"
            f"👥 <b>کاربران جدید:</b>\n"
            f"   {today_new_users} نفر {users_change}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📈 <b>آمار کلی:</b>\n"
            f"   👥 کل کاربران: {total_users:,}\n"
            f"   ✅ سرویس فعال: {active_subs:,}\n"
            f"   ⚠️ در حال انقضا (3 روز): {expiring_soon}\n"
            f"   ❌ منقضی شده امروز: {expired_today}\n"
            f"   ⏳ پرداخت معلق: {pending_payments}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 گزارش خودکار V2Ray Shop Bot"
        )

        return report

    async def generate_weekly_report(self) -> str:
        """Generate weekly report."""
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=7)

        async with get_session() as session:
            # Weekly revenue
            weekly_revenue = await session.scalar(
                select(func.coalesce(func.sum(Payment.amount), 0)).where(
                    Payment.status == PaymentStatus.COMPLETED,
                    Payment.created_at >= week_start,
                )
            ) or 0

            # Weekly orders
            weekly_orders = await session.scalar(
                select(func.count(Order.id)).where(
                    Order.created_at >= week_start,
                    Order.status.in_([OrderStatus.COMPLETED, OrderStatus.PAID]),
                )
            ) or 0

            # Weekly new users
            weekly_users = await session.scalar(
                select(func.count(User.id)).where(User.created_at >= week_start)
            ) or 0

            # Average order value
            avg_order = 0
            if weekly_orders > 0:
                avg_order = weekly_revenue // weekly_orders

            # Top plan
            from core.database.models import Plan
            from sqlalchemy.orm import selectinload

            top_plan_stmt = (
                select(Order.plan_id, func.count(Order.id).label("cnt"))
                .where(
                    Order.created_at >= week_start,
                    Order.status == OrderStatus.COMPLETED,
                    Order.plan_id.isnot(None),
                )
                .group_by(Order.plan_id)
                .order_by(func.count(Order.id).desc())
                .limit(1)
            )
            top_result = await session.execute(top_plan_stmt)
            top_row = top_result.first()
            top_plan_name = "نامشخص"
            if top_row:
                plan = await session.get(Plan, top_row[0])
                if plan:
                    top_plan_name = plan.name

        report = (
            f"📊 <b>گزارش هفتگی</b>\n"
            f"📅 {week_start.strftime('%m/%d')} تا {now.strftime('%m/%d')}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💰 درآمد هفته: <b>{weekly_revenue:,}</b> تومان\n"
            f"🛒 سفارشات: {weekly_orders}\n"
            f"👥 کاربران جدید: {weekly_users}\n"
            f"💵 میانگین سفارش: {avg_order:,} تومان\n"
            f"⭐ محبوب‌ترین پلن: {top_plan_name}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 گزارش خودکار V2Ray Shop Bot"
        )

        return report

    async def send_daily_report(self):
        """Generate and send daily report to admins."""
        from bot.loader import bot
        from bot.config import settings

        report = await self.generate_daily_report()

        for admin_id in settings.ADMIN_IDS:
            try:
                await bot.send_message(admin_id, report)
            except Exception as e:
                logger.error(f"Failed to send daily report to {admin_id}: {e}")

    async def send_weekly_report(self):
        """Generate and send weekly report to admins."""
        from bot.loader import bot
        from bot.config import settings

        report = await self.generate_weekly_report()

        for admin_id in settings.ADMIN_IDS:
            try:
                await bot.send_message(admin_id, report)
            except Exception as e:
                logger.error(f"Failed to send weekly report to {admin_id}: {e}")


def _calc_change(current: int, previous: int) -> str:
    """Calculate percentage change indicator."""
    if previous == 0:
        if current > 0:
            return "📈 +∞%"
        return ""

    change = ((current - previous) / previous) * 100

    if change > 0:
        return f"📈 +{change:.0f}%"
    elif change < 0:
        return f"📉 {change:.0f}%"
    else:
        return "➡️ 0%"


# Singleton
report_service = ReportService()
