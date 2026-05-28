"""Custom plan builder handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from bot.keyboards.user_kb import UserKeyboards
from core.database.engine import get_session
from core.database.models import User
from core.database.models.custom_plan import CustomPlanConfig

router = Router(name="custom_plan")


class CustomPlanStates(StatesGroup):
    """States for custom plan builder."""

    select_data = State()
    select_duration = State()
    select_ip = State()
    confirm = State()


@router.callback_query(F.data == "shop:custom")
async def start_custom_plan(callback: CallbackQuery, state: FSMContext):
    """Start custom plan builder."""
    async with get_session() as session:
        stmt = select(CustomPlanConfig).where(CustomPlanConfig.is_active == True)
        result = await session.execute(stmt)
        config = result.scalar_one_or_none()

    if not config:
        await callback.answer("⚠️ ساخت پلن سفارشی غیرفعال است.", show_alert=True)
        return

    await state.update_data(custom_config_id=config.id)

    text = (
        f"🛠️ <b>ساخت پلن سفارشی</b>\n\n"
        f"حجم ترافیک مورد نظر خود را به گیگابایت وارد کنید:\n\n"
        f"📊 حداقل: {config.min_data_gb} GB\n"
        f"📊 حداکثر: {config.max_data_gb} GB\n"
        f"💰 هر گیگابایت: {config.price_per_gb:,} تومان\n\n"
        f"🔢 عدد مورد نظر را ارسال کنید:"
    )

    await callback.message.edit_text(text)
    await state.set_state(CustomPlanStates.select_data)
    await callback.answer()


@router.message(CustomPlanStates.select_data)
async def process_custom_data(message: Message, state: FSMContext):
    """Process custom data selection."""
    try:
        data_gb = int(message.text.strip())
    except ValueError:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کنید.")
        return

    async with get_session() as session:
        data = await state.get_data()
        config = await session.get(CustomPlanConfig, data["custom_config_id"])

    if data_gb < config.min_data_gb or data_gb > config.max_data_gb:
        await message.answer(
            f"❌ حجم باید بین {config.min_data_gb} تا {config.max_data_gb} گیگابایت باشد."
        )
        return

    await state.update_data(custom_data_gb=data_gb)

    text = (
        f"✅ حجم: {data_gb} GB\n\n"
        f"⏱️ <b>مدت زمان</b> مورد نظر را به روز وارد کنید:\n\n"
        f"📅 حداقل: {config.min_duration_days} روز\n"
        f"📅 حداکثر: {config.max_duration_days} روز\n"
        f"💰 هر روز: {config.price_per_day:,} تومان\n\n"
        f"🔢 عدد مورد نظر را ارسال کنید:"
    )

    await message.answer(text)
    await state.set_state(CustomPlanStates.select_duration)


@router.message(CustomPlanStates.select_duration)
async def process_custom_duration(message: Message, state: FSMContext):
    """Process custom duration selection."""
    try:
        duration_days = int(message.text.strip())
    except ValueError:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کنید.")
        return

    async with get_session() as session:
        data = await state.get_data()
        config = await session.get(CustomPlanConfig, data["custom_config_id"])

    if duration_days < config.min_duration_days or duration_days > config.max_duration_days:
        await message.answer(
            f"❌ مدت باید بین {config.min_duration_days} تا {config.max_duration_days} روز باشد."
        )
        return

    await state.update_data(custom_duration=duration_days)

    text = (
        f"✅ مدت: {duration_days} روز\n\n"
        f"👥 <b>تعداد کاربر همزمان</b> را وارد کنید:\n\n"
        f"👤 حداقل: {config.min_ip_limit}\n"
        f"👥 حداکثر: {config.max_ip_limit}\n"
        f"💰 هر کاربر اضافه: {config.price_per_ip:,} تومان\n\n"
        f"🔢 عدد مورد نظر را ارسال کنید:"
    )

    await message.answer(text)
    await state.set_state(CustomPlanStates.select_ip)


@router.message(CustomPlanStates.select_ip)
async def process_custom_ip(message: Message, state: FSMContext):
    """Process IP limit and show summary."""
    try:
        ip_limit = int(message.text.strip())
    except ValueError:
        await message.answer("❌ لطفاً یک عدد معتبر وارد کنید.")
        return

    async with get_session() as session:
        data = await state.get_data()
        config = await session.get(CustomPlanConfig, data["custom_config_id"])

    if ip_limit < config.min_ip_limit or ip_limit > config.max_ip_limit:
        await message.answer(
            f"❌ تعداد باید بین {config.min_ip_limit} تا {config.max_ip_limit} باشد."
        )
        return

    data_gb = data["custom_data_gb"]
    duration_days = data["custom_duration"]

    # Calculate price
    total_price = config.calculate_price(data_gb, duration_days, ip_limit)

    await state.update_data(custom_ip=ip_limit, custom_price=total_price)

    # Show summary
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💳 پرداخت آنلاین", callback_data="custom:pay:zarinpal"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💰 پرداخت از کیف پول", callback_data="custom:pay:wallet"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🪙 ارز دیجیتال", callback_data="custom:pay:crypto"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🏦 کارت به کارت", callback_data="custom:pay:card2card"
                ),
            ],
            [
                InlineKeyboardButton(text="❌ انصراف", callback_data="shop:categories"),
            ],
        ]
    )

    discount_text = ""
    if data_gb >= config.bulk_discount_threshold_gb:
        discount_text = f"\n🏷️ تخفیف حجم بالا: {config.bulk_discount_percent}%"

    text = (
        f"🛠️ <b>خلاصه پلن سفارشی</b>\n\n"
        f"📊 حجم: {data_gb} GB\n"
        f"⏱️ مدت: {duration_days} روز\n"
        f"👥 کاربر همزمان: {ip_limit}\n"
        f"{discount_text}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 قیمت نهایی: <b>{total_price:,}</b> تومان\n\n"
        f"روش پرداخت را انتخاب کنید:"
    )

    await message.answer(text, reply_markup=kb)
    await state.set_state(CustomPlanStates.confirm)


@router.callback_query(CustomPlanStates.confirm, F.data.startswith("custom:pay:"))
async def process_custom_payment(callback: CallbackQuery, state: FSMContext, db_user: User):
    """Process custom plan payment."""
    method = callback.data.split(":")[2]
    data = await state.get_data()

    data_gb = data["custom_data_gb"]
    duration_days = data["custom_duration"]
    ip_limit = data["custom_ip"]
    total_price = data["custom_price"]

    # Create order
    from core.database.models import Order, OrderType, OrderStatus

    async with get_session() as session:
        order = Order(
            user_id=db_user.id,
            plan_id=None,
            order_type=OrderType.NEW,
            status=OrderStatus.PENDING,
            amount=total_price,
            original_amount=total_price,
            payment_method=method,
            note=f"Custom: {data_gb}GB, {duration_days}d, {ip_limit}ip",
        )
        session.add(order)
        await session.flush()
        order_id = order.id

    await state.update_data(custom_order_id=order_id)

    if method == "wallet":
        # Direct wallet payment
        from core.database.models import Wallet, WalletTransaction, TransactionType

        async with get_session() as session:
            wallet_stmt = select(Wallet).where(Wallet.user_id == db_user.id)
            from sqlalchemy import select as sel
            wallet_result = await session.execute(wallet_stmt)
            wallet = wallet_result.scalar_one_or_none()

            if not wallet or wallet.balance < total_price:
                await callback.answer("⚠️ موجودی کیف پول کافی نیست.", show_alert=True)
                return

            wallet.balance -= total_price
            wallet.total_spent += total_price

            tx = WalletTransaction(
                wallet_id=wallet.id,
                transaction_type=TransactionType.PURCHASE,
                amount=total_price,
                balance_after=wallet.balance,
                description=f"خرید پلن سفارشی: {data_gb}GB/{duration_days}d",
                reference_id=f"order_{order_id}",
            )
            session.add(tx)

            order_obj = await session.get(Order, order_id)
            order_obj.status = OrderStatus.PAID

        await callback.message.edit_text("✅ پرداخت موفق! در حال ایجاد سرویس...")
        # TODO: Create subscription with custom params
        await callback.answer("✅ پرداخت انجام شد!")

    elif method == "zarinpal":
        from core.services.payment.zarinpal import ZarinPalService

        zarinpal = ZarinPalService()
        result = await zarinpal.create_payment(
            amount=total_price,
            description=f"پلن سفارشی {data_gb}GB/{duration_days}d",
            order_id=str(order_id),
        )

        if result.success:
            from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="💳 پرداخت", url=result.payment_url)],
                ]
            )
            await callback.message.edit_text(
                f"💳 مبلغ: {total_price:,} تومان\n\nبرای پرداخت کلیک کنید:",
                reply_markup=kb,
            )
        else:
            await callback.message.edit_text(f"❌ خطا: {result.error}")

        await callback.answer()

    await state.clear()
