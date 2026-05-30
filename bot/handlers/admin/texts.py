"""Admin bot text customization handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.filters.admin import AdminFilter
from core.services.bot_texts import get_text, set_text, reset_text, get_all_text_keys, DEFAULT_TEXTS

router = Router(name="admin_texts")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


class TextEditStates(StatesGroup):
    """States for text editing."""
    waiting_new_value = State()


@router.callback_query(F.data == "admin:settings:texts")
async def show_text_categories(callback: CallbackQuery):
    """Show text categories for editing."""
    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    # Group by category
    categories = {}
    for key, info in DEFAULT_TEXTS.items():
        cat = info["category"]
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1

    cat_names = {
        "general": "🌐 عمومی",
        "shop": "🛒 فروشگاه",
        "wallet": "💰 کیف پول",
        "support": "📞 پشتیبانی",
        "referral": "👥 زیرمجموعه",
        "services": "📦 سرویس‌ها",
    }

    builder = InlineKeyboardBuilder()
    for cat, count in categories.items():
        name = cat_names.get(cat, cat)
        builder.row(InlineKeyboardButton(
            text=f"{name} ({count})",
            callback_data=f"admin:texts:cat:{cat}",
        ))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:menu"))

    await callback.message.edit_text(
        "📝 <b>مدیریت متون ربات</b>\n\n"
        "دسته‌بندی مورد نظر را انتخاب کنید:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:texts:cat:"))
async def show_category_texts(callback: CallbackQuery):
    """Show texts in a category."""
    category = callback.data.split(":")[3]

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    text = f"📝 <b>متون دسته: {category}</b>\n\n"

    for key, info in DEFAULT_TEXTS.items():
        if info["category"] == category:
            desc = info["description"]
            text += f"• <code>{key}</code> — {desc}\n"
            builder.row(InlineKeyboardButton(
                text=f"✏️ {desc}",
                callback_data=f"admin:texts:edit:{key}",
            ))

    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:settings:texts"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:texts:edit:"))
async def edit_text_start(callback: CallbackQuery, state: FSMContext):
    """Start editing a text."""
    key = callback.data.replace("admin:texts:edit:", "")

    current_value = await get_text(key)
    info = DEFAULT_TEXTS.get(key, {})

    await state.update_data(edit_text_key=key)
    await state.set_state(TextEditStates.waiting_new_value)

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔄 بازگشت به پیش‌فرض", callback_data=f"admin:texts:reset:{key}"))
    builder.row(InlineKeyboardButton(text="❌ انصراف", callback_data="admin:settings:texts"))

    await callback.message.edit_text(
        f"✏️ <b>ویرایش متن: {info.get('description', key)}</b>\n\n"
        f"📋 کلید: <code>{key}</code>\n\n"
        f"📝 مقدار فعلی:\n<blockquote>{current_value[:500]}</blockquote>\n\n"
        f"متن جدید را ارسال کنید:\n"
        f"(از HTML استفاده کنید: <b>bold</b>, <i>italic</i>, <code>code</code>)\n\n"
        f"💡 متغیرها: متن می‌تواند شامل {{name}}, {{balance}} و... باشد.",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.message(TextEditStates.waiting_new_value)
async def process_new_text(message: Message, state: FSMContext):
    """Process new text value."""
    data = await state.get_data()
    key = data.get("edit_text_key")

    if not key:
        await message.answer("❌ خطا.")
        await state.clear()
        return

    # Check for cancel
    if message.text and (message.text.startswith("/cancel") or message.text in [
        "📊 داشبورد", "👥 کاربران", "🖥️ سرورها", "📋 پلن‌ها",
        "💳 پرداخت‌ها", "🎁 تخفیف‌ها", "📢 ارسال پیام", "🎫 تیکت‌ها",
        "⚙️ تنظیمات", "🗄️ پشتیبان‌گیری", "🔙 منوی کاربری",
    ]):
        await state.clear()
        await message.answer("❌ ویرایش لغو شد.")
        return

    new_value = message.text or ""
    success = await set_text(key, new_value)

    if success:
        await message.answer(
            f"✅ <b>متن بروزرسانی شد!</b>\n\n"
            f"📋 کلید: <code>{key}</code>\n"
            f"📝 مقدار جدید:\n{new_value[:300]}"
        )
    else:
        await message.answer("❌ خطا در ذخیره متن.")

    await state.clear()


@router.callback_query(F.data.startswith("admin:texts:reset:"))
async def reset_text_handler(callback: CallbackQuery, state: FSMContext):
    """Reset text to default."""
    key = callback.data.replace("admin:texts:reset:", "")

    await state.clear()
    success = await reset_text(key)

    if success:
        await callback.message.edit_text(f"✅ متن «{key}» به مقدار پیش‌فرض بازگردانده شد.")
    else:
        await callback.message.edit_text("❌ خطا.")

    await callback.answer()
