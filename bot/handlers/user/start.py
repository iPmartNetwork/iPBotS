"""Start and main menu handlers."""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.user_kb import UserKeyboards
from bot.config import settings
from core.database.models import User

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: User, state: FSMContext):
    """Handle /start command."""
    # Clear any active state
    await state.clear()

    # Check for deep link to plan
    if message.text:
        parts = message.text.split()
        if len(parts) > 1:
            param = parts[1]
            if param.startswith("plan_"):
                try:
                    plan_id = int(param.replace("plan_", ""))
                    # Show plan detail directly
                    from core.database.models import Plan
                    from core.database.engine import get_session
                    async with get_session() as session:
                        plan = await session.get(Plan, plan_id)
                    if plan:
                        from bot.keyboards.user_kb import UserKeyboards
                        await message.answer(
                            f"📋 <b>{plan.name}</b>\n💰 {plan.final_price:,} تومان",
                            reply_markup=UserKeyboards.plan_detail(plan_id),
                        )
                        return
                except (ValueError, Exception):
                    pass

    from core.services.bot_texts import get_text
    welcome_text = await get_text("welcome", name=db_user.full_name)

    await message.answer(welcome_text, reply_markup=UserKeyboards.main_menu())


@router.message(F.text == "👤 حساب کاربری")
async def show_profile(message: Message, db_user: User, state: FSMContext):
    """Show user profile."""
    await state.clear()

    profile_text = (
        f"👤 <b>حساب کاربری</b>\n\n"
        f"🆔 شناسه: <code>{db_user.telegram_id}</code>\n"
        f"👤 نام: {db_user.full_name}\n"
        f"📱 یوزرنیم: {db_user.mention}\n"
        f"🗓️ تاریخ عضویت: {db_user.created_at.strftime('%Y/%m/%d')}\n"
        f"🛒 تعداد خرید: {db_user.total_purchases}\n"
        f"💰 مجموع خرید: {db_user.total_spent:,} تومان\n"
        f"🔗 کد دعوت: <code>{db_user.referral_code}</code>\n"
        f"🌐 زبان: {'فارسی' if db_user.language == 'fa' else 'English'}"
    )

    await message.answer(profile_text)


@router.message(F.text == "⭐ باشگاه مشتریان")
async def show_loyalty_menu(message: Message, db_user: User, state: FSMContext):
    """Show loyalty menu from reply keyboard."""
    await state.clear()

    from sqlalchemy import select
    from core.database.engine import get_session
    from core.database.models.loyalty import UserLoyalty

    async with get_session() as session:
        stmt = select(UserLoyalty).where(UserLoyalty.user_id == db_user.id)
        result = await session.execute(stmt)
        loyalty = result.scalar_one_or_none()

    points = loyalty.available_points if loyalty else 0
    total = loyalty.total_points if loyalty else 0
    level = loyalty.level if loyalty else "bronze"

    level_names = {"bronze": "🥉 برنزی", "silver": "🥈 نقره‌ای", "gold": "🥇 طلایی", "diamond": "💎 الماسی"}

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎁 جوایز", callback_data="loyalty:rewards"))
    builder.row(InlineKeyboardButton(text="📜 تاریخچه امتیاز", callback_data="loyalty:history"))
    builder.row(InlineKeyboardButton(text="📊 نحوه کسب امتیاز", callback_data="loyalty:info"))

    await message.answer(
        f"⭐ <b>باشگاه مشتریان</b>\n\n"
        f"{level_names.get(level, '⭐')} سطح: <b>{level_names.get(level, level)}</b>\n"
        f"💎 امتیاز موجود: <b>{points:,}</b>\n"
        f"📊 مجموع امتیاز: {total:,}\n\n"
        f"💡 با هر خرید امتیاز کسب کنید و جوایز بگیرید!",
        reply_markup=builder.as_markup(),
    )


@router.message(F.text == "🏪 نمایندگی")
async def show_reseller_menu(message: Message, db_user: User, state: FSMContext):
    """Show reseller menu from reply keyboard."""
    await state.clear()

    from sqlalchemy import select
    from core.database.engine import get_session
    from core.database.models.reseller import Reseller, ResellerLevel

    async with get_session() as session:
        stmt = select(Reseller).where(Reseller.user_id == db_user.id)
        result = await session.execute(stmt)
        reseller = result.scalar_one_or_none()

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()

    if not reseller:
        builder.row(InlineKeyboardButton(text="📝 درخواست نمایندگی", callback_data="reseller:apply"))

        await message.answer(
            "🏪 <b>سیستم نمایندگی</b>\n\n"
            "شما هنوز نماینده نیستید.\n"
            "با ثبت درخواست نمایندگی، می‌توانید با تخفیف ویژه سرویس بخرید.\n\n"
            "✅ مزایا:\n"
            "• تخفیف ویژه روی تمام پلن‌ها\n"
            "• پنل مدیریت مشتریان\n"
            "• پشتیبانی اختصاصی",
            reply_markup=builder.as_markup(),
        )
    else:
        builder.row(InlineKeyboardButton(text="🛒 خرید برای مشتری", callback_data="reseller:buy"))
        builder.row(InlineKeyboardButton(text="💰 مالی", callback_data="reseller:finance"))

        await message.answer(
            f"🏪 <b>پنل نمایندگی</b>\n\n"
            f"🏷️ فروشگاه: {reseller.shop_name}\n"
            f"💰 موجودی: {reseller.balance:,} تومان\n"
            f"📊 کل فروش: {reseller.total_sales}",
            reply_markup=builder.as_markup(),
        )


@router.message(F.text == "📖 آموزش اتصال")
async def show_tutorial_menu(message: Message, state: FSMContext):
    """Show tutorial menu from reply keyboard."""
    await state.clear()

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🤖 اندروید", callback_data="tutorial:android"),
        InlineKeyboardButton(text="🍎 آیفون", callback_data="tutorial:ios"),
    )
    builder.row(
        InlineKeyboardButton(text="🖥️ ویندوز", callback_data="tutorial:windows"),
        InlineKeyboardButton(text="💻 مک", callback_data="tutorial:mac"),
    )

    await message.answer(
        "📖 <b>آموزش اتصال</b>\n\nپلتفرم خود را انتخاب کنید:",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "main:menu")
async def back_to_main(callback: CallbackQuery, db_user: User, state: FSMContext):
    """Back to main menu."""
    await state.clear()
    await callback.message.edit_text("🏠 منوی اصلی")
    await callback.message.answer("🏠 منوی اصلی", reply_markup=UserKeyboards.main_menu())
    await callback.answer()


@router.callback_query(F.data == "shop:back")
async def shop_back(callback: CallbackQuery, state: FSMContext):
    """Back from shop."""
    await state.clear()
    await callback.message.edit_text("🏠 منوی اصلی")
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Help command."""
    from core.services.bot_texts import get_text
    help_text = await get_text("help")
    await message.answer(help_text)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Cancel any active operation."""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer("❌ عملیات لغو شد.")
    else:
        await message.answer("ℹ️ عملیات فعالی وجود ندارد.")


@router.message(Command("id"))
async def cmd_id(message: Message):
    """Show user Telegram ID."""
    await message.answer(f"🆔 شناسه تلگرام شما: <code>{message.from_user.id}</code>")


@router.callback_query(F.data == "check_join")
async def check_join_callback(callback: CallbackQuery):
    """Re-check channel membership."""
    await callback.message.edit_text("✅ ممنون! حالا می‌توانید از ربات استفاده کنید.\n\nدستور /start را بزنید.")
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    """No-op callback for pagination info button."""
    await callback.answer()
