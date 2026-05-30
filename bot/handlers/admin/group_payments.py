"""Group payment approval/rejection/ban handlers."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from core.database.engine import get_session
from core.database.models import Payment, PaymentStatus, Order, OrderStatus, User

router = Router(name="group_payments")


@router.callback_query(F.data.startswith("gpay:approve:"))
async def group_approve_payment(callback: CallbackQuery):
    """Approve payment from group."""
    from bot.config import settings

    # Check if user is admin
    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("⛔ فقط ادمین‌ها می‌توانند تأیید کنند.", show_alert=True)
        return

    payment_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        payment = await session.get(Payment, payment_id)
        if not payment:
            await callback.answer("⚠️ پرداخت یافت نشد.", show_alert=True)
            return

        if payment.status != PaymentStatus.PENDING:
            await callback.answer("⚠️ این پرداخت قبلاً پردازش شده.", show_alert=True)
            return

        payment.status = PaymentStatus.COMPLETED
        payment.verified_by = callback.from_user.id

        if payment.order_id:
            order = await session.get(Order, payment.order_id)
            if order:
                order.status = OrderStatus.PAID

        user = await session.get(User, payment.user_id)

    # Update message
    admin_name = callback.from_user.full_name
    if callback.message.caption:
        await callback.message.edit_caption(
            caption=callback.message.caption + f"\n\n✅ <b>تأیید شد</b> توسط {admin_name}",
            reply_markup=None,
        )
    else:
        await callback.message.edit_text(
            callback.message.text + f"\n\n✅ <b>تأیید شد</b> توسط {admin_name}",
            reply_markup=None,
        )

    # Notify user
    if user:
        from bot.loader import bot

        try:
            await bot.send_message(
                user.telegram_id,
                f"✅ پرداخت شما به مبلغ {payment.amount:,} تومان تأیید شد.",
            )
        except Exception:
            pass

    await callback.answer("✅ تأیید شد")


@router.callback_query(F.data.startswith("gpay:reject:"))
async def group_reject_payment(callback: CallbackQuery):
    """Reject payment from group."""
    from bot.config import settings

    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("⛔ فقط ادمین‌ها.", show_alert=True)
        return

    payment_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        payment = await session.get(Payment, payment_id)
        if not payment:
            await callback.answer("⚠️ یافت نشد.", show_alert=True)
            return

        if payment.status != PaymentStatus.PENDING:
            await callback.answer("⚠️ قبلاً پردازش شده.", show_alert=True)
            return

        payment.status = PaymentStatus.FAILED
        payment.verified_by = callback.from_user.id

        if payment.order_id:
            order = await session.get(Order, payment.order_id)
            if order:
                order.status = OrderStatus.CANCELLED

        user = await session.get(User, payment.user_id)

    admin_name = callback.from_user.full_name
    if callback.message.caption:
        await callback.message.edit_caption(
            caption=callback.message.caption + f"\n\n❌ <b>رد شد</b> توسط {admin_name}",
            reply_markup=None,
        )
    else:
        await callback.message.edit_text(
            callback.message.text + f"\n\n❌ <b>رد شد</b> توسط {admin_name}",
            reply_markup=None,
        )

    if user:
        from bot.loader import bot

        try:
            await bot.send_message(
                user.telegram_id,
                f"❌ پرداخت {payment.amount:,} تومان رد شد.",
            )
        except Exception:
            pass

    await callback.answer("❌ رد شد")


@router.callback_query(F.data.startswith("gpay:ban:"))
async def group_reject_and_ban(callback: CallbackQuery):
    """Reject payment and ban user."""
    from bot.config import settings

    if callback.from_user.id not in settings.admin_ids_list:
        await callback.answer("⛔ فقط ادمین‌ها.", show_alert=True)
        return

    payment_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        payment = await session.get(Payment, payment_id)
        if not payment:
            await callback.answer("⚠️ یافت نشد.", show_alert=True)
            return

        if payment.status != PaymentStatus.PENDING:
            await callback.answer("⚠️ قبلاً پردازش شده.", show_alert=True)
            return

        payment.status = PaymentStatus.FAILED
        payment.verified_by = callback.from_user.id

        if payment.order_id:
            order = await session.get(Order, payment.order_id)
            if order:
                order.status = OrderStatus.CANCELLED

        # Ban user
        user = await session.get(User, payment.user_id)
        if user:
            user.is_banned = True
            user.ban_reason = "فیش جعلی/تکراری"

    admin_name = callback.from_user.full_name
    if callback.message.caption:
        await callback.message.edit_caption(
            caption=callback.message.caption + f"\n\n🚫 <b>رد + بن شد</b> توسط {admin_name}",
            reply_markup=None,
        )
    else:
        await callback.message.edit_text(
            callback.message.text + f"\n\n🚫 <b>رد + بن شد</b> توسط {admin_name}",
            reply_markup=None,
        )

    if user:
        from bot.loader import bot

        try:
            await bot.send_message(
                user.telegram_id,
                "🚫 حساب شما به دلیل ارسال فیش جعلی/تکراری مسدود شد.",
            )
        except Exception:
            pass

    await callback.answer("🚫 رد و بن شد")
