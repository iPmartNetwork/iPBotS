"""Shop handlers - browsing and purchasing plans."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.keyboards.user_kb import UserKeyboards
from bot.states import UserStates
from core.database.engine import get_session
from core.database.models import (
    Plan,
    PlanCategory,
    Order,
    OrderStatus,
    OrderType,
    User,
    DiscountCode,
)

router = Router(name="shop")


@router.message(F.text == "🛒 خرید سرویس")
async def show_shop(message: Message):
    """Show shop categories."""
    async with get_session() as session:
        stmt = (
            select(PlanCategory)
            .where(PlanCategory.is_active == True)
            .order_by(PlanCategory.sort_order)
        )
        result = await session.execute(stmt)
        categories = result.scalars().all()

    if not categories:
        await message.answer("⚠️ در حال حاضر سرویسی موجود نیست.")
        return

    await message.answer(
        "🛒 <b>فروشگاه</b>\n\nدسته‌بندی مورد نظر خود را انتخاب کنید:",
        reply_markup=UserKeyboards.shop_categories(categories),
    )


@router.callback_query(F.data == "shop:categories")
async def show_categories(callback: CallbackQuery):
    """Show categories via callback."""
    async with get_session() as session:
        stmt = (
            select(PlanCategory)
            .where(PlanCategory.is_active == True)
            .order_by(PlanCategory.sort_order)
        )
        result = await session.execute(stmt)
        categories = result.scalars().all()

    await callback.message.edit_text(
        "🛒 <b>فروشگاه</b>\n\nدسته‌بندی مورد نظر خود را انتخاب کنید:",
        reply_markup=UserKeyboards.shop_categories(categories),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("shop:category:"))
async def show_plans(callback: CallbackQuery):
    """Show plans in a category."""
    category_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        stmt = (
            select(Plan)
            .where(Plan.category_id == category_id)
            .where(Plan.is_active == True)
            .where((Plan.stock == -1) | (Plan.stock > 0))
            .order_by(Plan.sort_order)
        )
        result = await session.execute(stmt)
        plans = result.scalars().all()

    if not plans:
        await callback.answer("⚠️ پلنی در این دسته‌بندی موجود نیست.", show_alert=True)
        return

    await callback.message.edit_text(
        "📋 <b>پلن‌های موجود</b>\n\nپلن مورد نظر خود را انتخاب کنید:",
        reply_markup=UserKeyboards.plan_list(plans),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("shop:plan:"))
async def show_plan_detail(callback: CallbackQuery):
    """Show plan details."""
    plan_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        stmt = select(Plan).where(Plan.id == plan_id)
        result = await session.execute(stmt)
        plan = result.scalar_one_or_none()

    if not plan:
        await callback.answer("⚠️ پلن یافت نشد.", show_alert=True)
        return

    detail_text = (
        f"📋 <b>{plan.name}</b>\n\n"
        f"📊 حجم: {plan.display_data}\n"
        f"⏱️ مدت: {plan.display_duration}\n"
        f"👥 کاربر همزمان: {plan.ip_limit}\n"
    )

    if plan.speed_limit > 0:
        detail_text += f"⚡ سرعت: {plan.speed_limit} Mbps\n"

    if plan.discount_percent > 0:
        detail_text += (
            f"\n💰 قیمت اصلی: <s>{plan.price:,}</s> تومان\n"
            f"🏷️ تخفیف: {plan.discount_percent}%\n"
            f"✅ قیمت نهایی: <b>{plan.final_price:,}</b> تومان"
        )
    else:
        detail_text += f"\n💰 قیمت: <b>{plan.final_price:,}</b> تومان"

    if plan.description:
        detail_text += f"\n\n📝 {plan.description}"

    await callback.message.edit_text(
        detail_text,
        reply_markup=UserKeyboards.plan_detail(plan_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay:wallet:"))
async def pay_with_wallet(callback: CallbackQuery, db_user: User):
    """Pay with wallet balance."""
    plan_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        # Get plan
        plan = await session.get(Plan, plan_id)
        if not plan:
            await callback.answer("⚠️ پلن یافت نشد.", show_alert=True)
            return

        # Get wallet
        from core.database.models import Wallet
        from sqlalchemy import select as sel

        wallet_stmt = sel(Wallet).where(Wallet.user_id == db_user.id)
        wallet_result = await session.execute(wallet_stmt)
        wallet = wallet_result.scalar_one_or_none()

        if not wallet or wallet.balance < plan.final_price:
            await callback.answer(
                f"⚠️ موجودی کیف پول کافی نیست.\n"
                f"موجودی: {wallet.balance if wallet else 0:,} تومان\n"
                f"مبلغ مورد نیاز: {plan.final_price:,} تومان",
                show_alert=True,
            )
            return

        # Create order
        order = Order(
            user_id=db_user.id,
            plan_id=plan_id,
            order_type=OrderType.NEW,
            status=OrderStatus.PAID,
            amount=plan.final_price,
            original_amount=plan.price,
            discount_amount=plan.price - plan.final_price,
            payment_method="wallet",
        )
        session.add(order)
        await session.flush()

        # Deduct from wallet
        wallet.balance -= plan.final_price
        wallet.total_spent += plan.final_price

        # Record transaction
        from core.database.models import WalletTransaction, TransactionType

        tx = WalletTransaction(
            wallet_id=wallet.id,
            transaction_type=TransactionType.PURCHASE,
            amount=plan.final_price,
            balance_after=wallet.balance,
            description=f"خرید پلن: {plan.name}",
            reference_id=f"order_{order.id}",
        )
        session.add(tx)

    # Create subscription on panel
    await _create_subscription(callback, db_user, plan_id, order.id)

    await callback.answer("✅ پرداخت با موفقیت انجام شد!", show_alert=True)


@router.callback_query(F.data.startswith("pay:zarinpal:"))
async def pay_with_zarinpal(callback: CallbackQuery, db_user: User):
    """Initiate ZarinPal payment."""
    plan_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        plan = await session.get(Plan, plan_id)
        if not plan:
            await callback.answer("⚠️ پلن یافت نشد.", show_alert=True)
            return

        # Create pending order
        order = Order(
            user_id=db_user.id,
            plan_id=plan_id,
            order_type=OrderType.NEW,
            status=OrderStatus.PENDING,
            amount=plan.final_price,
            original_amount=plan.price,
            discount_amount=plan.price - plan.final_price,
            payment_method="zarinpal",
        )
        session.add(order)
        await session.flush()
        order_id = order.id

    # Create payment
    from core.services.payment.zarinpal import ZarinPalService

    zarinpal = ZarinPalService()
    result = await zarinpal.create_payment(
        amount=plan.final_price,
        description=f"خرید پلن {plan.name}",
        order_id=str(order_id),
    )

    if result.success:
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💳 پرداخت آنلاین", url=result.payment_url
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 انصراف", callback_data=f"order:cancel:{order_id}"
                    )
                ],
            ]
        )
        await callback.message.edit_text(
            f"💳 <b>پرداخت آنلاین</b>\n\n"
            f"مبلغ: <b>{plan.final_price:,}</b> تومان\n"
            f"شماره سفارش: #{order_id}\n\n"
            f"برای پرداخت روی دکمه زیر کلیک کنید:",
            reply_markup=kb,
        )
    else:
        await callback.message.edit_text(
            f"❌ خطا در ایجاد درگاه پرداخت.\n{result.error}"
        )

    await callback.answer()


@router.callback_query(F.data.startswith("pay:card2card:"))
async def pay_card2card(callback: CallbackQuery, db_user: User, state: FSMContext):
    """Card to card payment."""
    plan_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        plan = await session.get(Plan, plan_id)
        if not plan:
            await callback.answer("⚠️ پلن یافت نشد.", show_alert=True)
            return

        # Create pending order
        order = Order(
            user_id=db_user.id,
            plan_id=plan_id,
            order_type=OrderType.NEW,
            status=OrderStatus.PENDING,
            amount=plan.final_price,
            original_amount=plan.price,
            discount_amount=plan.price - plan.final_price,
            payment_method="card2card",
        )
        session.add(order)
        await session.flush()
        order_id = order.id

    from core.services.payment.card2card import Card2CardService

    card_service = Card2CardService()
    info = card_service.get_payment_info(plan.final_price)

    await callback.message.edit_text(
        f"{info}\n\n"
        f"📌 شماره سفارش: #{order_id}\n\n"
        f"لطفاً پس از واریز، تصویر رسید بانکی را ارسال کنید."
    )

    await state.set_state(UserStates.card2card_receipt)
    await state.update_data(order_id=order_id, plan_id=plan_id)
    await callback.answer()


@router.callback_query(F.data.startswith("pay:crypto:"))
async def pay_crypto_options(callback: CallbackQuery):
    """Show crypto payment options."""
    plan_id = int(callback.data.split(":")[2])
    await callback.message.edit_text(
        "🪙 <b>پرداخت ارز دیجیتال</b>\n\nدرگاه مورد نظر را انتخاب کنید:",
        reply_markup=UserKeyboards.crypto_options(plan_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("discount:apply:"))
async def apply_discount(callback: CallbackQuery, state: FSMContext):
    """Ask for discount code."""
    plan_id = int(callback.data.split(":")[2])
    await state.set_state(UserStates.enter_discount_code)
    await state.update_data(plan_id=plan_id)
    await callback.message.edit_text(
        "🎁 <b>کد تخفیف</b>\n\nلطفاً کد تخفیف خود را وارد کنید:"
    )
    await callback.answer()


@router.message(UserStates.enter_discount_code)
async def process_discount_code(message: Message, state: FSMContext, db_user: User):
    """Process entered discount code."""
    code = message.text.strip()
    data = await state.get_data()
    plan_id = data.get("plan_id")

    async with get_session() as session:
        stmt = select(DiscountCode).where(DiscountCode.code == code)
        result = await session.execute(stmt)
        discount = result.scalar_one_or_none()

        if not discount or not discount.is_valid:
            await message.answer("❌ کد تخفیف نامعتبر یا منقضی شده است.")
            await state.clear()
            return

        plan = await session.get(Plan, plan_id)
        if not plan:
            await message.answer("⚠️ خطا در پردازش.")
            await state.clear()
            return

        discount_amount = discount.calculate_discount(plan.final_price)
        final_price = plan.final_price - discount_amount

        await message.answer(
            f"✅ <b>کد تخفیف اعمال شد!</b>\n\n"
            f"📋 پلن: {plan.name}\n"
            f"💰 قیمت اصلی: {plan.final_price:,} تومان\n"
            f"🎁 تخفیف: {discount_amount:,} تومان\n"
            f"✅ قیمت نهایی: <b>{final_price:,}</b> تومان\n\n"
            f"برای خرید از منوی فروشگاه اقدام کنید.",
            reply_markup=UserKeyboards.plan_detail(plan_id),
        )

    await state.clear()


async def _create_subscription(callback: CallbackQuery, db_user: User, plan_id: int, order_id: int):
    """Create subscription on panel after successful payment."""
    from datetime import datetime, timezone, timedelta
    from core.database.models import Plan, Server, Subscription, SubscriptionStatus
    from core.services.panel.xui import XUIService
    from core.services.panel.hiddify import HiddifyService
    from core.database.models.server import PanelType

    async with get_session() as session:
        plan = await session.get(Plan, plan_id)
        if not plan:
            return

        # Get server
        server = None
        if plan.server_id:
            server = await session.get(Server, plan.server_id)
        else:
            # Get default server
            stmt = select(Server).where(Server.is_default == True).where(Server.is_active == True)
            result = await session.execute(stmt)
            server = result.scalar_one_or_none()

        if not server:
            await callback.message.answer("❌ خطا: سروری در دسترس نیست. با پشتیبانی تماس بگیرید.")
            return

        # Create client on panel
        email = f"user_{db_user.telegram_id}_{order_id}"

        if server.panel_type == PanelType.XUI:
            panel = XUIService(
                host=server.host,
                port=server.port,
                username=server.username,
                password=server.password,
                api_path=server.api_path,
            )
        else:
            panel = HiddifyService(
                host=server.host,
                port=server.port,
                username=server.username,
                password=server.password,
                hiddify_api_key=server.hiddify_api_key,
            )

        inbound_id = plan.inbound_id or 1
        client = await panel.add_client(
            inbound_id=inbound_id,
            email=email,
            data_limit_gb=plan.data_limit_gb,
            expire_days=plan.duration_days,
            ip_limit=plan.ip_limit,
        )

        if not client:
            await callback.message.answer("❌ خطا در ایجاد سرویس. با پشتیبانی تماس بگیرید.")
            return

        # Get subscription URL
        sub_url = await panel.get_subscription_url(client.client_id)

        # Save subscription
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            user_id=db_user.id,
            plan_id=plan_id,
            server_id=server.id,
            order_id=order_id,
            panel_client_id=client.client_id,
            panel_email=email,
            inbound_id=inbound_id,
            subscription_url=sub_url,
            data_limit_bytes=plan.data_limit_gb * 1024 * 1024 * 1024 if plan.data_limit_gb > 0 else 0,
            ip_limit=plan.ip_limit,
            start_date=now,
            expire_date=now + timedelta(days=plan.duration_days),
            status=SubscriptionStatus.ACTIVE,
        )
        session.add(subscription)

        # Update user stats
        db_user_stmt = select(User).where(User.id == db_user.id)
        user_result = await session.execute(db_user_stmt)
        user = user_result.scalar_one()
        user.total_purchases += 1
        user.total_spent += plan.final_price

    # Send success message
    success_text = (
        f"✅ <b>سرویس شما فعال شد!</b>\n\n"
        f"📋 پلن: {plan.name}\n"
        f"📊 حجم: {plan.display_data}\n"
        f"⏱️ مدت: {plan.display_duration}\n"
        f"🖥️ سرور: {server.flag} {server.name}\n\n"
    )

    if sub_url:
        success_text += f"🔗 <b>لینک اشتراک:</b>\n<code>{sub_url}</code>\n\n"

    success_text += "📱 لینک بالا را در اپلیکیشن V2Ray خود وارد کنید."

    await callback.message.answer(success_text)
