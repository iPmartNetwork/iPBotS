"""Support and ticket handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.keyboards.user_kb import UserKeyboards
from bot.states import UserStates
from core.database.engine import get_session
from core.database.models import User, Ticket, TicketMessage, TicketStatus

router = Router(name="support")


@router.message(F.text == "📞 پشتیبانی")
async def show_support(message: Message):
    """Show support menu."""
    await message.answer(
        "📞 <b>پشتیبانی</b>\n\n"
        "از طریق سیستم تیکت می‌توانید سوالات و مشکلات خود را مطرح کنید.",
        reply_markup=UserKeyboards.support_menu(),
    )


@router.callback_query(F.data == "ticket:new")
async def new_ticket(callback: CallbackQuery, state: FSMContext):
    """Start new ticket flow."""
    await callback.message.edit_text(
        "📝 <b>تیکت جدید</b>\n\n"
        "لطفاً موضوع تیکت خود را وارد کنید:"
    )
    await state.set_state(UserStates.ticket_subject)
    await callback.answer()


@router.message(UserStates.ticket_subject)
async def process_ticket_subject(message: Message, state: FSMContext):
    """Process ticket subject."""
    subject = message.text.strip()
    if len(subject) < 3:
        await message.answer("❌ موضوع باید حداقل 3 کاراکتر باشد.")
        return

    await state.update_data(ticket_subject=subject)
    await message.answer(
        "📝 حالا پیام خود را بنویسید:\n\n"
        "(می‌توانید متن، عکس یا فایل ارسال کنید)"
    )
    await state.set_state(UserStates.ticket_message)


@router.message(UserStates.ticket_message)
async def process_ticket_message(message: Message, state: FSMContext, db_user: User):
    """Process ticket message and create ticket."""
    data = await state.get_data()
    subject = data.get("ticket_subject", "بدون موضوع")

    # Get message content
    text = message.text or message.caption or ""
    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id

    if not text and not file_id:
        await message.answer("❌ لطفاً یک پیام یا فایل ارسال کنید.")
        return

    async with get_session() as session:
        # Create ticket
        ticket = Ticket(
            user_id=db_user.id,
            subject=subject,
            status=TicketStatus.OPEN,
        )
        session.add(ticket)
        await session.flush()

        # Add message
        ticket_msg = TicketMessage(
            ticket_id=ticket.id,
            sender_id=db_user.telegram_id,
            is_admin=False,
            message=text,
            file_id=file_id,
        )
        session.add(ticket_msg)
        ticket_id = ticket.id

    await message.answer(
        f"✅ <b>تیکت #{ticket_id} ایجاد شد</b>\n\n"
        f"📌 موضوع: {subject}\n\n"
        f"پاسخ تیکت شما به زودی ارسال خواهد شد.",
        reply_markup=UserKeyboards.support_menu(),
    )

    # Notify admins
    from bot.loader import bot
    from core.services.notification import NotificationService
    from bot.keyboards.admin_kb import AdminKeyboards

    notifier = NotificationService(bot)
    await notifier.notify_admins(
        f"🎫 <b>تیکت جدید #{ticket_id}</b>\n\n"
        f"👤 کاربر: {db_user.mention} ({db_user.telegram_id})\n"
        f"📌 موضوع: {subject}\n"
        f"💬 پیام: {text[:200]}"
    )

    await state.clear()


@router.callback_query(F.data == "ticket:list")
async def list_tickets(callback: CallbackQuery, db_user: User):
    """List user's tickets."""
    async with get_session() as session:
        stmt = (
            select(Ticket)
            .where(Ticket.user_id == db_user.id)
            .order_by(Ticket.id.desc())
            .limit(10)
        )
        result = await session.execute(stmt)
        tickets = result.scalars().all()

    if not tickets:
        await callback.answer("تیکتی یافت نشد.", show_alert=True)
        return

    text = "📋 <b>تیکت‌های شما</b>\n\n"
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()

    status_icons = {
        TicketStatus.OPEN: "🟡",
        TicketStatus.ANSWERED: "🟢",
        TicketStatus.WAITING: "🟠",
        TicketStatus.CLOSED: "⚫",
    }

    for ticket in tickets:
        icon = status_icons.get(ticket.status, "⚪")
        builder.row(
            InlineKeyboardButton(
                text=f"{icon} #{ticket.id} - {ticket.subject[:30]}",
                callback_data=f"ticket:view:{ticket.id}",
            )
        )

    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="main:menu")
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("ticket:view:"))
async def view_ticket(callback: CallbackQuery, db_user: User):
    """View ticket messages."""
    ticket_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        stmt = (
            select(Ticket)
            .where(Ticket.id == ticket_id)
            .where(Ticket.user_id == db_user.id)
            .options(selectinload(Ticket.messages))
        )
        result = await session.execute(stmt)
        ticket = result.scalar_one_or_none()

    if not ticket:
        await callback.answer("⚠️ تیکت یافت نشد.", show_alert=True)
        return

    text = f"🎫 <b>تیکت #{ticket.id}</b>\n📌 {ticket.subject}\n\n"

    for msg in ticket.messages[-5:]:  # Last 5 messages
        sender = "👤 شما" if not msg.is_admin else "🛡️ پشتیبانی"
        text += f"{sender}:\n{msg.message}\n\n"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    if ticket.status != TicketStatus.CLOSED:
        builder.row(
            InlineKeyboardButton(
                text="💬 پاسخ", callback_data=f"ticket:reply:{ticket.id}"
            ),
            InlineKeyboardButton(
                text="🔒 بستن", callback_data=f"ticket:close:{ticket.id}"
            ),
        )
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="ticket:list")
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("ticket:reply:"))
async def reply_to_ticket(callback: CallbackQuery, state: FSMContext):
    """Start reply to ticket."""
    ticket_id = int(callback.data.split(":")[2])
    await state.update_data(reply_ticket_id=ticket_id)
    await state.set_state(UserStates.ticket_reply)
    await callback.message.edit_text("💬 پاسخ خود را بنویسید:")
    await callback.answer()


@router.message(UserStates.ticket_reply)
async def process_ticket_reply(message: Message, state: FSMContext, db_user: User):
    """Process ticket reply."""
    data = await state.get_data()
    ticket_id = data.get("reply_ticket_id")

    text = message.text or message.caption or ""
    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id

    async with get_session() as session:
        ticket = await session.get(Ticket, ticket_id)
        if not ticket or ticket.user_id != db_user.id:
            await message.answer("⚠️ خطا.")
            await state.clear()
            return

        ticket_msg = TicketMessage(
            ticket_id=ticket_id,
            sender_id=db_user.telegram_id,
            is_admin=False,
            message=text,
            file_id=file_id,
        )
        session.add(ticket_msg)
        ticket.status = TicketStatus.WAITING

    await message.answer(
        f"✅ پاسخ شما به تیکت #{ticket_id} ارسال شد.",
        reply_markup=UserKeyboards.support_menu(),
    )
    await state.clear()


@router.callback_query(F.data.startswith("ticket:close:"))
async def close_ticket(callback: CallbackQuery, db_user: User):
    """Close a ticket."""
    ticket_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        ticket = await session.get(Ticket, ticket_id)
        if ticket and ticket.user_id == db_user.id:
            ticket.status = TicketStatus.CLOSED

    await callback.answer("✅ تیکت بسته شد.")
    await callback.message.edit_text(f"🔒 تیکت #{ticket_id} بسته شد.")


@router.callback_query(F.data == "support:faq")
async def show_faq(callback: CallbackQuery):
    """Show FAQ."""
    faq_text = (
        "❓ <b>سوالات متداول</b>\n\n"
        "🔹 <b>چگونه سرویس بخرم؟</b>\n"
        "از منوی «خرید سرویس» پلن مورد نظر را انتخاب و پرداخت کنید.\n\n"
        "🔹 <b>چگونه از سرویس استفاده کنم؟</b>\n"
        "لینک اشتراک را در اپلیکیشن V2Ray وارد کنید.\n"
        "اپلیکیشن‌های پیشنهادی: v2rayNG (اندروید)، Streisand (iOS)\n\n"
        "🔹 <b>سرویسم قطع شده، چه کنم؟</b>\n"
        "ابتدا ترافیک و تاریخ انقضا را بررسی کنید. اگر مشکل ادامه داشت تیکت بزنید.\n\n"
        "🔹 <b>آیا امکان استرداد وجه وجود دارد؟</b>\n"
        "در صورت عدم استفاده از سرویس، با پشتیبانی تماس بگیرید.\n\n"
        "🔹 <b>زیرمجموعه‌گیری چیست؟</b>\n"
        "با اشتراک لینک دعوت، از خرید زیرمجموعه‌ها پورسانت دریافت کنید."
    )

    await callback.message.edit_text(
        faq_text, reply_markup=UserKeyboards.back_button("main:menu")
    )
    await callback.answer()
