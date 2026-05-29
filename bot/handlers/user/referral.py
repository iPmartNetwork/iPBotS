"""Referral system handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func

from bot.keyboards.user_kb import UserKeyboards
from bot.config import settings
from core.database.engine import get_session
from core.database.models import User

router = Router(name="referral")


@router.message(F.text == "👥 زیرمجموعه")
async def show_referral(message: Message, db_user: User, state: FSMContext):
    """Show referral info."""
    await state.clear()
    async with get_session() as session:
        # Count referrals
        stmt = select(func.count(User.id)).where(User.referred_by_id == db_user.id)
        result = await session.execute(stmt)
        referral_count = result.scalar() or 0

    bot_username = settings.BOT_USERNAME or (await message.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={db_user.referral_code}"

    text = (
        f"👥 <b>سیستم زیرمجموعه‌گیری</b>\n\n"
        f"🔗 لینک دعوت شما:\n<code>{referral_link}</code>\n\n"
        f"👥 تعداد زیرمجموعه‌ها: {referral_count}\n"
        f"💰 درآمد کل: {db_user.referral_earnings:,} تومان\n"
        f"📊 درصد پورسانت: {settings.REFERRAL_BONUS_PERCENT}%\n\n"
        f"💡 با اشتراک لینک دعوت، از هر خرید زیرمجموعه‌ها "
        f"{settings.REFERRAL_BONUS_PERCENT}% پورسانت دریافت کنید."
    )

    await message.answer(
        text, reply_markup=UserKeyboards.referral_menu(db_user.referral_code)
    )


@router.callback_query(F.data.startswith("ref:copy:"))
async def copy_referral_link(callback: CallbackQuery, db_user: User):
    """Copy referral link."""
    bot_username = settings.BOT_USERNAME or (await callback.bot.get_me()).username
    referral_link = f"https://t.me/{bot_username}?start={db_user.referral_code}"

    await callback.message.answer(
        f"🔗 لینک دعوت شما:\n\n<code>{referral_link}</code>\n\n"
        f"👆 روی لینک بالا بزنید تا کپی شود."
    )
    await callback.answer()


@router.callback_query(F.data == "ref:list")
async def referral_list(callback: CallbackQuery, db_user: User):
    """Show referral list."""
    async with get_session() as session:
        stmt = (
            select(User)
            .where(User.referred_by_id == db_user.id)
            .order_by(User.id.desc())
            .limit(20)
        )
        result = await session.execute(stmt)
        referrals = result.scalars().all()

    if not referrals:
        await callback.answer("هنوز زیرمجموعه‌ای ندارید.", show_alert=True)
        return

    text = "👥 <b>لیست زیرمجموعه‌ها</b>\n\n"
    for i, ref in enumerate(referrals, 1):
        text += (
            f"{i}. {ref.full_name} | "
            f"خرید: {ref.total_purchases} | "
            f"عضویت: {ref.created_at.strftime('%Y/%m/%d')}\n"
        )

    await callback.message.edit_text(
        text, reply_markup=UserKeyboards.back_button("main:menu")
    )
    await callback.answer()


@router.callback_query(F.data == "ref:withdraw")
async def referral_withdraw(callback: CallbackQuery, db_user: User):
    """Withdraw referral earnings to wallet."""
    if db_user.referral_earnings < settings.REFERRAL_MIN_WITHDRAW:
        await callback.answer(
            f"⚠️ حداقل مبلغ برداشت {settings.REFERRAL_MIN_WITHDRAW:,} تومان است.\n"
            f"درآمد فعلی: {db_user.referral_earnings:,} تومان",
            show_alert=True,
        )
        return

    async with get_session() as session:
        from core.database.models import Wallet, WalletTransaction, TransactionType

        # Get user and wallet
        user = await session.get(User, db_user.id)
        wallet_stmt = select(Wallet).where(Wallet.user_id == db_user.id)
        wallet_result = await session.execute(wallet_stmt)
        wallet = wallet_result.scalar_one_or_none()

        if not wallet:
            await callback.answer("⚠️ خطا در کیف پول.", show_alert=True)
            return

        amount = user.referral_earnings

        # Transfer to wallet
        wallet.balance += amount
        wallet.total_deposited += amount
        user.referral_earnings = 0

        # Record transaction
        tx = WalletTransaction(
            wallet_id=wallet.id,
            transaction_type=TransactionType.REFERRAL_BONUS,
            amount=amount,
            balance_after=wallet.balance,
            description="برداشت درآمد زیرمجموعه",
        )
        session.add(tx)

    await callback.answer(
        f"✅ مبلغ {amount:,} تومان به کیف پول شما واریز شد.", show_alert=True
    )
    await callback.message.edit_text(
        f"✅ <b>برداشت موفق</b>\n\n"
        f"مبلغ {amount:,} تومان به کیف پول شما واریز شد."
    )
