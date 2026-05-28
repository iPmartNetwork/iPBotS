"""Admin payment management handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_kb import AdminKeyboards
from core.database.engine import get_session
from core.database.models import Payment, PaymentStatus, PaymentMethod, Order, OrderStatus, User

router = Router(name="admin_payments")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(F.text == "💳 پرداخت‌ها")
async def payments_menu(message: Message):
    """Show pending payments."""
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

    text = "💳 <b>پرداخت‌های معلق</b>\n\n"
    for pay in payments:
        text += (
            f"🔹 #{pay.id} | {pay.amount:,} تومان | "
            f"{pay.method.value} | کاربر: {pay.user_id}\n"
        )

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    for pay in payments[:10]:
        builder.row(
            InlineKeyboardButton(
                text=f"#{pay.id} - {pay.amount:,} تومان",
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
            await callback.answer("⚠️ پرداخت یافت نشد.", show_alert=True)
            return

        user = await session.get(User, payment.user_id)

    text = (
        f"💳 <b>جزئیات پرداخت #{payment.id}</b>\n\n"
        f"👤 کاربر: {user.full_name if user else 'نامشخص'} ({payment.user_id})\n"
        f"💰 مبلغ: {payment.amount:,} تومان\n"
        f"📋 روش: {payment.method.value}\n"
        f"📊 وضعیت: {payment.status.value}\n"
        f"📅 تاریخ: {payment.created_at.strftime('%Y/%m/%d %H:%M')}\n"
    )

    if payment.card_sender_name:
        text += f"👤 نام واریزکننده: {payment.card_sender_name}\n"

    await callback.message.edit_text(
        text, reply_markup=AdminKeyboards.payment_pending(payment_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:pay:approve:"))
async def approve_payment(callback: CallbackQuery):
    """Approve a pending payment."""
    payment_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        payment = await session.get(Payment, payment_id)
        if not payment:
            await callback.answer("⚠️ پرداخت یافت نشد.", show_alert=True)
            return

        payment.status = PaymentStatus.COMPLETED
        payment.verified_by = callback.from_user.id

        # Update order if exists
        if payment.order_id:
            order = await session.get(Order, payment.order_id)
            if order:
                order.status = OrderStatus.PAID

        user = await session.get(User, payment.user_id)

    await callback.message.edit_text(
        f"✅ پرداخت #{payment_id} تأیید شد.\n"
        f"مبلغ: {payment.amount:,} تومان"
    )

    # Notify user
    if user:
        from bot.loader import bot

        try:
            await bot.send_message(
                user.telegram_id,
                f"✅ پرداخت شما به مبلغ {payment.amount:,} تومان تأیید شد.\n"
                f"سرویس شما به زودی فعال می‌شود.",
            )
        except Exception:
            pass

    await callback.answer("✅ تأیید شد")


@router.callback_query(F.data.startswith("admin:pay:reject:"))
async def reject_payment(callback: CallbackQuery):
    """Reject a pending payment."""
    payment_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        payment = await session.get(Payment, payment_id)
        if not payment:
            await callback.answer("⚠️ پرداخت یافت نشد.", show_alert=True)
            return

        payment.status = PaymentStatus.FAILED
        payment.verified_by = callback.from_user.id

        if payment.order_id:
            order = await session.get(Order, payment.order_id)
            if order:
                order.status = OrderStatus.CANCELLED

        user = await session.get(User, payment.user_id)

    await callback.message.edit_text(f"❌ پرداخت #{payment_id} رد شد.")

    # Notify user
    if user:
        from bot.loader import bot

        try:
            await bot.send_message(
                user.telegram_id,
                f"❌ پرداخت شما به مبلغ {payment.amount:,} تومان رد شد.\n"
                f"در صورت مشکل با پشتیبانی تماس بگیرید.",
            )
        except Exception:
            pass

    await callback.answer("❌ رد شد")
