"""User services (subscriptions) handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.keyboards.user_kb import UserKeyboards
from bot.states.user_states import UserStates
from bot.utils.qrcode import generate_qr_code
from core.database.engine import get_session
from core.database.models import User, Subscription, SubscriptionStatus

router = Router(name="services")


@router.message(F.text == "📦 سرویس‌های من")
async def show_services(message: Message, db_user: User, state: FSMContext):
    """Show user's subscriptions."""
    await state.clear()
    async with get_session() as session:
        stmt = (
            select(Subscription)
            .where(Subscription.user_id == db_user.id)
            .options(selectinload(Subscription.plan))
            .order_by(Subscription.id.desc())
        )
        result = await session.execute(stmt)
        subscriptions = result.scalars().all()

    if not subscriptions:
        await message.answer(
            "📦 <b>سرویس‌های من</b>\n\n"
            "شما هنوز سرویسی خریداری نکرده‌اید.\n"
            "از بخش «خرید سرویس» اقدام کنید.",
            reply_markup=UserKeyboards.subscription_list([]),
        )
        return

    await message.answer(
        "📦 <b>سرویس‌های من</b>\n\nسرویس مورد نظر را انتخاب کنید:",
        reply_markup=UserKeyboards.subscription_list(subscriptions),
    )


@router.callback_query(F.data == "sub:list")
async def show_services_callback(callback: CallbackQuery, db_user: User):
    """Show services via callback."""
    async with get_session() as session:
        stmt = (
            select(Subscription)
            .where(Subscription.user_id == db_user.id)
            .options(selectinload(Subscription.plan))
            .order_by(Subscription.id.desc())
        )
        result = await session.execute(stmt)
        subscriptions = result.scalars().all()

    await callback.message.edit_text(
        "📦 <b>سرویس‌های من</b>\n\nسرویس مورد نظر را انتخاب کنید:",
        reply_markup=UserKeyboards.subscription_list(subscriptions),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sub:detail:"))
async def show_subscription_detail(callback: CallbackQuery, db_user: User):
    """Show subscription details."""
    sub_id = int(callback.data.split(":")[2])

    async with get_session() as session:
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

    # Status icon
    status_map = {
        SubscriptionStatus.ACTIVE: "✅ فعال",
        SubscriptionStatus.EXPIRED: "⏰ منقضی",
        SubscriptionStatus.DISABLED: "🚫 غیرفعال",
        SubscriptionStatus.TRAFFIC_ENDED: "📊 اتمام ترافیک",
        SubscriptionStatus.PENDING: "⏳ در انتظار",
    }

    plan_name = sub.plan.name if sub.plan else "تست رایگان"

    # Traffic bar
    traffic_bar = _create_progress_bar(sub.traffic_percent)

    detail_text = (
        f"📋 <b>جزئیات سرویس</b>\n\n"
        f"📦 پلن: {plan_name}\n"
        f"🖥️ سرور: {sub.server.flag + ' ' + sub.server.name if sub.server else 'نامشخص'}\n"
        f"📊 وضعیت: {status_map.get(sub.status, sub.status.value)}\n\n"
        f"📈 <b>مصرف ترافیک:</b>\n"
        f"{traffic_bar}\n"
        f"📥 مصرف شده: {sub.used_traffic_gb} GB\n"
        f"📊 کل: {sub.data_limit_gb if sub.data_limit_gb > 0 else '♾️'} GB\n"
        f"📤 باقیمانده: {sub.remaining_traffic_gb if sub.data_limit_bytes > 0 else '♾️'} GB\n\n"
        f"📅 شروع: {sub.start_date.strftime('%Y/%m/%d')}\n"
        f"📅 انقضا: {sub.expire_date.strftime('%Y/%m/%d')}\n"
        f"⏱️ باقیمانده: {sub.remaining_days} روز\n"
    )

    await callback.message.edit_text(
        detail_text,
        reply_markup=UserKeyboards.subscription_detail(sub_id, sub.is_active),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sub:config:"))
async def show_config_link(callback: CallbackQuery, db_user: User):
    """Show subscription/config link."""
    sub_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        stmt = (
            select(Subscription)
            .where(Subscription.id == sub_id)
            .where(Subscription.user_id == db_user.id)
        )
        result = await session.execute(stmt)
        sub = result.scalar_one_or_none()

    if not sub:
        await callback.answer("⚠️ سرویس یافت نشد.", show_alert=True)
        return

    if sub.subscription_url:
        await callback.message.answer(
            f"🔗 <b>لینک اشتراک (Subscription):</b>\n\n"
            f"<code>{sub.subscription_url}</code>\n\n"
            f"📱 این لینک را در اپلیکیشن V2Ray خود وارد کنید.\n"
            f"(v2rayNG, Streisand, Hiddify, ...)"
        )
    else:
        await callback.message.answer("⚠️ لینک اشتراک موجود نیست.")

    await callback.answer()


@router.callback_query(F.data.startswith("sub:qrcode:"))
async def show_qrcode(callback: CallbackQuery, db_user: User):
    """Generate and send QR code for subscription."""
    sub_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        stmt = (
            select(Subscription)
            .where(Subscription.id == sub_id)
            .where(Subscription.user_id == db_user.id)
        )
        result = await session.execute(stmt)
        sub = result.scalar_one_or_none()

    if not sub or not sub.subscription_url:
        await callback.answer("⚠️ لینک اشتراک موجود نیست.", show_alert=True)
        return

    # Generate QR code
    qr_buffer = generate_qr_code(sub.subscription_url)

    from aiogram.types import BufferedInputFile

    photo = BufferedInputFile(qr_buffer.getvalue(), filename="qrcode.png")
    await callback.message.answer_photo(
        photo,
        caption="📱 QR Code سرویس شما\n\nبا اپلیکیشن V2Ray اسکن کنید.",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sub:upgrade:"))
async def upgrade_subscription(callback: CallbackQuery, db_user: User):
    """Show upgrade options for a subscription."""
    sub_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        from sqlalchemy.orm import selectinload
        sub = await session.get(Subscription, sub_id)
        if not sub or sub.user_id != db_user.id:
            await callback.answer("⚠️ سرویس یافت نشد.", show_alert=True)
            return

        # Get plans with more data or longer duration
        from core.database.models import Plan
        stmt = (
            select(Plan)
            .where(Plan.is_active == True)
            .where(
                (Plan.data_limit_gb > (sub.data_limit_bytes // (1024**3))) |
                (Plan.duration_days > sub.remaining_days)
            )
            .order_by(Plan.price)
            .limit(5)
        )
        result = await session.execute(stmt)
        upgrade_plans = result.scalars().all()

    if not upgrade_plans:
        await callback.answer("⚠️ پلن ارتقایی موجود نیست.", show_alert=True)
        return

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    text = "⬆️ <b>ارتقای سرویس</b>\n\nپلن جدید را انتخاب کنید:\n\n"

    for plan in upgrade_plans:
        text += f"📋 {plan.name} | {plan.display_data} | {plan.display_duration} | {plan.final_price:,}ت\n"
        builder.row(InlineKeyboardButton(
            text=f"{plan.name} - {plan.final_price:,}ت",
            callback_data=f"pay:wallet:{plan.id}",
        ))

    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"sub:detail:{sub_id}"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("sub:traffic:"))
async def refresh_traffic(callback: CallbackQuery, db_user: User):
    """Refresh traffic info from panel."""
    sub_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        stmt = (
            select(Subscription)
            .where(Subscription.id == sub_id)
            .where(Subscription.user_id == db_user.id)
            .options(selectinload(Subscription.server))
        )
        result = await session.execute(stmt)
        sub = result.scalar_one_or_none()

        if not sub:
            await callback.answer("⚠️ سرویس یافت نشد.", show_alert=True)
            return

        # Sync from panel
        from core.services.panel.xui import XUIService
        from core.services.panel.hiddify import HiddifyService
        from core.database.models.server import PanelType

        server = sub.server
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

        traffic = await panel.get_client_traffic(sub.panel_email)
        if traffic:
            sub.used_traffic_bytes = traffic["used"]

    await callback.answer("✅ اطلاعات ترافیک بروزرسانی شد.")

    # Re-show detail
    await show_subscription_detail(callback, db_user)


def _create_progress_bar(percent: int, length: int = 10) -> str:
    """Create a text progress bar."""
    filled = int(length * percent / 100)
    empty = length - filled
    bar = "█" * filled + "░" * empty
    return f"[{bar}] {percent}%"


@router.callback_query(F.data.startswith("sub:rebuy:"))
async def rebuy_subscription(callback: CallbackQuery, db_user: User):
    """Rebuy an expired subscription's plan."""
    sub_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        sub = await session.get(Subscription, sub_id)
        if not sub or not sub.plan_id:
            await callback.answer("⚠️ پلن مرتبط یافت نشد.", show_alert=True)
            return
        plan_id = sub.plan_id

    # Redirect to plan detail
    from bot.keyboards.user_kb import UserKeyboards
    from core.database.models import Plan

    async with get_session() as session:
        plan = await session.get(Plan, plan_id)

    if not plan:
        await callback.answer("⚠️ پلن دیگر موجود نیست.", show_alert=True)
        return

    await callback.message.edit_text(
        f"🔄 <b>خرید مجدد</b>\n\n"
        f"📋 پلن: {plan.name}\n"
        f"📊 حجم: {plan.display_data}\n"
        f"⏱️ مدت: {plan.display_duration}\n"
        f"💰 قیمت: {plan.final_price:,} تومان",
        reply_markup=UserKeyboards.plan_detail(plan_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("sub:transfer:"))
async def transfer_subscription_start(callback: CallbackQuery, state: FSMContext, db_user: User):
    """Start subscription transfer."""
    sub_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        sub = await session.get(Subscription, sub_id)
        if not sub or sub.user_id != db_user.id or not sub.is_active:
            await callback.answer("⚠️ امکان انتقال وجود ندارد.", show_alert=True)
            return

    await state.update_data(transfer_sub_id=sub_id)
    await state.set_state(UserStates.transfer_target)
    await callback.message.edit_text(
        "🔄 <b>انتقال سرویس</b>\n\n"
        "شناسه تلگرام (عددی) شخص مقصد را وارد کنید:"
    )
    await callback.answer()
