"""Start and main menu handlers."""

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards.user_kb import UserKeyboards
from bot.config import settings
from core.database.models import User

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, db_user: User):
    """Handle /start command."""
    welcome_text = (
        f"👋 سلام <b>{db_user.full_name}</b>!\n\n"
        f"🚀 به ربات فروش VPN خوش آمدید.\n\n"
        f"از منوی زیر می‌توانید سرویس مورد نظر خود را خریداری کنید.\n\n"
        f"📌 در صورت نیاز به راهنمایی، از بخش پشتیبانی استفاده کنید.\n\n"
        f"<i>© iPmart Network</i>"
    )

    await message.answer(welcome_text, reply_markup=UserKeyboards.main_menu())


@router.message(F.text == "👤 حساب کاربری")
async def show_profile(message: Message, db_user: User):
    """Show user profile."""
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


@router.callback_query(F.data == "main:menu")
async def back_to_main(callback: CallbackQuery, db_user: User):
    """Back to main menu."""
    await callback.message.delete()
    await callback.message.answer(
        "🏠 منوی اصلی", reply_markup=UserKeyboards.main_menu()
    )
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Help command."""
    help_text = (
        "📖 <b>راهنمای ربات</b>\n\n"
        "🛒 <b>خرید سرویس</b> - مشاهده و خرید پلن‌های VPN\n"
        "📦 <b>سرویس‌های من</b> - مدیریت سرویس‌های فعال\n"
        "💰 <b>کیف پول</b> - شارژ و مدیریت موجودی\n"
        "👥 <b>زیرمجموعه</b> - لینک دعوت و درآمد\n"
        "📞 <b>پشتیبانی</b> - ارسال تیکت\n"
        "👤 <b>حساب کاربری</b> - اطلاعات حساب\n\n"
        "💡 برای شروع خرید، روی «خرید سرویس» کلیک کنید."
    )
    await message.answer(help_text)


@router.message(Command("id"))
async def cmd_id(message: Message):
    """Show user Telegram ID."""
    await message.answer(f"🆔 شناسه تلگرام شما: <code>{message.from_user.id}</code>")
