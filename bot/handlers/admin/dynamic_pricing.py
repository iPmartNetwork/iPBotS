"""Admin handler for Dynamic Pricing configuration."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.filters.admin import IsAdmin
from core.services.dynamic_pricing import dynamic_pricing

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.callback_query(F.data == "admin:dynamic_pricing")
async def show_dynamic_pricing(callback: CallbackQuery):
    """Show dynamic pricing configuration."""
    service = dynamic_pricing

    text = (
        "💰 <b>قیمت‌گذاری پویا</b>\n\n"
        f"⏰ <b>ساعات کم‌ترافیک:</b> {service.OFF_PEAK_HOURS[0]}:00 - {service.OFF_PEAK_HOURS[-1]}:00 UTC\n"
        f"   تخفیف: {service.OFF_PEAK_DISCOUNT}%\n\n"
        f"📅 <b>روزهای کم‌تقاضا:</b> {'دوشنبه، سه‌شنبه' if service.LOW_DEMAND_DAYS == [1, 2] else str(service.LOW_DEMAND_DAYS)}\n"
        f"   تخفیف: {service.LOW_DEMAND_DISCOUNT}%\n\n"
        f"🎯 <b>تخفیف وفاداری:</b> 5% (بعد از 5 خرید)\n\n"
        f"📊 <b>سقف تخفیف:</b> 25%\n\n"
        f"{'🟢 الان ساعت کم‌ترافیک است' if service.is_off_peak() else '🔴 الان ساعت پیک است'}"
    )

    # Test with sample price
    sample = service.calculate_discount(100000, user_purchases=3)
    text += (
        f"\n\n<b>نمونه (100,000 تومان، 3 خرید):</b>\n"
        f"قیمت نهایی: {sample['final_price']:,} تومان\n"
        f"تخفیف: {sample['discount_percent']}%\n"
        f"دلیل: {sample['reason'] or 'بدون تخفیف'}"
    )

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⏰ تغییر ساعات کم‌ترافیک",
                callback_data="admin:dp_edit_hours",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📊 تغییر درصد تخفیف‌ها",
                callback_data="admin:dp_edit_discounts",
            ),
        ],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:dashboard")],
    ])

    await callback.message.edit_text(text, reply_markup=buttons)


class DPStates(StatesGroup):
    """States for dynamic pricing config."""

    waiting_off_peak_discount = State()
    waiting_low_demand_discount = State()


@router.callback_query(F.data == "admin:dp_edit_discounts")
async def edit_discounts(callback: CallbackQuery, state: FSMContext):
    """Edit discount percentages."""
    await callback.message.edit_text(
        "📊 <b>تغییر درصد تخفیف‌ها</b>\n\n"
        f"تخفیف ساعات کم‌ترافیک فعلی: {dynamic_pricing.OFF_PEAK_DISCOUNT}%\n\n"
        "درصد جدید تخفیف ساعات کم‌ترافیک را وارد کنید (عدد):"
    )
    await state.set_state(DPStates.waiting_off_peak_discount)


@router.message(DPStates.waiting_off_peak_discount)
async def receive_off_peak_discount(message: Message, state: FSMContext):
    """Receive new off-peak discount."""
    try:
        value = int(message.text.strip())
        if not 0 <= value <= 50:
            await message.answer("❌ عدد باید بین 0 تا 50 باشد.")
            return
    except ValueError:
        await message.answer("❌ لطفاً یک عدد وارد کنید.")
        return

    dynamic_pricing.OFF_PEAK_DISCOUNT = value
    await state.update_data(off_peak=value)

    await message.answer(
        f"✅ تخفیف ساعات کم‌ترافیک: {value}%\n\n"
        f"حالا درصد تخفیف روزهای کم‌تقاضا را وارد کنید (فعلی: {dynamic_pricing.LOW_DEMAND_DISCOUNT}%):"
    )
    await state.set_state(DPStates.waiting_low_demand_discount)


@router.message(DPStates.waiting_low_demand_discount)
async def receive_low_demand_discount(message: Message, state: FSMContext):
    """Receive new low-demand discount."""
    try:
        value = int(message.text.strip())
        if not 0 <= value <= 50:
            await message.answer("❌ عدد باید بین 0 تا 50 باشد.")
            return
    except ValueError:
        await message.answer("❌ لطفاً یک عدد وارد کنید.")
        return

    dynamic_pricing.LOW_DEMAND_DISCOUNT = value
    await state.clear()

    await message.answer(
        f"✅ <b>تنظیمات ذخیره شد!</b>\n\n"
        f"⏰ تخفیف کم‌ترافیک: {dynamic_pricing.OFF_PEAK_DISCOUNT}%\n"
        f"📅 تخفیف کم‌تقاضا: {value}%\n\n"
        f"⚠️ توجه: این تغییرات تا ریستارت بات فعال هستند.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💰 قیمت‌گذاری پویا", callback_data="admin:dynamic_pricing")],
        ]),
    )


@router.callback_query(F.data == "admin:dp_edit_hours")
async def edit_hours_info(callback: CallbackQuery):
    """Show info about editing hours."""
    await callback.message.edit_text(
        "⏰ <b>ساعات کم‌ترافیک</b>\n\n"
        f"فعلی: {dynamic_pricing.OFF_PEAK_HOURS[0]}:00 - {dynamic_pricing.OFF_PEAK_HOURS[-1]}:00 UTC\n\n"
        "⚠️ برای تغییر ساعات، فایل تنظیمات سرور را ویرایش کنید:\n"
        "<code>core/services/dynamic_pricing.py</code>\n\n"
        "متغیر: <code>OFF_PEAK_HOURS</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:dynamic_pricing")],
        ]),
    )
