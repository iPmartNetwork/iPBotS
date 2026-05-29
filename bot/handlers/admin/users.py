"""Admin user management handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_kb import AdminKeyboards
from bot.states import AdminStates
from core.database.engine import get_session
from core.database.models import User, Wallet, WalletTransaction, TransactionType, Subscription, SubscriptionStatus

router = Router(name="admin_users")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(F.text == "👥 کاربران")
async def users_menu(message: Message, state: FSMContext):
    """Show users list."""
    await state.clear()

    async with get_session() as session:
        # Get all users with stats
        stmt = (
            select(User)
            .order_by(User.id.desc())
            .limit(20)
        )
        result = await session.execute(stmt)
        users = result.scalars().all()

        total_count = await session.scalar(select(func.count(User.id))) or 0

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()

    text = f"👥 <b>کاربران</b> ({total_count} نفر)\n\n"

    for user in users[:15]:
        status = "🟢" if user.is_active and not user.is_banned else "🔴"
        name = user.full_name[:15]
        builder.row(
            InlineKeyboardButton(
                text=f"{status} {name} | {user.telegram_id}",
                callback_data=f"admin:user:view:{user.id}",
            )
        )

    builder.row(
        InlineKeyboardButton(text="🔍 جستجو", callback_data="admin:user:search"),
    )

    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "admin:user:search")
async def search_user_prompt(callback: CallbackQuery, state: FSMContext):
    """Prompt for user search."""
    await callback.message.edit_text(
        "🔍 <b>جستجوی کاربر</b>\n\n"
        "شناسه تلگرام یا یوزرنیم را ارسال کنید:"
    )
    await state.set_state(AdminStates.user_search)
    await callback.answer()


@router.message(AdminStates.user_search)
async def search_user(message: Message, state: FSMContext):
    """Search for a user."""
    query = message.text.strip().replace("@", "")

    async with get_session() as session:
        try:
            telegram_id = int(query)
            stmt = select(User).where(User.telegram_id == telegram_id)
        except ValueError:
            stmt = select(User).where(User.username == query)

        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

    if not user:
        await message.answer("❌ کاربر یافت نشد.")
        await state.clear()
        return

    await state.clear()
    await _show_user_detail(message, user)


@router.callback_query(F.data.startswith("admin:user:view:"))
async def view_user(callback: CallbackQuery):
    """View user details."""
    user_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        user = await session.get(User, user_id)

    if not user:
        await callback.answer("❌ کاربر یافت نشد.", show_alert=True)
        return

    await _show_user_detail_callback(callback, user)
    await callback.answer()


async def _show_user_detail(message: Message, user: User):
    """Show user detail via message."""
    async with get_session() as session:
        # Get wallet
        wallet_stmt = select(Wallet).where(Wallet.user_id == user.id)
        wallet_result = await session.execute(wallet_stmt)
        wallet = wallet_result.scalar_one_or_none()

        # Count active subscriptions
        sub_count = await session.scalar(
            select(func.count(Subscription.id)).where(
                Subscription.user_id == user.id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
        ) or 0

        # Count referrals
        ref_count = await session.scalar(
            select(func.count(User.id)).where(User.referred_by_id == user.id)
        ) or 0

    balance = wallet.balance if wallet else 0
    status = "🟢 فعال" if user.is_active and not user.is_banned else "🔴 مسدود"

    text = (
        f"👤 <b>اطلاعات کاربر</b>\n\n"
        f"🆔 شناسه: <code>{user.telegram_id}</code>\n"
        f"👤 نام: {user.full_name}\n"
        f"📱 یوزرنیم: @{user.username or 'ندارد'}\n"
        f"📊 وضعیت: {status}\n"
        f"📅 عضویت: {user.created_at.strftime('%Y/%m/%d')}\n\n"
        f"💰 <b>مالی:</b>\n"
        f"   موجودی کیف پول: {balance:,} تومان\n"
        f"   مجموع خرید: {user.total_spent:,} تومان\n"
        f"   تعداد خرید: {user.total_purchases}\n\n"
        f"📦 <b>سرویس‌ها:</b>\n"
        f"   فعال: {sub_count}\n\n"
        f"👥 <b>زیرمجموعه:</b> {ref_count} نفر\n"
        f"🔗 کد دعوت: <code>{user.referral_code}</code>"
    )

    if user.is_banned:
        text += f"\n\n🚫 دلیل مسدودی: {user.ban_reason or 'نامشخص'}"

    await message.answer(text, reply_markup=AdminKeyboards.user_management(user.id))


async def _show_user_detail_callback(callback: CallbackQuery, user: User):
    """Show user detail via callback."""
    async with get_session() as session:
        wallet_stmt = select(Wallet).where(Wallet.user_id == user.id)
        wallet_result = await session.execute(wallet_stmt)
        wallet = wallet_result.scalar_one_or_none()

        sub_count = await session.scalar(
            select(func.count(Subscription.id)).where(
                Subscription.user_id == user.id,
                Subscription.status == SubscriptionStatus.ACTIVE,
            )
        ) or 0

        ref_count = await session.scalar(
            select(func.count(User.id)).where(User.referred_by_id == user.id)
        ) or 0

    balance = wallet.balance if wallet else 0
    status = "🟢 فعال" if user.is_active and not user.is_banned else "🔴 مسدود"

    text = (
        f"👤 <b>اطلاعات کاربر</b>\n\n"
        f"🆔 شناسه: <code>{user.telegram_id}</code>\n"
        f"👤 نام: {user.full_name}\n"
        f"📱 یوزرنیم: @{user.username or 'ندارد'}\n"
        f"📊 وضعیت: {status}\n"
        f"📅 عضویت: {user.created_at.strftime('%Y/%m/%d')}\n\n"
        f"💰 موجودی: {balance:,} تومان\n"
        f"🛒 خرید: {user.total_purchases} ({user.total_spent:,} ت)\n"
        f"📦 سرویس فعال: {sub_count}\n"
        f"👥 زیرمجموعه: {ref_count}"
    )

    await callback.message.edit_text(text, reply_markup=AdminKeyboards.user_management(user.id))


@router.callback_query(F.data.startswith("admin:user:credit:"))
async def credit_user_start(callback: CallbackQuery, state: FSMContext):
    """Start crediting user wallet."""
    user_id = int(callback.data.split(":")[3])
    await state.update_data(credit_user_id=user_id)
    await state.set_state(AdminStates.user_credit_amount)
    await callback.message.edit_text("💰 مبلغ شارژ کیف پول را به تومان وارد کنید:")
    await callback.answer()


@router.message(AdminStates.user_credit_amount)
async def credit_user_process(message: Message, state: FSMContext):
    """Process wallet credit."""
    try:
        amount = int(message.text.replace(",", "").strip())
    except ValueError:
        await message.answer("❌ عدد معتبر وارد کنید.")
        return

    if amount <= 0:
        await message.answer("❌ مبلغ باید بیشتر از صفر باشد.")
        return

    data = await state.get_data()
    user_id = data.get("credit_user_id")

    async with get_session() as session:
        wallet_stmt = select(Wallet).where(Wallet.user_id == user_id)
        wallet_result = await session.execute(wallet_stmt)
        wallet = wallet_result.scalar_one_or_none()

        if not wallet:
            await message.answer("❌ کیف پول کاربر یافت نشد.")
            await state.clear()
            return

        wallet.balance += amount
        wallet.total_deposited += amount

        tx = WalletTransaction(
            wallet_id=wallet.id,
            transaction_type=TransactionType.ADMIN_CREDIT,
            amount=amount,
            balance_after=wallet.balance,
            description="شارژ توسط ادمین",
        )
        session.add(tx)

        # Get user for notification
        user = await session.get(User, user_id)

    await message.answer(
        f"✅ مبلغ {amount:,} تومان به کیف پول اضافه شد.\n"
        f"موجودی جدید: {wallet.balance:,} تومان"
    )

    # Notify user
    if user:
        from bot.loader import bot
        try:
            await bot.send_message(
                user.telegram_id,
                f"💰 مبلغ {amount:,} تومان به کیف پول شما اضافه شد.",
            )
        except Exception:
            pass

    await state.clear()


@router.callback_query(F.data.startswith("admin:user:ban:"))
async def ban_user_start(callback: CallbackQuery, state: FSMContext):
    """Start banning user."""
    user_id = int(callback.data.split(":")[3])
    await state.update_data(ban_user_id=user_id)
    await state.set_state(AdminStates.user_ban_reason)
    await callback.message.edit_text("🚫 دلیل مسدودسازی را وارد کنید:")
    await callback.answer()


@router.callback_query(F.data.startswith("admin:user:unban:"))
async def unban_user(callback: CallbackQuery):
    """Unban a user."""
    user_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.is_banned = False
            user.ban_reason = None

    await callback.answer("✅ کاربر رفع مسدودی شد.", show_alert=True)
    await callback.message.edit_text("✅ کاربر رفع مسدودی شد.")


@router.message(AdminStates.user_ban_reason)
async def ban_user_process(message: Message, state: FSMContext):
    """Process user ban."""
    reason = message.text.strip()
    data = await state.get_data()
    user_id = data.get("ban_user_id")

    async with get_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.is_banned = True
            user.ban_reason = reason

    await message.answer(f"✅ کاربر مسدود شد.\nدلیل: {reason}")
    await state.clear()


@router.callback_query(F.data.startswith("admin:user:msg:"))
async def message_user_start(callback: CallbackQuery, state: FSMContext):
    """Start sending message to user."""
    user_id = int(callback.data.split(":")[3])
    await state.update_data(msg_user_id=user_id)
    await state.set_state(AdminStates.user_message)
    await callback.message.edit_text("📩 پیام خود را بنویسید:")
    await callback.answer()


@router.message(AdminStates.user_message)
async def message_user_process(message: Message, state: FSMContext):
    """Send message to user."""
    data = await state.get_data()
    user_id = data.get("msg_user_id")

    async with get_session() as session:
        user = await session.get(User, user_id)

    if not user:
        await message.answer("❌ کاربر یافت نشد.")
        await state.clear()
        return

    from bot.loader import bot

    try:
        await bot.send_message(
            user.telegram_id,
            f"📩 <b>پیام از مدیریت:</b>\n\n{message.text}",
        )
        await message.answer("✅ پیام ارسال شد.")
    except Exception as e:
        await message.answer(f"❌ خطا در ارسال: {e}")

    await state.clear()


@router.callback_query(F.data.startswith("admin:user:subs:"))
async def user_subscriptions(callback: CallbackQuery):
    """Show user's subscriptions."""
    user_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        from sqlalchemy.orm import selectinload
        stmt = (
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .options(selectinload(Subscription.plan))
            .order_by(Subscription.id.desc())
            .limit(10)
        )
        result = await session.execute(stmt)
        subs = result.scalars().all()

    if not subs:
        await callback.answer("سرویسی ندارد.", show_alert=True)
        return

    text = "📦 <b>سرویس‌های کاربر:</b>\n\n"
    for sub in subs:
        status = "✅" if sub.is_active else "❌"
        plan_name = sub.plan.name if sub.plan else "نامشخص"
        text += (
            f"{status} {plan_name}\n"
            f"   📊 {sub.used_traffic_gb}/{sub.data_limit_gb}GB | "
            f"⏱️ {sub.remaining_days} روز\n\n"
        )

    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data.startswith("admin:user:wallet:"))
async def user_wallet_info(callback: CallbackQuery):
    """Show user wallet info."""
    user_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        wallet_stmt = select(Wallet).where(Wallet.user_id == user_id)
        wallet_result = await session.execute(wallet_stmt)
        wallet = wallet_result.scalar_one_or_none()

        if not wallet:
            await callback.answer("کیف پول خالی.", show_alert=True)
            return

        tx_stmt = (
            select(WalletTransaction)
            .where(WalletTransaction.wallet_id == wallet.id)
            .order_by(WalletTransaction.id.desc())
            .limit(5)
        )
        tx_result = await session.execute(tx_stmt)
        transactions = tx_result.scalars().all()

    text = (
        f"💰 <b>کیف پول کاربر</b>\n\n"
        f"💵 موجودی: {wallet.balance:,} تومان\n"
        f"📥 واریز: {wallet.total_deposited:,} تومان\n"
        f"📤 خرج: {wallet.total_spent:,} تومان\n\n"
    )

    if transactions:
        text += "📜 <b>آخرین تراکنش‌ها:</b>\n"
        for tx in transactions:
            text += f"  • {tx.amount:,}ت | {tx.description or tx.transaction_type.value}\n"

    await callback.message.edit_text(text)
    await callback.answer()
