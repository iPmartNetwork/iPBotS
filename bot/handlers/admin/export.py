"""Admin data export handlers."""

import csv
import io
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from sqlalchemy import select

from bot.filters.admin import AdminFilter
from core.database.engine import get_session
from core.database.models import User, Subscription, SubscriptionStatus, Payment, PaymentStatus

router = Router(name="admin_export")
router.message.filter(AdminFilter())


@router.message(F.text == "/export_users")
async def export_users_csv(message: Message):
    """Export all users to CSV."""
    async with get_session() as session:
        stmt = select(User).order_by(User.id)
        result = await session.execute(stmt)
        users = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Telegram_ID", "Username", "Name", "Joined", "Purchases", "Spent", "Banned", "Referral_Code"])

    for user in users:
        writer.writerow([
            user.id,
            user.telegram_id,
            user.username or "",
            user.full_name,
            user.created_at.strftime("%Y-%m-%d"),
            user.total_purchases,
            user.total_spent,
            user.is_banned,
            user.referral_code,
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    doc = BufferedInputFile(csv_bytes, filename=f"users_{datetime.now().strftime('%Y%m%d')}.csv")
    await message.answer_document(doc, caption=f"📊 خروجی کاربران ({len(users)} نفر)")


@router.message(F.text == "/export_payments")
async def export_payments_csv(message: Message):
    """Export payments to CSV."""
    async with get_session() as session:
        stmt = select(Payment).order_by(Payment.id.desc()).limit(500)
        result = await session.execute(stmt)
        payments = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "User_ID", "Amount", "Method", "Status", "Date"])

    for pay in payments:
        writer.writerow([
            pay.id,
            pay.user_id,
            pay.amount,
            pay.method.value,
            pay.status.value,
            pay.created_at.strftime("%Y-%m-%d %H:%M"),
        ])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    doc = BufferedInputFile(csv_bytes, filename=f"payments_{datetime.now().strftime('%Y%m%d')}.csv")
    await message.answer_document(doc, caption=f"📊 خروجی پرداخت‌ها ({len(payments)} رکورد)")
