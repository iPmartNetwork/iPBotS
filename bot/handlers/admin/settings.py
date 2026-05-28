"""Admin settings and backup handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_kb import AdminKeyboards

router = Router(name="admin_settings")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(F.text == "⚙️ تنظیمات")
async def settings_menu(message: Message):
    """Show settings menu."""
    await message.answer(
        "⚙️ <b>تنظیمات</b>",
        reply_markup=AdminKeyboards.settings_menu(),
    )


@router.message(F.text == "🎁 تخفیف‌ها")
async def discounts_menu(message: Message):
    """Show discounts menu."""
    await message.answer(
        "🎁 <b>مدیریت تخفیف‌ها و کدهای هدیه</b>",
        reply_markup=AdminKeyboards.discount_management(),
    )


@router.message(F.text == "🎫 تیکت‌ها")
async def tickets_menu(message: Message):
    """Show open tickets for admin."""
    from sqlalchemy import select
    from core.database.engine import get_session
    from core.database.models import Ticket, TicketStatus, User
    from sqlalchemy.orm import selectinload

    async with get_session() as session:
        stmt = (
            select(Ticket)
            .where(Ticket.status.in_([TicketStatus.OPEN, TicketStatus.WAITING]))
            .options(selectinload(Ticket.user))
            .order_by(Ticket.id.desc())
            .limit(20)
        )
        result = await session.execute(stmt)
        tickets = result.scalars().all()

    if not tickets:
        await message.answer("✅ تیکت باز وجود ندارد.")
        return

    text = "🎫 <b>تیکت‌های باز</b>\n\n"

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()

    for ticket in tickets:
        status_icon = "🟡" if ticket.status == TicketStatus.OPEN else "🟠"
        text += (
            f"{status_icon} #{ticket.id} | {ticket.subject[:25]} | "
            f"{ticket.user.full_name if ticket.user else 'نامشخص'}\n"
        )
        builder.row(
            InlineKeyboardButton(
                text=f"#{ticket.id} - {ticket.subject[:20]}",
                callback_data=f"admin:ticket:view:{ticket.id}",
            )
        )

    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("admin:ticket:view:"))
async def admin_view_ticket(callback: CallbackQuery):
    """Admin view ticket."""
    ticket_id = int(callback.data.split(":")[3])

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from core.database.engine import get_session
    from core.database.models import Ticket

    async with get_session() as session:
        stmt = (
            select(Ticket)
            .where(Ticket.id == ticket_id)
            .options(selectinload(Ticket.messages), selectinload(Ticket.user))
        )
        result = await session.execute(stmt)
        ticket = result.scalar_one_or_none()

    if not ticket:
        await callback.answer("⚠️ تیکت یافت نشد.", show_alert=True)
        return

    text = (
        f"🎫 <b>تیکت #{ticket.id}</b>\n"
        f"👤 کاربر: {ticket.user.full_name if ticket.user else 'نامشخص'}\n"
        f"📌 موضوع: {ticket.subject}\n\n"
    )

    for msg in ticket.messages[-5:]:
        sender = "👤 کاربر" if not msg.is_admin else "🛡️ ادمین"
        text += f"{sender}:\n{msg.message}\n\n"

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="💬 پاسخ", callback_data=f"admin:ticket:reply:{ticket_id}"
        ),
        InlineKeyboardButton(
            text="🔒 بستن", callback_data=f"admin:ticket:close:{ticket_id}"
        ),
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:ticket:reply:"))
async def admin_reply_ticket(callback: CallbackQuery):
    """Start admin reply to ticket."""
    from aiogram.fsm.context import FSMContext
    from bot.states import AdminStates

    ticket_id = int(callback.data.split(":")[3])

    # We need state from the handler context
    # This is a simplified version - in production use state properly
    await callback.message.edit_text(
        f"💬 پاسخ خود را برای تیکت #{ticket_id} بنویسید:\n\n"
        f"(فرمت: /reply_{ticket_id} متن پاسخ)"
    )
    await callback.answer()


@router.message(F.text.startswith("/reply_"))
async def process_admin_reply(message: Message):
    """Process admin ticket reply."""
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
        await message.answer("❌ فرمت صحیح: /reply_ID متن پاسخ")
        return

    try:
        ticket_id = int(parts[0].replace("/reply_", ""))
    except ValueError:
        await message.answer("❌ شناسه تیکت نامعتبر.")
        return

    reply_text = parts[1]

    from core.database.engine import get_session
    from core.database.models import Ticket, TicketMessage, TicketStatus, User
    from sqlalchemy import select

    async with get_session() as session:
        ticket = await session.get(Ticket, ticket_id)
        if not ticket:
            await message.answer("❌ تیکت یافت نشد.")
            return

        # Add admin reply
        ticket_msg = TicketMessage(
            ticket_id=ticket_id,
            sender_id=message.from_user.id,
            is_admin=True,
            message=reply_text,
        )
        session.add(ticket_msg)
        ticket.status = TicketStatus.ANSWERED

        # Get user
        user = await session.get(User, ticket.user_id)

    await message.answer(f"✅ پاسخ به تیکت #{ticket_id} ارسال شد.")

    # Notify user
    if user:
        from bot.loader import bot
        from core.services.notification import NotificationService

        notifier = NotificationService(bot)
        await notifier.notify_ticket_reply(user.telegram_id, ticket_id)


@router.message(F.text == "🗄️ پشتیبان‌گیری")
async def manual_backup(message: Message):
    """Trigger manual backup."""
    await message.answer("🔄 در حال ایجاد پشتیبان...")

    from core.scheduler.jobs import auto_backup

    try:
        await auto_backup()
        await message.answer("✅ پشتیبان‌گیری با موفقیت انجام شد.")
    except Exception as e:
        await message.answer(f"❌ خطا در پشتیبان‌گیری: {e}")
