"""Admin dashboard and reports handler."""

from datetime import datetime, timezone, timedelta

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy import select, func

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_kb import AdminKeyboards
from core.database.engine import get_session
from core.database.models import (
    User,
    Order,
    OrderStatus,
    Subscription,
    SubscriptionStatus,
    Payment,
    PaymentStatus,
)

router = Router(name="admin_dashboard")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(Command("admin"))
@router.message(F.text == "📊 داشبورد")
async def show_dashboard(message: Message):
    """Show admin dashboard."""
    await message.answer(
        "🛡️ <b>پنل مدیریت iPBotS</b>",
        reply_markup=AdminKeyboards.main_menu(),
    )

    async with get_session() as session:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total_users = await session.scalar(select(func.count(User.id))) or 0
        today_users = await session.scalar(
            select(func.count(User.id)).where(User.created_at >= today_start)
        ) or 0
        active_subs = await session.scalar(
            select(func.count(Subscription.id)).where(
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        ) or 0
        today_revenue = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.created_at >= today_start,
            )
        ) or 0
        monthly_revenue = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.created_at >= month_start,
            )
        ) or 0
        total_revenue = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == PaymentStatus.COMPLETED
            )
        ) or 0
        pending_payments = await session.scalar(
            select(func.count(Payment.id)).where(
                Payment.status == PaymentStatus.PENDING
            )
        ) or 0
        today_orders = await session.scalar(
            select(func.count(Order.id)).where(
                Order.created_at >= today_start,
                Order.status == OrderStatus.COMPLETED,
            )
        ) or 0

    dashboard_text = (
        f"📊 <b>داشبورد مدیریت</b>\n\n"
        f"👥 <b>کاربران:</b>\n"
        f"   کل: {total_users:,}\n"
        f"   امروز: +{today_users}\n\n"
        f"📦 <b>سرویس‌ها:</b>\n"
        f"   فعال: {active_subs:,}\n\n"
        f"💰 <b>درآمد:</b>\n"
        f"   امروز: {today_revenue:,} تومان\n"
        f"   این ماه: {monthly_revenue:,} تومان\n"
        f"   کل: {total_revenue:,} تومان\n\n"
        f"🛒 <b>سفارشات امروز:</b> {today_orders}\n"
        f"⏳ <b>پرداخت‌های معلق:</b> {pending_payments}\n\n"
        f"🕐 آخرین بروزرسانی: {now.strftime('%H:%M:%S')}"
    )

    await message.answer(dashboard_text, reply_markup=AdminKeyboards.dashboard())


@router.callback_query(F.data == "admin:dashboard:refresh")
async def refresh_dashboard(callback: CallbackQuery):
    """Refresh dashboard."""
    async with get_session() as session:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total_users = await session.scalar(select(func.count(User.id))) or 0
        today_users = await session.scalar(
            select(func.count(User.id)).where(User.created_at >= today_start)
        ) or 0
        active_subs = await session.scalar(
            select(func.count(Subscription.id)).where(
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        ) or 0
        today_revenue = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.created_at >= today_start,
            )
        ) or 0
        monthly_revenue = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == PaymentStatus.COMPLETED,
                Payment.created_at >= month_start,
            )
        ) or 0
        total_revenue = await session.scalar(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == PaymentStatus.COMPLETED
            )
        ) or 0
        pending_payments = await session.scalar(
            select(func.count(Payment.id)).where(
                Payment.status == PaymentStatus.PENDING
            )
        ) or 0
        today_orders = await session.scalar(
            select(func.count(Order.id)).where(
                Order.created_at >= today_start,
                Order.status == OrderStatus.COMPLETED,
            )
        ) or 0

    dashboard_text = (
        f"📊 <b>داشبورد مدیریت</b>\n\n"
        f"👥 <b>کاربران:</b>\n"
        f"   کل: {total_users:,}\n"
        f"   امروز: +{today_users}\n\n"
        f"📦 <b>سرویس‌ها:</b>\n"
        f"   فعال: {active_subs:,}\n\n"
        f"💰 <b>درآمد:</b>\n"
        f"   امروز: {today_revenue:,} تومان\n"
        f"   این ماه: {monthly_revenue:,} تومان\n"
        f"   کل: {total_revenue:,} تومان\n\n"
        f"🛒 <b>سفارشات امروز:</b> {today_orders}\n"
        f"⏳ <b>پرداخت‌های معلق:</b> {pending_payments}\n\n"
        f"🕐 بروزرسانی: {now.strftime('%H:%M:%S')}"
    )

    await callback.message.edit_text(dashboard_text, reply_markup=AdminKeyboards.dashboard())
    await callback.answer("✅ بروزرسانی شد")


@router.callback_query(F.data == "admin:report:daily")
async def daily_report(callback: CallbackQuery):
    """Generate daily report."""
    from core.services.daily_report import report_service

    report = await report_service.generate_daily_report()
    await callback.message.answer(report)
    await callback.answer()


@router.callback_query(F.data == "admin:report:monthly")
async def monthly_report(callback: CallbackQuery):
    """Generate weekly/monthly report."""
    from core.services.daily_report import report_service

    report = await report_service.generate_weekly_report()
    await callback.message.answer(report)
    await callback.answer()


@router.callback_query(F.data == "admin:menu")
async def admin_menu(callback: CallbackQuery):
    """Show admin menu."""
    await callback.message.delete()
    await callback.message.answer(
        "🛡️ <b>پنل مدیریت</b>", reply_markup=AdminKeyboards.main_menu()
    )
    await callback.answer()


@router.message(F.text == "🔙 منوی کاربری")
async def back_to_user_menu(message: Message):
    """Switch back to user menu."""
    from bot.keyboards.user_kb import UserKeyboards

    await message.answer("🏠 منوی کاربری", reply_markup=UserKeyboards.main_menu())
