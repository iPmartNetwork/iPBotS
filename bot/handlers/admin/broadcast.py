"""Admin broadcast message handlers - complete rewrite."""

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
async def broadcast_menu(message: Message, state: FSMContext):
    """Show broadcast options."""
    await state.clear()
    await message.answer(
        "📢 <b>ارسال پیام انبوه</b>\n\nنوع ارسال را انتخاب کنید:",
        reply_markup=AdminKeyboards.broadcast_options(),
    )


@router.callback_query(F.data == "admin:broadcast:all")
async def broadcast_all(callback: CallbackQuery, state: FSMContext):
    """Broadcast to all users."""
    await state.update_data(broadcast_target="all")
    await callback.message.edit_text(
        "📢 <b>ارسال به همه</b>\n\n"
        "پیام خود را بنویسید:\n"
        "(HTML پشتیبانی می‌شود: <b>bold</b>, <i>italic</i>, <code>code</code>)"
    )
    await state.set_state(AdminStates.broadcast_message)
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast:active")
async def broadcast_active(callback: CallbackQuery, state: FSMContext):
    """Broadcast to active users."""
    await state.update_data(broadcast_target="active")
    await callback.message.edit_text("📢 <b>ارسال به فعال‌ها</b>\n\nپیام خود را بنویسید:")
    await state.set_state(AdminStates.broadcast_message)
    await callback.answer()


@router.message(AdminStates.broadcast_message)
async def process_broadcast(message: Message, state: FSMContext):
    """Process and confirm broadcast."""
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
            [InlineKeyboardButton(text=f"✅ ارسال به {user_count} نفر", callback_data="admin:broadcast:send")],
            [InlineKeyboardButton(text="❌ انصراف", callback_data="admin:broadcast:cancel")],
        ]
    )

    await message.answer(
        f"📢 <b>پیش‌نمایش:</b>\n\n{message.text}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👥 دریافت‌کنندگان: {user_count}",
        reply_markup=kb,
    )
    await state.set_state(AdminStates.broadcast_confirm)


@router.callback_query(AdminStates.broadcast_confirm, F.data == "admin:broadcast:send")
async def send_broadcast(callback: CallbackQuery, state: FSMContext):
    """Send broadcast."""
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
            if "blocked" in str(e).lower() or "deactivated" in str(e).lower():
                blocked += 1
            else:
                failed += 1

        if (success + failed + blocked) % 25 == 0:
            await asyncio.sleep(1)

    await callback.message.answer(
        f"✅ <b>ارسال تمام شد</b>\n\n"
        f"✅ موفق: {success}\n"
        f"🚫 بلاک: {blocked}\n"
        f"❌ ناموفق: {failed}\n"
        f"📊 کل: {success + failed + blocked}"
    )


@router.callback_query(AdminStates.broadcast_confirm, F.data == "admin:broadcast:cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    """Cancel broadcast."""
    await state.clear()
    await callback.message.edit_text("❌ ارسال لغو شد.")
    await callback.answer()
