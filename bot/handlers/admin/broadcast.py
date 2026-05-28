"""Admin broadcast message handlers."""

import asyncio

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_kb import AdminKeyboards
from bot.states import AdminStates
from core.database.engine import get_session
from core.database.models import User

router = Router(name="admin_broadcast")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(F.text == "📢 ارسال پیام")
async def broadcast_menu(message: Message):
    """Show broadcast options."""
    await message.answer(
        "📢 <b>ارسال پیام انبوه</b>\n\n"
        "نوع ارسال را انتخاب کنید:",
        reply_markup=AdminKeyboards.broadcast_options(),
    )


@router.callback_query(F.data == "admin:broadcast:all")
async def broadcast_all(callback: CallbackQuery, state: FSMContext):
    """Broadcast to all users."""
    await state.update_data(broadcast_target="all")
    await callback.message.edit_text(
        "📢 <b>ارسال به همه کاربران</b>\n\n"
        "پیام خود را بنویسید:\n"
        "(می‌توانید از HTML استفاده کنید)"
    )
    await state.set_state(AdminStates.broadcast_message)
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast:active")
async def broadcast_active(callback: CallbackQuery, state: FSMContext):
    """Broadcast to active users only."""
    await state.update_data(broadcast_target="active")
    await callback.message.edit_text(
        "📢 <b>ارسال به کاربران فعال</b>\n\n"
        "پیام خود را بنویسید:"
    )
    await state.set_state(AdminStates.broadcast_message)
    await callback.answer()


@router.message(AdminStates.broadcast_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Process broadcast message and confirm."""
    await state.update_data(broadcast_text=message.text)
    data = await state.get_data()
    target = data.get("broadcast_target", "all")

    async with get_session() as session:
        if target == "active":
            stmt = select(User).where(User.is_active == True, User.is_banned == False)
        else:
            stmt = select(User).where(User.is_banned == False)

        result = await session.execute(stmt)
        users = result.scalars().all()
        user_count = len(users)

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ ارسال به {user_count} کاربر",
                    callback_data="admin:broadcast:confirm",
                ),
            ],
            [
                InlineKeyboardButton(text="❌ انصراف", callback_data="admin:menu"),
            ],
        ]
    )

    await message.answer(
        f"📢 <b>پیش‌نمایش پیام:</b>\n\n"
        f"{message.text}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 تعداد دریافت‌کنندگان: {user_count}\n"
        f"📋 هدف: {'همه' if target == 'all' else 'فعال‌ها'}",
        reply_markup=kb,
    )
    await state.set_state(AdminStates.broadcast_confirm)


@router.callback_query(AdminStates.broadcast_confirm, F.data == "admin:broadcast:confirm")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    """Confirm and send broadcast."""
    data = await state.get_data()
    text = data.get("broadcast_text", "")
    target = data.get("broadcast_target", "all")

    await state.clear()
    await callback.message.edit_text("📢 در حال ارسال...")
    await callback.answer()

    async with get_session() as session:
        if target == "active":
            stmt = select(User).where(User.is_active == True, User.is_banned == False)
        else:
            stmt = select(User).where(User.is_banned == False)

        result = await session.execute(stmt)
        users = result.scalars().all()

    from bot.loader import bot

    success = 0
    failed = 0
    blocked = 0

    for user in users:
        try:
            await bot.send_message(user.telegram_id, text)
            success += 1
        except Exception as e:
            error_msg = str(e).lower()
            if "blocked" in error_msg or "deactivated" in error_msg:
                blocked += 1
            else:
                failed += 1

        # Rate limit: 30 messages per second
        if (success + failed + blocked) % 30 == 0:
            await asyncio.sleep(1)

    await callback.message.answer(
        f"✅ <b>ارسال پیام انبوه تمام شد</b>\n\n"
        f"✅ موفق: {success}\n"
        f"🚫 بلاک شده: {blocked}\n"
        f"❌ ناموفق: {failed}\n"
        f"📊 کل: {success + failed + blocked}"
    )
