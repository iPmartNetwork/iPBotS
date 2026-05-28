"""Admin plan management handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_kb import AdminKeyboards
from bot.states import AdminStates
from core.database.engine import get_session
from core.database.models import Plan, PlanCategory, Server

router = Router(name="admin_plans")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(F.text == "📋 پلن‌ها")
async def plans_menu(message: Message):
    """Show plans management menu."""
    await message.answer(
        "📋 <b>مدیریت پلن‌ها</b>",
        reply_markup=AdminKeyboards.plan_management(),
    )


@router.callback_query(F.data == "admin:plans:list")
async def list_plans(callback: CallbackQuery):
    """List all plans."""
    async with get_session() as session:
        stmt = select(Plan).order_by(Plan.sort_order)
        result = await session.execute(stmt)
        plans = result.scalars().all()

    if not plans:
        await callback.answer("پلنی وجود ندارد.", show_alert=True)
        return

    text = "📋 <b>لیست پلن‌ها</b>\n\n"
    for plan in plans:
        status = "✅" if plan.is_active else "❌"
        text += (
            f"{status} <b>{plan.name}</b>\n"
            f"   💰 {plan.price:,} تومان | 📊 {plan.display_data} | ⏱️ {plan.display_duration}\n\n"
        )

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ پلن جدید", callback_data="admin:plan:add")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:menu")
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "admin:plan:add")
async def add_plan_start(callback: CallbackQuery, state: FSMContext):
    """Start adding a new plan."""
    await callback.message.edit_text(
        "📋 <b>افزودن پلن جدید</b>\n\n"
        "نام پلن را وارد کنید:"
    )
    await state.set_state(AdminStates.plan_name)
    await callback.answer()


@router.message(AdminStates.plan_name)
async def plan_name_input(message: Message, state: FSMContext):
    """Process plan name."""
    await state.update_data(plan_name=message.text.strip())
    await message.answer(
        "حجم ترافیک را به گیگابایت وارد کنید:\n(0 = نامحدود)"
    )
    await state.set_state(AdminStates.plan_data)


@router.message(AdminStates.plan_data)
async def plan_data_input(message: Message, state: FSMContext):
    """Process plan data limit."""
    try:
        data_gb = int(message.text.strip())
    except ValueError:
        await message.answer("❌ عدد معتبر وارد کنید.")
        return

    await state.update_data(plan_data=data_gb)
    await message.answer("مدت زمان را به روز وارد کنید:")
    await state.set_state(AdminStates.plan_duration)


@router.message(AdminStates.plan_duration)
async def plan_duration_input(message: Message, state: FSMContext):
    """Process plan duration."""
    try:
        days = int(message.text.strip())
    except ValueError:
        await message.answer("❌ عدد معتبر وارد کنید.")
        return

    await state.update_data(plan_duration=days)
    await message.answer("قیمت را به تومان وارد کنید:")
    await state.set_state(AdminStates.plan_price)


@router.message(AdminStates.plan_price)
async def plan_price_input(message: Message, state: FSMContext):
    """Process plan price."""
    try:
        price = int(message.text.replace(",", "").strip())
    except ValueError:
        await message.answer("❌ عدد معتبر وارد کنید.")
        return

    await state.update_data(plan_price=price)
    await message.answer(
        "تعداد کاربر همزمان (IP Limit) را وارد کنید:\n(پیش‌فرض: 1)"
    )
    await state.set_state(AdminStates.plan_ip_limit)


@router.message(AdminStates.plan_ip_limit)
async def plan_ip_limit_input(message: Message, state: FSMContext):
    """Process IP limit and create plan."""
    try:
        ip_limit = int(message.text.strip()) if message.text.strip() else 1
    except ValueError:
        ip_limit = 1

    data = await state.get_data()

    async with get_session() as session:
        plan = Plan(
            name=data["plan_name"],
            data_limit_gb=data["plan_data"],
            duration_days=data["plan_duration"],
            price=data["plan_price"],
            ip_limit=ip_limit,
            is_active=True,
        )
        session.add(plan)

    await message.answer(
        f"✅ <b>پلن ایجاد شد</b>\n\n"
        f"📋 نام: {data['plan_name']}\n"
        f"📊 حجم: {data['plan_data']} GB\n"
        f"⏱️ مدت: {data['plan_duration']} روز\n"
        f"💰 قیمت: {data['plan_price']:,} تومان\n"
        f"👥 کاربر همزمان: {ip_limit}\n\n"
        f"⚠️ برای تخصیص سرور و inbound، پلن را ویرایش کنید."
    )
    await state.clear()


@router.callback_query(F.data == "admin:categories:list")
async def list_categories(callback: CallbackQuery):
    """List plan categories."""
    async with get_session() as session:
        stmt = select(PlanCategory).order_by(PlanCategory.sort_order)
        result = await session.execute(stmt)
        categories = result.scalars().all()

    text = "📁 <b>دسته‌بندی‌ها</b>\n\n"
    if categories:
        for cat in categories:
            status = "✅" if cat.is_active else "❌"
            text += f"{status} {cat.icon} {cat.name}\n"
    else:
        text += "دسته‌بندی‌ای وجود ندارد."

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ دسته‌بندی جدید", callback_data="admin:category:add")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:menu")
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
