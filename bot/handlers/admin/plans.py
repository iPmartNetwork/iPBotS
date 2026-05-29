"""Admin plan management handlers - complete rewrite."""

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
async def plans_menu(message: Message, state: FSMContext):
    """Show plans management menu."""
    await state.clear()

    async with get_session() as session:
        stmt = select(Plan).order_by(Plan.sort_order, Plan.id)
        result = await session.execute(stmt)
        plans = result.scalars().all()

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()

    text = "📋 <b>مدیریت پلن‌ها</b>\n\n"

    if plans:
        for plan in plans:
            status = "✅" if plan.is_active else "❌"
            text += f"{status} <b>{plan.name}</b> | {plan.display_data} | {plan.display_duration} | {plan.price:,}ت\n"
            builder.row(
                InlineKeyboardButton(
                    text=f"{'✅' if plan.is_active else '❌'} {plan.name}",
                    callback_data=f"admin:plan:toggle:{plan.id}",
                )
            )
    else:
        text += "هیچ پلنی وجود ندارد.\n"

    builder.row(InlineKeyboardButton(text="➕ پلن جدید", callback_data="admin:plan:add"))
    builder.row(InlineKeyboardButton(text="📁 دسته‌بندی‌ها", callback_data="admin:categories:list"))

    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("admin:plan:toggle:"))
async def toggle_plan(callback: CallbackQuery):
    """Toggle plan active status."""
    plan_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        plan = await session.get(Plan, plan_id)
        if plan:
            plan.is_active = not plan.is_active
            new_status = "فعال ✅" if plan.is_active else "غیرفعال ❌"

    await callback.answer(f"پلن {new_status} شد", show_alert=True)


@router.callback_query(F.data == "admin:plan:add")
async def add_plan_start(callback: CallbackQuery, state: FSMContext):
    """Start adding a new plan."""
    await state.clear()
    await callback.message.edit_text(
        "📋 <b>افزودن پلن جدید</b>\n\n"
        "نام پلن را وارد کنید:\n"
        "(مثال: پلن 30 گیگ ماهانه)"
    )
    await state.set_state(AdminStates.plan_name)
    await callback.answer()


@router.message(AdminStates.plan_name)
async def plan_name_input(message: Message, state: FSMContext):
    """Process plan name."""
    await state.update_data(plan_name=message.text.strip())
    await message.answer(
        "📊 حجم ترافیک (گیگابایت):\n"
        "(0 = نامحدود)"
    )
    await state.set_state(AdminStates.plan_data)


@router.message(AdminStates.plan_data)
async def plan_data_input(message: Message, state: FSMContext):
    """Process plan data limit."""
    try:
        data_gb = int(message.text.strip())
    except ValueError:
        await message.answer("❌ عدد وارد کنید.")
        return

    await state.update_data(plan_data=data_gb)
    await message.answer("⏱️ مدت زمان (روز):\n(مثال: 30)")
    await state.set_state(AdminStates.plan_duration)


@router.message(AdminStates.plan_duration)
async def plan_duration_input(message: Message, state: FSMContext):
    """Process plan duration."""
    try:
        days = int(message.text.strip())
    except ValueError:
        await message.answer("❌ عدد وارد کنید.")
        return

    if days <= 0:
        await message.answer("❌ باید بیشتر از 0 باشد.")
        return

    await state.update_data(plan_duration=days)
    await message.answer("💰 قیمت (تومان):\n(مثال: 50000)")
    await state.set_state(AdminStates.plan_price)


@router.message(AdminStates.plan_price)
async def plan_price_input(message: Message, state: FSMContext):
    """Process plan price."""
    try:
        price = int(message.text.replace(",", "").strip())
    except ValueError:
        await message.answer("❌ عدد وارد کنید.")
        return

    if price <= 0:
        await message.answer("❌ قیمت باید بیشتر از 0 باشد.")
        return

    await state.update_data(plan_price=price)
    await message.answer("👥 تعداد کاربر همزمان (IP Limit):\n(پیش‌فرض: 1)")
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
        f"✅ <b>پلن ایجاد شد!</b>\n\n"
        f"📋 نام: {data['plan_name']}\n"
        f"📊 حجم: {data['plan_data']} GB {'(نامحدود)' if data['plan_data'] == 0 else ''}\n"
        f"⏱️ مدت: {data['plan_duration']} روز\n"
        f"💰 قیمت: {data['plan_price']:,} تومان\n"
        f"👥 کاربر همزمان: {ip_limit}\n\n"
        f"⚠️ برای نمایش در فروشگاه، یک دسته‌بندی تخصیص دهید."
    )
    await state.clear()


@router.callback_query(F.data == "admin:categories:list")
async def list_categories(callback: CallbackQuery):
    """List plan categories."""
    async with get_session() as session:
        stmt = select(PlanCategory).order_by(PlanCategory.sort_order)
        result = await session.execute(stmt)
        categories = result.scalars().all()

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()

    text = "📁 <b>دسته‌بندی‌ها</b>\n\n"
    if categories:
        for cat in categories:
            status = "✅" if cat.is_active else "❌"
            text += f"{status} {cat.icon} {cat.name}\n"
    else:
        text += "دسته‌بندی‌ای وجود ندارد.\n"

    builder.row(InlineKeyboardButton(text="➕ دسته‌بندی جدید", callback_data="admin:category:add"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "admin:category:add")
async def add_category(callback: CallbackQuery, state: FSMContext):
    """Add new category - simple inline."""
    await callback.message.edit_text(
        "📁 نام دسته‌بندی جدید را ارسال کنید:\n"
        "(مثال: اقتصادی)"
    )
    await state.set_state(AdminStates.plan_category)
    await callback.answer()


@router.message(AdminStates.plan_category)
async def process_new_category(message: Message, state: FSMContext):
    """Create new category."""
    name = message.text.strip()

    async with get_session() as session:
        cat = PlanCategory(name=name, icon="📦", is_active=True)
        session.add(cat)

    await message.answer(f"✅ دسته‌بندی «{name}» ایجاد شد.")
    await state.clear()
