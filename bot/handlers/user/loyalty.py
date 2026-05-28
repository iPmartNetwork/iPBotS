"""Loyalty points system handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from core.database.engine import get_session
from core.database.models import User
from core.database.models.loyalty import (
    UserLoyalty,
    LoyaltyReward,
    LoyaltyTransaction,
    LoyaltyConfig,
)

router = Router(name="loyalty")


@router.callback_query(F.data == "loyalty:menu")
async def show_loyalty(callback: CallbackQuery, db_user: User):
    """Show loyalty points menu."""
    async with get_session() as session:
        # Get user loyalty
        stmt = select(UserLoyalty).where(UserLoyalty.user_id == db_user.id)
        result = await session.execute(stmt)
        loyalty = result.scalar_one_or_none()

        # Get config
        config_stmt = select(LoyaltyConfig).where(LoyaltyConfig.is_active == True)
        config_result = await session.execute(config_stmt)
        config = config_result.scalar_one_or_none()

    points = loyalty.available_points if loyalty else 0
    total = loyalty.total_points if loyalty else 0
    level = loyalty.level if loyalty else "bronze"

    level_icons = {
        "bronze": "🥉",
        "silver": "🥈",
        "gold": "🥇",
        "diamond": "💎",
    }
    level_names = {
        "bronze": "برنزی",
        "silver": "نقره‌ای",
        "gold": "طلایی",
        "diamond": "الماسی",
    }

    text = (
        f"⭐ <b>باشگاه مشتریان</b>\n\n"
        f"{level_icons.get(level, '⭐')} سطح: <b>{level_names.get(level, level)}</b>\n"
        f"💎 امتیاز موجود: <b>{points:,}</b>\n"
        f"📊 مجموع امتیاز: {total:,}\n\n"
        f"💡 با هر خرید امتیاز کسب کنید و جوایز بگیرید!"
    )

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎁 جوایز", callback_data="loyalty:rewards"),
    )
    builder.row(
        InlineKeyboardButton(text="📜 تاریخچه امتیاز", callback_data="loyalty:history"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 نحوه کسب امتیاز", callback_data="loyalty:info"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="main:menu"),
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "loyalty:rewards")
async def show_rewards(callback: CallbackQuery, db_user: User):
    """Show available rewards."""
    async with get_session() as session:
        stmt = (
            select(LoyaltyReward)
            .where(LoyaltyReward.is_active == True)
            .order_by(LoyaltyReward.points_required)
        )
        result = await session.execute(stmt)
        rewards = result.scalars().all()

        # Get user points
        loyalty_stmt = select(UserLoyalty).where(UserLoyalty.user_id == db_user.id)
        loyalty_result = await session.execute(loyalty_stmt)
        loyalty = loyalty_result.scalar_one_or_none()

    user_points = loyalty.available_points if loyalty else 0

    if not rewards:
        await callback.answer("جایزه‌ای تعریف نشده.", show_alert=True)
        return

    text = f"🎁 <b>جوایز موجود</b>\n💎 امتیاز شما: {user_points:,}\n\n"

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()

    for reward in rewards:
        can_redeem = "✅" if user_points >= reward.points_required else "🔒"
        text += (
            f"{reward.icon} <b>{reward.name}</b>\n"
            f"   💎 {reward.points_required:,} امتیاز | {can_redeem}\n\n"
        )
        if user_points >= reward.points_required:
            builder.row(
                InlineKeyboardButton(
                    text=f"{reward.icon} دریافت {reward.name}",
                    callback_data=f"loyalty:redeem:{reward.id}",
                )
            )

    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="loyalty:menu"),
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("loyalty:redeem:"))
async def redeem_reward(callback: CallbackQuery, db_user: User):
    """Redeem a loyalty reward."""
    reward_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        reward = await session.get(LoyaltyReward, reward_id)
        if not reward or not reward.is_active:
            await callback.answer("⚠️ جایزه موجود نیست.", show_alert=True)
            return

        loyalty_stmt = select(UserLoyalty).where(UserLoyalty.user_id == db_user.id)
        loyalty_result = await session.execute(loyalty_stmt)
        loyalty = loyalty_result.scalar_one_or_none()

        if not loyalty or loyalty.available_points < reward.points_required:
            await callback.answer("⚠️ امتیاز کافی ندارید.", show_alert=True)
            return

        # Deduct points
        loyalty.available_points -= reward.points_required
        loyalty.spent_points += reward.points_required

        # Record transaction
        tx = LoyaltyTransaction(
            user_id=db_user.id,
            points=-reward.points_required,
            transaction_type="redeem",
            description=f"دریافت جایزه: {reward.name}",
            reference_id=f"reward_{reward.id}",
        )
        session.add(tx)

        # Update stock
        if reward.stock > 0:
            reward.stock -= 1

    # Apply reward based on type
    reward_text = ""
    if reward.reward_type == "discount_percent":
        reward_text = f"🏷️ کد تخفیف {reward.reward_value}% برای خرید بعدی شما فعال شد."
    elif reward.reward_type == "free_days":
        reward_text = f"📅 {reward.reward_value} روز رایگان به سرویس فعال شما اضافه شد."
    elif reward.reward_type == "extra_traffic":
        reward_text = f"📊 {reward.reward_value} GB ترافیک اضافه به سرویس شما اضافه شد."

    await callback.message.edit_text(
        f"✅ <b>جایزه دریافت شد!</b>\n\n"
        f"🎁 {reward.name}\n"
        f"💎 امتیاز مصرف شده: {reward.points_required:,}\n\n"
        f"{reward_text}"
    )
    await callback.answer("✅ جایزه دریافت شد!")


@router.callback_query(F.data == "loyalty:history")
async def loyalty_history(callback: CallbackQuery, db_user: User):
    """Show loyalty points history."""
    async with get_session() as session:
        stmt = (
            select(LoyaltyTransaction)
            .where(LoyaltyTransaction.user_id == db_user.id)
            .order_by(LoyaltyTransaction.id.desc())
            .limit(15)
        )
        result = await session.execute(stmt)
        transactions = result.scalars().all()

    if not transactions:
        await callback.answer("تاریخچه‌ای وجود ندارد.", show_alert=True)
        return

    text = "📜 <b>تاریخچه امتیاز</b>\n\n"
    for tx in transactions:
        icon = "➕" if tx.points > 0 else "➖"
        text += f"{icon} {abs(tx.points):,} | {tx.description or tx.transaction_type}\n"

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="loyalty:menu"),
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "loyalty:info")
async def loyalty_info(callback: CallbackQuery):
    """Show how to earn points."""
    text = (
        "📊 <b>نحوه کسب امتیاز</b>\n\n"
        "🛒 <b>خرید سرویس:</b> هر 10,000 تومان = 1 امتیاز\n"
        "👥 <b>دعوت دوستان:</b> هر زیرمجموعه = 50 امتیاز\n"
        "⭐ <b>تمدید سرویس:</b> 2 برابر امتیاز عادی\n\n"
        "━━━━━━━━━━━━━━━\n\n"
        "🏆 <b>سطوح باشگاه:</b>\n"
        "🥉 برنزی: 0 - 499 امتیاز\n"
        "🥈 نقره‌ای: 500 - 1999 امتیاز\n"
        "🥇 طلایی: 2000 - 4999 امتیاز\n"
        "💎 الماسی: 5000+ امتیاز\n\n"
        "💡 سطح بالاتر = تخفیف‌های بیشتر!"
    )

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="loyalty:menu"),
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
