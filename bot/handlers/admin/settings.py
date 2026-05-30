"""Admin settings, tickets, discounts, and backup handlers - complete rewrite."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_kb import AdminKeyboards
from bot.states import AdminStates
from core.database.engine import get_session
from core.database.models import (
    Ticket, TicketMessage, TicketStatus, User,
    DiscountCode, DiscountType,
)

router = Router(name="admin_settings")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


# ═══════════════════════════════════════════
# TICKETS
# ═══════════════════════════════════════════

@router.message(F.text == "🎫 تیکت‌ها")
async def tickets_menu(message: Message, state: FSMContext):
    """Show open tickets."""
    await state.clear()

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

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()

    text = f"🎫 <b>تیکت‌های باز</b> ({len(tickets)})\n\n"

    for ticket in tickets:
        icon = "🟡" if ticket.status == TicketStatus.OPEN else "🟠"
        name = ticket.user.full_name[:12] if ticket.user else "?"
        text += f"{icon} #{ticket.id} | {ticket.subject[:20]} | {name}\n"
        builder.row(
            InlineKeyboardButton(
                text=f"{icon} #{ticket.id} - {ticket.subject[:25]}",
                callback_data=f"admin:ticket:view:{ticket.id}",
            )
        )

    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("admin:ticket:view:"))
async def admin_view_ticket(callback: CallbackQuery):
    """View ticket details."""
    ticket_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        stmt = (
            select(Ticket)
            .where(Ticket.id == ticket_id)
            .options(selectinload(Ticket.messages), selectinload(Ticket.user))
        )
        result = await session.execute(stmt)
        ticket = result.scalar_one_or_none()

    if not ticket:
        await callback.answer("⚠️ یافت نشد.", show_alert=True)
        return

    text = (
        f"🎫 <b>تیکت #{ticket.id}</b>\n"
        f"👤 {ticket.user.full_name if ticket.user else '?'}\n"
        f"📌 {ticket.subject}\n\n"
    )

    for msg in ticket.messages[-5:]:
        sender = "👤" if not msg.is_admin else "🛡️"
        text += f"{sender} {msg.message[:200]}\n\n"

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    if ticket.status != TicketStatus.CLOSED:
        builder.row(
            InlineKeyboardButton(text="💬 پاسخ", callback_data=f"admin:ticket:reply:{ticket.id}"),
            InlineKeyboardButton(text="🔒 بستن", callback_data=f"admin:ticket:close:{ticket.id}"),
        )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:ticket:reply:"))
async def admin_reply_ticket(callback: CallbackQuery, state: FSMContext):
    """Start reply to ticket."""
    ticket_id = int(callback.data.split(":")[3])
    await state.update_data(reply_ticket_id=ticket_id)
    await state.set_state(AdminStates.ticket_reply)
    await callback.message.edit_text(f"💬 پاسخ خود را برای تیکت #{ticket_id} بنویسید:")
    await callback.answer()


@router.message(AdminStates.ticket_reply)
async def process_admin_reply(message: Message, state: FSMContext):
    """Process admin ticket reply."""
    data = await state.get_data()
    ticket_id = data.get("reply_ticket_id")

    async with get_session() as session:
        ticket = await session.get(Ticket, ticket_id)
        if not ticket:
            await message.answer("❌ تیکت یافت نشد.")
            await state.clear()
            return

        ticket_msg = TicketMessage(
            ticket_id=ticket_id,
            sender_id=message.from_user.id,
            is_admin=True,
            message=message.text,
        )
        session.add(ticket_msg)
        ticket.status = TicketStatus.ANSWERED

        user = await session.get(User, ticket.user_id)

    await message.answer(f"✅ پاسخ به تیکت #{ticket_id} ارسال شد.")

    if user:
        from bot.loader import bot
        try:
            await bot.send_message(
                user.telegram_id,
                f"📩 <b>پاسخ جدید</b>\n\nتیکت #{ticket_id} پاسخ دریافت کرد.\n\n🛡️ {message.text}"
            )
        except Exception:
            pass

    await state.clear()


@router.callback_query(F.data.startswith("admin:ticket:close:"))
async def close_ticket(callback: CallbackQuery):
    """Close ticket."""
    ticket_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        ticket = await session.get(Ticket, ticket_id)
        if ticket:
            ticket.status = TicketStatus.CLOSED

    await callback.message.edit_text(f"🔒 تیکت #{ticket_id} بسته شد.")
    await callback.answer()


# ═══════════════════════════════════════════
# DISCOUNTS
# ═══════════════════════════════════════════

@router.message(F.text == "🎁 تخفیف‌ها")
async def discounts_menu(message: Message, state: FSMContext):
    """Show discounts."""
    await state.clear()

    async with get_session() as session:
        stmt = select(DiscountCode).order_by(DiscountCode.id.desc()).limit(20)
        result = await session.execute(stmt)
        codes = result.scalars().all()

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()

    text = "🎁 <b>کدهای تخفیف</b>\n\n"

    if codes:
        for code in codes:
            status = "✅" if code.is_valid else "❌"
            val = f"{code.value}%" if code.discount_type == DiscountType.PERCENT else f"{code.value:,}ت"
            text += f"{status} <code>{code.code}</code> | {val} | استفاده: {code.used_count}/{code.max_uses or '♾️'}\n"
    else:
        text += "کدی وجود ندارد.\n"

    builder.row(InlineKeyboardButton(text="➕ کد جدید", callback_data="admin:discount:add"))

    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "admin:discount:add")
async def add_discount_start(callback: CallbackQuery, state: FSMContext):
    """Start adding discount code."""
    await callback.message.edit_text(
        "🎁 <b>ساخت کد تخفیف</b>\n\n"
        "کد تخفیف را وارد کنید:\n"
        "(مثال: SALE20)"
    )
    await state.set_state(AdminStates.discount_code)
    await callback.answer()


@router.message(AdminStates.discount_code)
async def discount_code_input(message: Message, state: FSMContext):
    """Process discount code."""
    await state.update_data(discount_code=message.text.strip().upper())

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="درصدی (%)", callback_data="dtype:percent")],
            [InlineKeyboardButton(text="مبلغ ثابت (تومان)", callback_data="dtype:fixed")],
        ]
    )
    await message.answer("نوع تخفیف:", reply_markup=kb)
    await state.set_state(AdminStates.discount_type)


@router.callback_query(AdminStates.discount_type, F.data.startswith("dtype:"))
async def discount_type_input(callback: CallbackQuery, state: FSMContext):
    """Process discount type."""
    dtype = callback.data.split(":")[1]
    await state.update_data(discount_type=dtype)

    if dtype == "percent":
        await callback.message.edit_text("مقدار تخفیف (درصد):\n(مثال: 20)")
    else:
        await callback.message.edit_text("مقدار تخفیف (تومان):\n(مثال: 50000)")

    await state.set_state(AdminStates.discount_value)
    await callback.answer()


@router.message(AdminStates.discount_value)
async def discount_value_input(message: Message, state: FSMContext):
    """Process discount value."""
    try:
        value = int(message.text.replace(",", "").strip())
    except ValueError:
        await message.answer("❌ عدد وارد کنید.")
        return

    await state.update_data(discount_value=value)
    await message.answer("حداکثر تعداد استفاده:\n(0 = نامحدود)")
    await state.set_state(AdminStates.discount_max_uses)


@router.message(AdminStates.discount_max_uses)
async def discount_max_uses_input(message: Message, state: FSMContext):
    """Process max uses and create discount."""
    try:
        max_uses = int(message.text.strip())
    except ValueError:
        max_uses = 0

    data = await state.get_data()
    dtype = DiscountType.PERCENT if data["discount_type"] == "percent" else DiscountType.FIXED

    async with get_session() as session:
        code = DiscountCode(
            code=data["discount_code"],
            discount_type=dtype,
            value=data["discount_value"],
            max_uses=max_uses,
            is_active=True,
            one_per_user=True,
        )
        session.add(code)

    val_text = f"{data['discount_value']}%" if dtype == DiscountType.PERCENT else f"{data['discount_value']:,} تومان"

    await message.answer(
        f"✅ <b>کد تخفیف ایجاد شد!</b>\n\n"
        f"🏷️ کد: <code>{data['discount_code']}</code>\n"
        f"💰 مقدار: {val_text}\n"
        f"🔢 حداکثر استفاده: {max_uses or '♾️'}"
    )
    await state.clear()


# ═══════════════════════════════════════════
# SETTINGS & BACKUP
# ═══════════════════════════════════════════

@router.message(F.text == "⚙️ تنظیمات")
async def settings_menu(message: Message, state: FSMContext):
    """Show settings."""
    await state.clear()
    await message.answer("⚙️ <b>تنظیمات</b>", reply_markup=AdminKeyboards.settings_menu())


@router.message(F.text == "🗄️ پشتیبان‌گیری")
async def manual_backup(message: Message, state: FSMContext):
    """Trigger manual backup."""
    await state.clear()
    await message.answer("🔄 در حال ایجاد پشتیبان...")

    from core.scheduler.jobs import auto_backup

    try:
        await auto_backup()
        await message.answer("✅ پشتیبان‌گیری انجام شد.")
    except Exception as e:
        await message.answer(f"❌ خطا: {e}")


@router.callback_query(F.data == "admin:settings:payment")
async def payment_settings(callback: CallbackQuery):
    """Payment notification settings info."""
    from bot.config import settings

    group_id = settings.PAYMENT_GROUP_ID
    topic_wallet = settings.PAYMENT_TOPIC_CARD2CARD_WALLET
    topic_purchase = settings.PAYMENT_TOPIC_CARD2CARD_PURCHASE
    topic_online = settings.PAYMENT_TOPIC_ONLINE

    text = (
        f"💳 <b>تنظیمات اعلان پرداخت</b>\n\n"
        f"📍 گروه: <code>{group_id or 'غیرفعال'}</code>\n"
        f"🏦 تاپیک شارژ کیف پول: <code>{topic_wallet or 'ندارد'}</code>\n"
        f"🛒 تاپیک خرید مستقیم: <code>{topic_purchase or 'ندارد'}</code>\n"
        f"💳 تاپیک درگاه آنلاین: <code>{topic_online or 'ندارد'}</code>\n\n"
        f"⚙️ برای تغییر، فایل .env را ویرایش کنید:\n"
        f"<code>PAYMENT_GROUP_ID=...</code>\n"
        f"<code>PAYMENT_TOPIC_CARD2CARD_WALLET=...</code>\n"
        f"<code>PAYMENT_TOPIC_CARD2CARD_PURCHASE=...</code>\n"
        f"<code>PAYMENT_TOPIC_ONLINE=...</code>\n\n"
        f"💡 بات باید ادمین گروه باشد.\n"
        f"💡 برای فروم، شناسه تاپیک را وارد کنید."
    )

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:settings:"))
async def settings_placeholder(callback: CallbackQuery):
    """Settings sub-menu placeholder."""
    await callback.answer("⚙️ این بخش به زودی فعال می‌شود.", show_alert=True)


@router.callback_query(F.data == "admin:broadcast:select")
async def broadcast_select_placeholder(callback: CallbackQuery):
    """Broadcast to specific group - placeholder."""
    await callback.answer("📋 ارسال به دسته خاص به زودی فعال می‌شود.", show_alert=True)


@router.callback_query(F.data == "admin:giftcard:add")
async def giftcard_add_placeholder(callback: CallbackQuery):
    """Gift card creation - placeholder."""
    await callback.answer("🎁 ساخت گیفت کارت به زودی فعال می‌شود.", show_alert=True)


@router.callback_query(F.data == "admin:discount:list")
async def discount_list_callback(callback: CallbackQuery):
    """Show discount list via callback."""
    from core.database.models import DiscountCode, DiscountType

    async with get_session() as session:
        stmt = select(DiscountCode).order_by(DiscountCode.id.desc()).limit(20)
        result = await session.execute(stmt)
        codes = result.scalars().all()

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    text = "🎁 <b>کدهای تخفیف</b>\n\n"

    if codes:
        for code in codes:
            status = "✅" if code.is_valid else "❌"
            val = f"{code.value}%" if code.discount_type == DiscountType.PERCENT else f"{code.value:,}ت"
            text += f"{status} <code>{code.code}</code> | {val}\n"
    else:
        text += "کدی وجود ندارد.\n"

    builder.row(InlineKeyboardButton(text="➕ کد جدید", callback_data="admin:discount:add"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:cancel:"))
async def cancel_action(callback: CallbackQuery):
    """Cancel a pending action."""
    await callback.message.edit_text("❌ عملیات لغو شد.")
    await callback.answer()
