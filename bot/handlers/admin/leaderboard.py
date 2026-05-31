"""Reseller leaderboard handler."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, func

from bot.filters.admin import AdminFilter
from core.database.engine import get_session
from core.database.models.reseller import Reseller

router = Router(name="admin_leaderboard")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(F.text == "/leaderboard")
@router.callback_query(F.data == "admin:leaderboard")
async def show_leaderboard(event, **kwargs):
    """Show reseller leaderboard."""
    async with get_session() as session:
        stmt = (
            select(Reseller)
            .where(Reseller.is_active == True)
            .order_by(Reseller.total_revenue.desc())
            .limit(20)
        )
        result = await session.execute(stmt)
        resellers = result.scalars().all()

    if not resellers:
        text = "🏆 <b>لیدربورد نمایندگان</b>\n\nهنوز نماینده‌ای ثبت نشده."
    else:
        text = "🏆 <b>لیدربورد نمایندگان</b>\n\n"

        medals = ["🥇", "🥈", "🥉"]
        for i, reseller in enumerate(resellers):
            medal = medals[i] if i < 3 else f"{i+1}."
            text += (
                f"{medal} <b>{reseller.shop_name}</b>\n"
                f"   💰 {reseller.total_revenue:,}ت | "
                f"🛒 {reseller.total_sales} فروش | "
                f"👥 {reseller.total_clients} مشتری\n\n"
            )

    if isinstance(event, Message):
        await event.answer(text)
    else:
        await event.message.edit_text(text)
        await event.answer()
