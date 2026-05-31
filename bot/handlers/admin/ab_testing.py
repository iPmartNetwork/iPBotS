"""Admin handler for A/B Testing management."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from loguru import logger

from bot.filters.admin import IsAdmin
from core.database.engine import get_session
from core.database.models.ab_test import ABTest

router = Router()
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


class ABTestStates(StatesGroup):
    """States for A/B test creation."""

    waiting_name = State()
    waiting_variant_a = State()
    waiting_variant_b = State()
    waiting_description = State()


@router.callback_query(F.data == "admin:ab_tests")
async def show_ab_tests(callback: CallbackQuery):
    """Show list of A/B tests."""
    async with get_session() as session:
        stmt = select(ABTest).order_by(ABTest.id.desc())
        result = await session.execute(stmt)
        tests = result.scalars().all()

    if not tests:
        text = "📊 <b>تست‌های A/B</b>\n\nهیچ تستی وجود ندارد."
    else:
        text = "📊 <b>تست‌های A/B</b>\n\n"
        for test in tests:
            status = "🟢" if test.is_active else "🔴"
            text += (
                f"{status} <b>{test.name}</b>\n"
                f"   نمایش: {test.total_impressions} | تبدیل: {test.total_conversions}\n"
                f"   A: {test.conversion_rate_a}% | B: {test.conversion_rate_b}%\n"
                f"   برنده: {test.winner}\n\n"
            )

    buttons = []
    for test in tests[:10]:
        buttons.append([
            InlineKeyboardButton(
                text=f"{'🟢' if test.is_active else '🔴'} {test.name}",
                callback_data=f"admin:ab_detail:{test.id}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="➕ تست جدید", callback_data="admin:ab_create"),
    ])
    buttons.append([
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:dashboard"),
    ])

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(F.data == "admin:ab_create")
async def start_create_ab_test(callback: CallbackQuery, state: FSMContext):
    """Start A/B test creation flow."""
    await callback.message.edit_text(
        "📝 <b>ساخت تست A/B جدید</b>\n\n"
        "نام تست را وارد کنید:\n"
        "(مثال: pricing_page_v2)"
    )
    await state.set_state(ABTestStates.waiting_name)


@router.message(ABTestStates.waiting_name)
async def receive_test_name(message: Message, state: FSMContext):
    """Receive test name."""
    await state.update_data(name=message.text.strip())
    await message.answer(
        "✅ نام: <code>{}</code>\n\n"
        "حالا <b>متن Variant A</b> (کنترل) را وارد کنید:".format(message.text.strip())
    )
    await state.set_state(ABTestStates.waiting_variant_a)


@router.message(ABTestStates.waiting_variant_a)
async def receive_variant_a(message: Message, state: FSMContext):
    """Receive variant A text."""
    await state.update_data(variant_a=message.text)
    await message.answer(
        "✅ Variant A ذخیره شد.\n\n"
        "حالا <b>متن Variant B</b> (تغییر) را وارد کنید:"
    )
    await state.set_state(ABTestStates.waiting_variant_b)


@router.message(ABTestStates.waiting_variant_b)
async def receive_variant_b(message: Message, state: FSMContext):
    """Receive variant B text and create test."""
    data = await state.get_data()
    name = data["name"]
    variant_a = data["variant_a"]
    variant_b = message.text

    async with get_session() as session:
        test = ABTest(
            name=name,
            variant_a=variant_a,
            variant_b=variant_b,
            is_active=True,
        )
        session.add(test)

    await state.clear()
    await message.answer(
        f"✅ <b>تست A/B ساخته شد!</b>\n\n"
        f"📋 نام: {name}\n"
        f"🅰️ Variant A: {variant_a[:50]}...\n"
        f"🅱️ Variant B: {variant_b[:50]}...\n\n"
        f"تست فعال است و به کاربران نمایش داده می‌شود.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 لیست تست‌ها", callback_data="admin:ab_tests")],
        ]),
    )
    logger.info(f"A/B test created: {name}")


@router.callback_query(F.data.startswith("admin:ab_detail:"))
async def show_ab_detail(callback: CallbackQuery):
    """Show detailed A/B test results."""
    test_id = int(callback.data.split(":")[-1])

    async with get_session() as session:
        test = await session.get(ABTest, test_id)

    if not test:
        await callback.answer("تست یافت نشد!", show_alert=True)
        return

    text = (
        f"📊 <b>تست: {test.name}</b>\n"
        f"{'🟢 فعال' if test.is_active else '🔴 غیرفعال'}\n\n"
        f"🅰️ <b>Variant A (کنترل):</b>\n"
        f"<i>{test.variant_a[:100]}</i>\n"
        f"👁 نمایش: {test.impressions_a}\n"
        f"✅ تبدیل: {test.conversions_a}\n"
        f"📈 نرخ: {test.conversion_rate_a}%\n\n"
        f"🅱️ <b>Variant B (تغییر):</b>\n"
        f"<i>{test.variant_b[:100]}</i>\n"
        f"👁 نمایش: {test.impressions_b}\n"
        f"✅ تبدیل: {test.conversions_b}\n"
        f"📈 نرخ: {test.conversion_rate_b}%\n\n"
        f"🏆 <b>برنده: Variant {test.winner}</b>"
    )

    toggle_text = "⏸ غیرفعال کردن" if test.is_active else "▶️ فعال کردن"

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=toggle_text,
                callback_data=f"admin:ab_toggle:{test.id}",
            ),
            InlineKeyboardButton(
                text="🗑 حذف",
                callback_data=f"admin:ab_delete:{test.id}",
            ),
        ],
        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:ab_tests")],
    ])

    await callback.message.edit_text(text, reply_markup=buttons)


@router.callback_query(F.data.startswith("admin:ab_toggle:"))
async def toggle_ab_test(callback: CallbackQuery):
    """Toggle A/B test active status."""
    test_id = int(callback.data.split(":")[-1])

    async with get_session() as session:
        test = await session.get(ABTest, test_id)
        if test:
            test.is_active = not test.is_active
            status = "فعال" if test.is_active else "غیرفعال"

    await callback.answer(f"تست {status} شد!", show_alert=True)
    await show_ab_tests(callback)


@router.callback_query(F.data.startswith("admin:ab_delete:"))
async def delete_ab_test(callback: CallbackQuery):
    """Delete an A/B test."""
    test_id = int(callback.data.split(":")[-1])

    async with get_session() as session:
        test = await session.get(ABTest, test_id)
        if test:
            await session.delete(test)

    await callback.answer("تست حذف شد!", show_alert=True)
    await show_ab_tests(callback)
