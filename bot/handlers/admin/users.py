"""Admin user management handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, or_

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_kb import AdminKeyboards
from bot.states import AdminStates
from core.database.engine import get_session
from core.database.models import User, Wallet, WalletTransaction, TransactionType

router = Router(name="admin_users")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(F.text == "👥 کاربران")
async def users_menu(message: Message, state: FSMContext):
    """Show users management."""
    await message.answer(
        "👥 <b>مدیریت کاربران</b>\n\n"
        "شناسه تلگرام یا یوزرنیم کاربر را ارسال کنید:"
    )
    await state.set_state(AdminStates.user_search)


@router.message(AdminStates.user_search)
async def search_user(message: Message, state: FSMContext):
    """Search for a user."""
    query = message.text.strip().replace("@", "")

    async with get_session() as session:
        # Search by telegram_id or username
        try:
            telegram_id = int(query)
            stmt = select(User).where(User.telegram_id == telegram_id)
        except ValueError:
            stmt = select(User).where(User.username == query)

        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

    if not user:
        await message.answer("❌ کاربر یافت نشد. دوباره تلاش کنید.")
        return

    await state.clear()

    user_text = (
        f"👤 <b>اطلاعات کاربر</b>\n\n"
        f"🆔 شناسه: <code>{user.telegram_id}</code>\n"
        f"👤 نام: {user.full_name}\n"
        f"📱 یوزرنیم: @{user.username or 'ندارد'}\n"
        f"📅 عضویت: {user.created_at.strftime('%Y/%m/%d')}\n"
        f"🛒 خرید: {user.total_purchases}\n"
        f"💰 مجموع خرید: {user.total_spent:,} تومان\n"
        f"🚫 مسدود: {'بله' if user.is_banned else 'خیر'}\n"
        f"🔗 کد دعوت: {user.referral_code}\n"
    )

    await message.answer(
        user_text, reply_markup=AdminKeyboards.user_management(user.id)
    )


@router.callback_query(F.data.startswith("admin:user:credit:"))
async def credit_user_start(callback: CallbackQuery, state: FSMContext):
    """Start crediting user wallet."""
    user_id = int(callback.data.split(":")[3])
    await state.update_data(credit_user_id=user_id)
    await state.set_state(AdminStates.user_credit_amount)
    await callback.message.edit_text(
        "💰 مبلغ شارژ کیف پول را به تومان وارد کنید:"
    )
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
            description=f"شارژ توسط ادمین",
        )
        session.add(tx)

    await message.answer(
        f"✅ مبلغ {amount:,} تومان به کیف پول کاربر اضافه شد.\n"
        f"موجودی جدید: {wallet.balance:,} تومان"
    )

    # Notify user
    user_stmt = select(User).where(User.id == user_id)
    async with get_session() as session:
        user_result = await session.execute(user_stmt)
        user = user_result.scalar_one_or_none()

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
