"""Traffic statistics and usage charts handlers."""

import io
from datetime import datetime, timezone, timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from sqlalchemy import select

from core.database.engine import get_session
from core.database.models import User, Subscription, SubscriptionStatus

router = Router(name="traffic_stats")


@router.callback_query(F.data.startswith("sub:stats:"))
async def show_traffic_stats(callback: CallbackQuery, db_user: User):
    """Show detailed traffic statistics with visual chart."""
    sub_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        from sqlalchemy.orm import selectinload

        stmt = (
            select(Subscription)
            .where(Subscription.id == sub_id)
            .where(Subscription.user_id == db_user.id)
            .options(selectinload(Subscription.plan), selectinload(Subscription.server))
        )
        result = await session.execute(stmt)
        sub = result.scalar_one_or_none()

    if not sub:
        await callback.answer("⚠️ سرویس یافت نشد.", show_alert=True)
        return

    # Generate text-based chart
    chart = _generate_usage_chart(sub)

    text = (
        f"📊 <b>آمار مصرف سرویس</b>\n\n"
        f"📋 پلن: {sub.plan.name}\n"
        f"🖥️ سرور: {sub.server.flag} {sub.server.name}\n\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"📥 <b>ترافیک:</b>\n"
        f"{chart}\n\n"
        f"📈 مصرف شده: {sub.used_traffic_gb} GB\n"
        f"📊 کل: {sub.data_limit_gb if sub.data_limit_gb > 0 else '♾️'} GB\n"
        f"📉 باقیمانده: {sub.remaining_traffic_gb if sub.data_limit_bytes > 0 else '♾️'} GB\n\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"📅 <b>زمان:</b>\n"
        f"🟢 شروع: {sub.start_date.strftime('%Y/%m/%d')}\n"
        f"🔴 انقضا: {sub.expire_date.strftime('%Y/%m/%d')}\n"
        f"⏱️ باقیمانده: {sub.remaining_days} روز\n"
        f"{_generate_time_chart(sub)}\n\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"⚡ <b>سرعت مصرف:</b>\n"
        f"{_calculate_daily_usage(sub)}"
    )

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🔄 بروزرسانی", callback_data=f"sub:stats:{sub_id}"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="🔙 بازگشت", callback_data=f"sub:detail:{sub_id}"
        ),
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


def _generate_usage_chart(sub: Subscription) -> str:
    """Generate text-based traffic usage chart."""
    if sub.data_limit_bytes == 0:
        return "♾️ ترافیک نامحدود"

    percent = sub.traffic_percent
    bar_length = 20
    filled = int(bar_length * percent / 100)
    empty = bar_length - filled

    # Color-coded bar
    if percent < 50:
        bar_char = "🟩"
    elif percent < 75:
        bar_char = "🟨"
    elif percent < 90:
        bar_char = "🟧"
    else:
        bar_char = "🟥"

    bar = bar_char * filled + "⬜" * empty
    return f"{bar} {percent}%"


def _generate_time_chart(sub: Subscription) -> str:
    """Generate time remaining chart."""
    now = datetime.now(timezone.utc)
    total_duration = (sub.expire_date - sub.start_date).total_seconds()
    elapsed = (now - sub.start_date).total_seconds()

    if total_duration <= 0:
        return ""

    percent = min(100, int((elapsed / total_duration) * 100))
    bar_length = 20
    filled = int(bar_length * percent / 100)
    empty = bar_length - filled

    bar = "🔵" * filled + "⚪" * empty
    return f"{bar} {percent}%"


def _calculate_daily_usage(sub: Subscription) -> str:
    """Calculate average daily usage."""
    now = datetime.now(timezone.utc)
    days_active = max(1, (now - sub.start_date).days)
    daily_gb = sub.used_traffic_gb / days_active

    text = f"📊 میانگین روزانه: {daily_gb:.2f} GB\n"

    if sub.data_limit_bytes > 0 and sub.remaining_days > 0:
        remaining_gb = sub.remaining_traffic_gb
        suggested_daily = remaining_gb / sub.remaining_days
        text += f"💡 پیشنهادی روزانه: {suggested_daily:.2f} GB\n"

        # Estimate when traffic will end
        if daily_gb > 0:
            days_until_end = remaining_gb / daily_gb
            if days_until_end < sub.remaining_days:
                text += f"⚠️ با این سرعت، ترافیک تا {int(days_until_end)} روز دیگر تمام می‌شود!"
            else:
                text += f"✅ ترافیک تا پایان مدت کافی است."

    return text
