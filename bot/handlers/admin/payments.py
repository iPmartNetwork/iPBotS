"""Admin payment management handlers - complete rewrite."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_kb import AdminKeyboards
from core.database.engine import get_session
from core.database.models import Payment, PaymentStatus, Order, OrderStatus, User, Subscription, SubscriptionStatus

router = Router(name="admin_payments")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(F.text == "💳 پرداخت‌ها")
async def payments_menu(message: Message, state: FSMContext):
    """Show pending payments."""
    await state.clear()

    async with get_session() as session:
        stmt = (
            select(Payment)
            .where(Payment.status == PaymentStatus.PENDING)
            .order_by(Payment.id.desc())
            .limit(20)
        )
        result = await session.execute(stmt)
        payments = result.scalars().all()

    if not payments:
        await message.answer("✅ پرداخت معلقی وجود ندارد.")
        return

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()

    text = f"💳 <b>پرداخت‌های معلق</b> ({len(payments)})\n\n"

    for pay in payments[:10]:
        text += f"🔹 #{pay.id} | {pay.amount:,}ت | {pay.method.value}\n"
        builder.row(
            InlineKeyboardButton(
                text=f"#{pay.id} - {pay.amount:,}ت ({pay.method.value})",
                callback_data=f"admin:pay:view:{pay.id}",
            )
        )

    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("admin:pay:view:"))
async def view_payment(callback: CallbackQuery):
    """View payment details."""
    payment_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        payment = await session.get(Payment, payment_id)
        if not payment:
            await callback.answer("⚠️ یافت نشد.", show_alert=True)
            return
        user = await session.get(User, payment.user_id)

    text = (
        f"💳 <b>پرداخت #{payment.id}</b>\n\n"
        f"👤 کاربر: {user.full_name if user else '?'} (<code>{user.telegram_id if user else '?'}</code>)\n"
        f"💰 مبلغ: {payment.amount:,} تومان\n"
        f"📋 روش: {payment.method.value}\n"
        f"📊 وضعیت: {payment.status.value}\n"
        f"📅 تاریخ: {payment.created_at.strftime('%Y/%m/%d %H:%M')}\n"
    )

    await callback.message.edit_text(text, reply_markup=AdminKeyboards.payment_pending(payment_id))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:pay:approve:"))
async def approve_payment(callback: CallbackQuery):
    """Approve a pending payment."""
    payment_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        payment = await session.get(Payment, payment_id)
        if not payment:
            await callback.answer("⚠️ یافت نشد.", show_alert=True)
            return

        payment.status = PaymentStatus.COMPLETED
        payment.verified_by = callback.from_user.id

        order = None
        if payment.order_id:
            order = await session.get(Order, payment.order_id)
            if order:
                order.status = OrderStatus.PAID

        user = await session.get(User, payment.user_id)

    await callback.message.edit_text(f"✅ پرداخت #{payment_id} تأیید شد. ({payment.amount:,}ت)")

    if user:
        from bot.loader import bot
        try:
            await bot.send_message(user.telegram_id, f"✅ پرداخت {payment.amount:,} تومان تأیید شد.")
        except Exception:
            pass

        # Auto-create subscription for plan purchases
        if order and order.plan_id and user:
            try:
                await bot.send_message(
                    user.telegram_id,
                    "🔄 سرویس شما در حال فعال‌سازی است..."
                )

                from datetime import datetime, timezone, timedelta
                from core.database.models import Plan, Server, Subscription, SubscriptionStatus
                from core.services.panel.xui import XUIService
                from core.services.panel.hiddify import HiddifyService
                from core.services.panel.marzban import MarzbanService
                from core.database.models.server import PanelType

                async with get_session() as session2:
                    plan = await session2.get(Plan, order.plan_id)
                    if plan:
                        # Get server
                        server = None
                        if plan.server_id:
                            server = await session2.get(Server, plan.server_id)
                        else:
                            from sqlalchemy import select as sel2
                            srv_stmt = sel2(Server).where(Server.is_default == True, Server.is_active == True)
                            srv_result = await session2.execute(srv_stmt)
                            server = srv_result.scalar_one_or_none()

                        if server:
                            email = f"user_{user.telegram_id}_{order.id}"
                            if server.panel_type == PanelType.XUI:
                                panel_svc = XUIService(host=server.host, port=server.port, username=server.username, password=server.password, api_path=server.api_path)
                            elif server.panel_type == PanelType.MARZBAN:
                                panel_svc = MarzbanService(host=server.host, port=server.port, username=server.username, password=server.password)
                            else:
                                panel_svc = HiddifyService(host=server.host, port=server.port, username=server.username, password=server.password, hiddify_api_key=server.hiddify_api_key)

                            client = await panel_svc.add_client(
                                inbound_id=plan.inbound_id or 1,
                                email=email,
                                data_limit_gb=plan.data_limit_gb,
                                expire_days=plan.duration_days,
                                ip_limit=plan.ip_limit,
                            )

                            if client:
                                sub_url = await panel_svc.get_subscription_url(client.client_id)
                                now = datetime.now(timezone.utc)
                                subscription = Subscription(
                                    user_id=user.id,
                                    plan_id=plan.id,
                                    server_id=server.id,
                                    order_id=order.id,
                                    panel_client_id=client.client_id,
                                    panel_email=email,
                                    inbound_id=plan.inbound_id or 1,
                                    subscription_url=sub_url,
                                    data_limit_bytes=plan.data_limit_gb * 1024**3 if plan.data_limit_gb > 0 else 0,
                                    ip_limit=plan.ip_limit,
                                    start_date=now,
                                    expire_date=now + timedelta(days=plan.duration_days),
                                    status=SubscriptionStatus.ACTIVE,
                                )
                                session2.add(subscription)

                                # Update order status
                                order_obj = await session2.get(Order, order.id)
                                if order_obj:
                                    order_obj.status = OrderStatus.COMPLETED

                                await bot.send_message(
                                    user.telegram_id,
                                    f"✅ <b>سرویس فعال شد!</b>\n\n"
                                    f"📋 پلن: {plan.name}\n"
                                    f"🔗 لینک:\n<code>{sub_url}</code>"
                                )
            except Exception as e:
                from loguru import logger
                logger.error(f"Auto-create subscription failed: {e}")

    await callback.answer("✅ تأیید شد")


@router.callback_query(F.data.startswith("admin:pay:reject:"))
async def reject_payment(callback: CallbackQuery):
    """Reject a pending payment."""
    payment_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        payment = await session.get(Payment, payment_id)
        if not payment:
            await callback.answer("⚠️ یافت نشد.", show_alert=True)
            return

        payment.status = PaymentStatus.FAILED
        payment.verified_by = callback.from_user.id

        if payment.order_id:
            order = await session.get(Order, payment.order_id)
            if order:
                order.status = OrderStatus.CANCELLED

        user = await session.get(User, payment.user_id)

    await callback.message.edit_text(f"❌ پرداخت #{payment_id} رد شد.")

    if user:
        from bot.loader import bot
        try:
            await bot.send_message(user.telegram_id, f"❌ پرداخت {payment.amount:,} تومان رد شد.")
        except Exception:
            pass

    await callback.answer("❌ رد شد")
