"""Reseller (agency) system handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from bot.keyboards.user_kb import UserKeyboards
from core.database.engine import get_session
from core.database.models import User, Plan
from core.database.models.reseller import Reseller, ResellerLevel, ResellerTransaction

router = Router(name="reseller")


class ResellerStates(StatesGroup):
    """Reseller FSM states."""

    apply_shop_name = State()
    buy_for_client = State()
    client_telegram_id = State()


@router.callback_query(F.data == "reseller:panel")
async def reseller_panel(callback: CallbackQuery, db_user: User):
    """Show reseller panel."""
    async with get_session() as session:
        stmt = select(Reseller).where(Reseller.user_id == db_user.id)
        result = await session.execute(stmt)
        reseller = result.scalar_one_or_none()

    if not reseller:
        # Show apply option
        from aiogram.types import InlineKeyboardButton
        from aiogram.utils.keyboard import InlineKeyboardBuilder

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="📝 درخواست نمایندگی", callback_data="reseller:apply"
            )
        )
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="main:menu")
        )

        await callback.message.edit_text(
            "🏪 <b>سیستم نمایندگی</b>\n\n"
            "شما هنوز نماینده نیستید.\n"
            "با ثبت درخواست نمایندگی، می‌توانید با تخفیف ویژه سرویس بخرید "
            "و به مشتریان خود بفروشید.\n\n"
            "✅ مزایای نمایندگی:\n"
            "• تخفیف ویژه روی تمام پلن‌ها\n"
            "• پنل مدیریت مشتریان\n"
            "• پشتیبانی اختصاصی\n"
            "• امکان قیمت‌گذاری سفارشی",
            reply_markup=builder.as_markup(),
        )
        await callback.answer()
        return

    if not reseller.is_active:
        await callback.answer("⚠️ حساب نمایندگی شما غیرفعال است.", show_alert=True)
        return

    # Load level info
    async with get_session() as session:
        level = await session.get(ResellerLevel, reseller.level_id)

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🛒 خرید برای مشتری", callback_data="reseller:buy"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="👥 مشتریان من", callback_data="reseller:clients"
        ),
        InlineKeyboardButton(
            text="💰 مالی", callback_data="reseller:finance"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="📊 گزارش فروش", callback_data="reseller:report"
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="💳 شارژ حساب", callback_data="reseller:charge"
        ),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="main:menu"),
    )

    text = (
        f"🏪 <b>پنل نمایندگی</b>\n\n"
        f"🏷️ فروشگاه: {reseller.shop_name}\n"
        f"⭐ سطح: {level.name if level else 'نامشخص'}\n"
        f"🏷️ تخفیف: {level.discount_percent if level else 0}%\n\n"
        f"💰 موجودی: {reseller.balance:,} تومان\n"
        f"📊 کل فروش: {reseller.total_sales}\n"
        f"💵 درآمد کل: {reseller.total_revenue:,} تومان\n"
        f"👥 مشتریان: {reseller.total_clients}"
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "reseller:apply")
async def apply_reseller(callback: CallbackQuery, state: FSMContext):
    """Start reseller application."""
    await callback.message.edit_text(
        "📝 <b>درخواست نمایندگی</b>\n\n"
        "نام فروشگاه خود را وارد کنید:"
    )
    await state.set_state(ResellerStates.apply_shop_name)
    await callback.answer()


@router.message(ResellerStates.apply_shop_name)
async def process_reseller_apply(message: Message, state: FSMContext, db_user: User):
    """Process reseller application."""
    shop_name = message.text.strip()

    if len(shop_name) < 3:
        await message.answer("❌ نام فروشگاه باید حداقل 3 کاراکتر باشد.")
        return

    async with get_session() as session:
        # Get default level
        level_stmt = (
            select(ResellerLevel)
            .where(ResellerLevel.is_active == True)
            .order_by(ResellerLevel.sort_order)
        )
        level_result = await session.execute(level_stmt)
        default_level = level_result.scalars().first()

        if not default_level:
            await message.answer("⚠️ سیستم نمایندگی در حال حاضر غیرفعال است.")
            await state.clear()
            return

        # Create reseller
        reseller = Reseller(
            user_id=db_user.id,
            level_id=default_level.id,
            shop_name=shop_name,
            is_active=False,  # Needs admin approval
            is_verified=False,
        )
        session.add(reseller)

    await message.answer(
        f"✅ <b>درخواست نمایندگی ثبت شد</b>\n\n"
        f"🏪 نام فروشگاه: {shop_name}\n\n"
        f"⏳ درخواست شما پس از بررسی توسط مدیریت تأیید خواهد شد."
    )

    # Notify admins
    from bot.loader import bot
    from core.services.notification import NotificationService

    notifier = NotificationService(bot)
    await notifier.notify_admins(
        f"🏪 <b>درخواست نمایندگی جدید</b>\n\n"
        f"👤 کاربر: {db_user.mention}\n"
        f"🏷️ فروشگاه: {shop_name}\n"
        f"🆔 شناسه: {db_user.telegram_id}"
    )

    await state.clear()


@router.callback_query(F.data == "reseller:buy")
async def reseller_buy(callback: CallbackQuery, db_user: User):
    """Show plans with reseller discount."""
    async with get_session() as session:
        reseller_stmt = select(Reseller).where(Reseller.user_id == db_user.id)
        reseller_result = await session.execute(reseller_stmt)
        reseller = reseller_result.scalar_one_or_none()

        if not reseller:
            await callback.answer("⚠️ خطا.", show_alert=True)
            return

        level = await session.get(ResellerLevel, reseller.level_id)
        discount = level.discount_percent if level else 0

        plans_stmt = select(Plan).where(Plan.is_active == True).order_by(Plan.sort_order)
        plans_result = await session.execute(plans_stmt)
        plans = plans_result.scalars().all()

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()

    text = f"🛒 <b>خرید نمایندگی</b> (تخفیف {discount}%)\n\n"

    for plan in plans:
        reseller_price = int(plan.final_price * (100 - discount) / 100)
        text += f"📋 {plan.name} | {plan.display_data} | <b>{reseller_price:,}</b> تومان\n"
        builder.row(
            InlineKeyboardButton(
                text=f"{plan.name} - {reseller_price:,} ت",
                callback_data=f"reseller:plan:{plan.id}",
            )
        )

    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="reseller:panel")
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "reseller:finance")
async def reseller_finance(callback: CallbackQuery, db_user: User):
    """Show reseller financial info."""
    async with get_session() as session:
        reseller_stmt = select(Reseller).where(Reseller.user_id == db_user.id)
        reseller_result = await session.execute(reseller_stmt)
        reseller = reseller_result.scalar_one_or_none()

        if not reseller:
            await callback.answer("⚠️ خطا.", show_alert=True)
            return

        # Get recent transactions
        tx_stmt = (
            select(ResellerTransaction)
            .where(ResellerTransaction.reseller_id == reseller.id)
            .order_by(ResellerTransaction.id.desc())
            .limit(10)
        )
        tx_result = await session.execute(tx_stmt)
        transactions = tx_result.scalars().all()

    text = (
        f"💰 <b>اطلاعات مالی نمایندگی</b>\n\n"
        f"💵 موجودی: {reseller.balance:,} تومان\n"
        f"📊 کل فروش: {reseller.total_sales}\n"
        f"💰 درآمد کل: {reseller.total_revenue:,} تومان\n\n"
        f"📜 <b>آخرین تراکنش‌ها:</b>\n\n"
    )

    for tx in transactions:
        icon = "📥" if tx.amount > 0 else "📤"
        text += f"{icon} {abs(tx.amount):,} | {tx.description or tx.transaction_type}\n"

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="reseller:panel")
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
