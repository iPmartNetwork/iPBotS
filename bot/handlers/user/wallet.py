"""Wallet handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from bot.keyboards.user_kb import UserKeyboards
from bot.states import UserStates
from core.database.engine import get_session
from core.database.models import User, Wallet, WalletTransaction, TransactionType

router = Router(name="wallet")


@router.message(F.text == "💰 کیف پول")
async def show_wallet(message: Message, db_user: User, state: FSMContext):
    """Show wallet info."""
    await state.clear()

    async with get_session() as session:
        stmt = select(Wallet).where(Wallet.user_id == db_user.id)
        result = await session.execute(stmt)
        wallet = result.scalar_one_or_none()

    balance = wallet.balance if wallet else 0
    total_deposited = wallet.total_deposited if wallet else 0
    total_spent = wallet.total_spent if wallet else 0

    from core.services.bot_texts import get_text
    wallet_text = await get_text(
        "wallet_title",
        balance=f"{balance:,}",
        deposited=f"{total_deposited:,}",
        spent=f"{total_spent:,}",
    )

    await message.answer(wallet_text, reply_markup=UserKeyboards.wallet_menu())


@router.callback_query(F.data == "wallet:charge")
async def wallet_charge(callback: CallbackQuery, state: FSMContext):
    """Start wallet charge flow."""
    await callback.message.edit_text(
        "💰 <b>شارژ کیف پول</b>\n\n"
        "مبلغ مورد نظر را به تومان وارد کنید:\n"
        "(حداقل 10,000 تومان)"
    )
    await state.set_state(UserStates.wallet_charge_amount)
    await callback.answer()


@router.message(UserStates.wallet_charge_amount)
async def process_charge_amount(message: Message, state: FSMContext, db_user: User):
    """Process wallet charge amount."""
    try:
        amount = int(message.text.replace(",", "").replace("٬", "").strip())
    except ValueError:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کنید.")
        return

    if amount < 10000:
        await message.answer("❌ حداقل مبلغ شارژ 10,000 تومان است.")
        return

    if amount > 50000000:
        await message.answer("❌ حداکثر مبلغ شارژ 50,000,000 تومان است.")
        return

    await state.update_data(charge_amount=amount)

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 زرین‌پال", callback_data="wallet:pay:zarinpal"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏦 کارت به کارت", callback_data="wallet:pay:card2card"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🪙 ارز دیجیتال", callback_data="wallet:pay:crypto"
                ),
            ],
            [
                InlineKeyboardButton(text="❌ انصراف", callback_data="main:menu"),
            ],
        ]
    )

    await message.answer(
        f"💰 مبلغ شارژ: <b>{amount:,}</b> تومان\n\n"
        f"روش پرداخت را انتخاب کنید:",
        reply_markup=kb,
    )


@router.callback_query(F.data == "wallet:pay:zarinpal")
async def wallet_pay_zarinpal(callback: CallbackQuery, state: FSMContext, db_user: User):
    """Pay wallet charge via ZarinPal."""
    data = await state.get_data()
    amount = data.get("charge_amount", 0)

    if not amount:
        await callback.answer("⚠️ خطا. لطفاً دوباره تلاش کنید.", show_alert=True)
        await state.clear()
        return

    from core.database.models import Order, OrderStatus, OrderType

    async with get_session() as session:
        order = Order(
            user_id=db_user.id,
            plan_id=None,
            order_type=OrderType.WALLET_CHARGE,
            status=OrderStatus.PENDING,
            amount=amount,
            original_amount=amount,
            payment_method="zarinpal",
        )
        session.add(order)
        await session.flush()
        order_id = order.id

    from core.services.payment.zarinpal import ZarinPalService

    zarinpal = ZarinPalService()
    result = await zarinpal.create_payment(
        amount=amount,
        description="شارژ کیف پول",
        order_id=str(order_id),
    )

    if result.success:
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 پرداخت", url=result.payment_url)],
                [InlineKeyboardButton(text="❌ انصراف", callback_data="main:menu")],
            ]
        )
        await callback.message.edit_text(
            f"💳 <b>پرداخت شارژ کیف پول</b>\n\n"
            f"مبلغ: <b>{amount:,}</b> تومان\n\n"
            f"برای پرداخت روی دکمه زیر کلیک کنید:",
            reply_markup=kb,
        )
    else:
        await callback.message.edit_text(f"❌ خطا: {result.error}")

    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "wallet:history")
async def wallet_history(callback: CallbackQuery, db_user: User):
    """Show wallet transaction history."""
    async with get_session() as session:
        stmt = select(Wallet).where(Wallet.user_id == db_user.id)
        result = await session.execute(stmt)
        wallet = result.scalar_one_or_none()

        if not wallet:
            await callback.answer("کیف پول شما خالی است.", show_alert=True)
            return

        tx_stmt = (
            select(WalletTransaction)
            .where(WalletTransaction.wallet_id == wallet.id)
            .order_by(WalletTransaction.id.desc())
            .limit(10)
        )
        tx_result = await session.execute(tx_stmt)
        transactions = tx_result.scalars().all()

    if not transactions:
        await callback.answer("تراکنشی یافت نشد.", show_alert=True)
        return

    text = "📜 <b>آخرین تراکنش‌ها</b>\n\n"
    for tx in transactions:
        icon = "📥" if tx.transaction_type in (
            TransactionType.DEPOSIT,
            TransactionType.REFUND,
            TransactionType.REFERRAL_BONUS,
            TransactionType.ADMIN_CREDIT,
        ) else "📤"
        text += (
            f"{icon} {tx.amount:,} تومان | "
            f"{tx.description or tx.transaction_type.value}\n"
            f"   💰 مانده: {tx.balance_after:,} تومان\n\n"
        )

    await callback.message.edit_text(
        text, reply_markup=UserKeyboards.back_button("main:menu")
    )
    await callback.answer()


@router.callback_query(F.data == "wallet:withdraw")
async def wallet_withdraw(callback: CallbackQuery, state: FSMContext, db_user: User):
    """Start withdrawal flow."""
    async with get_session() as session:
        stmt = select(Wallet).where(Wallet.user_id == db_user.id)
        result = await session.execute(stmt)
        wallet = result.scalar_one_or_none()

    if not wallet or wallet.balance < 50000:
        await callback.answer(
            "⚠️ حداقل موجودی برای برداشت 50,000 تومان است.", show_alert=True
        )
        return

    await callback.message.edit_text(
        f"💸 <b>برداشت موجودی</b>\n\n"
        f"موجودی فعلی: {wallet.balance:,} تومان\n\n"
        f"مبلغ مورد نظر برای برداشت را وارد کنید:"
    )
    await state.set_state(UserStates.wallet_withdraw_amount)
    await callback.answer()


@router.message(UserStates.wallet_withdraw_amount)
async def process_withdraw_amount(message: Message, state: FSMContext, db_user: User):
    """Process withdrawal amount."""
    try:
        amount = int(message.text.replace(",", "").strip())
    except ValueError:
        await message.answer("❌ عدد معتبر وارد کنید.")
        return

    if amount < 50000:
        await message.answer("❌ حداقل مبلغ برداشت 50,000 تومان است.")
        return

    async with get_session() as session:
        stmt = select(Wallet).where(Wallet.user_id == db_user.id)
        result = await session.execute(stmt)
        wallet = result.scalar_one_or_none()

        if not wallet or wallet.balance < amount:
            await message.answer("❌ موجودی کافی نیست.")
            await state.clear()
            return

    await message.answer(
        f"💸 درخواست برداشت {amount:,} تومان ثبت شد.\n"
        f"⏳ پس از بررسی توسط مدیریت، مبلغ واریز خواهد شد."
    )

    # Notify admins
    from bot.loader import bot
    from core.services.notification import NotificationService
    notifier = NotificationService(bot)
    await notifier.notify_admins(
        f"💸 <b>درخواست برداشت</b>\n\n"
        f"👤 کاربر: {db_user.telegram_id}\n"
        f"💰 مبلغ: {amount:,} تومان"
    )

    await state.clear()


@router.callback_query(F.data == "wallet:pay:card2card")
async def wallet_pay_card2card(callback: CallbackQuery, state: FSMContext, db_user: User):
    """Charge wallet via card2card."""
    data = await state.get_data()
    amount = data.get("charge_amount", 0)

    if not amount:
        await callback.answer("⚠️ خطا.", show_alert=True)
        await state.clear()
        return

    from core.services.payment.card2card import Card2CardService
    card_service = Card2CardService()
    info = card_service.get_payment_info(amount)

    from core.database.models import Order, OrderType, OrderStatus

    async with get_session() as session:
        order = Order(
            user_id=db_user.id,
            order_type=OrderType.WALLET_CHARGE,
            status=OrderStatus.PENDING,
            amount=amount,
            original_amount=amount,
            payment_method="card2card",
        )
        session.add(order)
        await session.flush()
        order_id = order.id

    await callback.message.edit_text(
        f"{info}\n\n"
        f"💰 شارژ کیف پول: {amount:,} تومان\n\n"
        f"لطفاً پس از واریز، تصویر رسید را ارسال کنید."
    )

    await state.set_state(UserStates.card2card_receipt)
    await state.update_data(order_id=order_id)
    await callback.answer()
