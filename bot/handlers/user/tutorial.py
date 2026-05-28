"""Connection tutorial handlers - send guides for each platform."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile

router = Router(name="tutorial")


TUTORIALS = {
    "android": {
        "title": "📱 آموزش اتصال در اندروید",
        "app_name": "v2rayNG",
        "steps": (
            "📱 <b>آموزش اتصال - اندروید (v2rayNG)</b>\n\n"
            "1️⃣ اپلیکیشن <b>v2rayNG</b> را از Google Play یا GitHub نصب کنید.\n\n"
            "2️⃣ لینک اشتراک (Subscription) خود را کپی کنید.\n\n"
            "3️⃣ در اپلیکیشن، روی آیکون ➕ بزنید.\n\n"
            "4️⃣ گزینه «Import config from clipboard» را انتخاب کنید.\n\n"
            "5️⃣ یا از منوی بالا «Subscription group setting» را باز کنید "
            "و لینک اشتراک را اضافه کنید.\n\n"
            "6️⃣ روی دکمه 🔄 بزنید تا کانفیگ‌ها بروزرسانی شوند.\n\n"
            "7️⃣ یک سرور انتخاب کنید و دکمه اتصال (▶️) را بزنید.\n\n"
            "✅ تمام! اکنون متصل هستید."
        ),
    },
    "ios": {
        "title": "🍎 آموزش اتصال در آیفون",
        "app_name": "Streisand / Hiddify",
        "steps": (
            "🍎 <b>آموزش اتصال - آیفون (Streisand)</b>\n\n"
            "1️⃣ اپلیکیشن <b>Streisand</b> یا <b>Hiddify</b> را از App Store نصب کنید.\n\n"
            "2️⃣ لینک اشتراک خود را کپی کنید.\n\n"
            "3️⃣ اپلیکیشن را باز کنید.\n\n"
            "4️⃣ روی ➕ بزنید و «Add from clipboard» را انتخاب کنید.\n\n"
            "5️⃣ یا به بخش Subscription بروید و لینک را اضافه کنید.\n\n"
            "6️⃣ یک سرور انتخاب کنید و Connect بزنید.\n\n"
            "7️⃣ اجازه VPN را تأیید کنید.\n\n"
            "✅ تمام! اکنون متصل هستید."
        ),
    },
    "windows": {
        "title": "🖥️ آموزش اتصال در ویندوز",
        "app_name": "v2rayN / Hiddify Next",
        "steps": (
            "🖥️ <b>آموزش اتصال - ویندوز (v2rayN)</b>\n\n"
            "1️⃣ نرم‌افزار <b>v2rayN</b> یا <b>Hiddify Next</b> را دانلود کنید.\n\n"
            "2️⃣ فایل را از حالت فشرده خارج کنید.\n\n"
            "3️⃣ برنامه را اجرا کنید (Run as Administrator).\n\n"
            "4️⃣ لینک اشتراک را کپی کنید.\n\n"
            "5️⃣ در برنامه: Subscription > Subscription Setting\n\n"
            "6️⃣ لینک را در فیلد URL وارد کنید و OK بزنید.\n\n"
            "7️⃣ روی Update بزنید تا سرورها لود شوند.\n\n"
            "8️⃣ یک سرور انتخاب کنید و Enter بزنید.\n\n"
            "9️⃣ از System Proxy روی «Set System Proxy» کلیک کنید.\n\n"
            "✅ تمام! اکنون متصل هستید."
        ),
    },
    "mac": {
        "title": "💻 آموزش اتصال در مک",
        "app_name": "V2Box / Hiddify Next",
        "steps": (
            "💻 <b>آموزش اتصال - مک (V2Box)</b>\n\n"
            "1️⃣ اپلیکیشن <b>V2Box</b> یا <b>Hiddify Next</b> را از App Store نصب کنید.\n\n"
            "2️⃣ لینک اشتراک خود را کپی کنید.\n\n"
            "3️⃣ اپلیکیشن را باز کنید.\n\n"
            "4️⃣ به بخش Subscription بروید.\n\n"
            "5️⃣ روی ➕ بزنید و لینک را Paste کنید.\n\n"
            "6️⃣ Save کنید و سرورها لود می‌شوند.\n\n"
            "7️⃣ یک سرور انتخاب و Connect بزنید.\n\n"
            "✅ تمام! اکنون متصل هستید."
        ),
    },
}


@router.callback_query(F.data.startswith("tutorial:"))
async def show_tutorial(callback: CallbackQuery):
    """Show connection tutorial for a platform."""
    platform = callback.data.split(":")[1]

    tutorial = TUTORIALS.get(platform)
    if not tutorial:
        await callback.answer("⚠️ آموزش یافت نشد.", show_alert=True)
        return

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()

    # Add download links
    if platform == "android":
        builder.row(
            InlineKeyboardButton(
                text="📥 دانلود v2rayNG",
                url="https://play.google.com/store/apps/details?id=com.v2ray.ang",
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="📥 دانلود Hiddify",
                url="https://play.google.com/store/apps/details?id=app.hiddify.com",
            )
        )
    elif platform == "ios":
        builder.row(
            InlineKeyboardButton(
                text="📥 دانلود Streisand",
                url="https://apps.apple.com/app/streisand/id6450534064",
            )
        )
    elif platform == "windows":
        builder.row(
            InlineKeyboardButton(
                text="📥 دانلود Hiddify Next",
                url="https://github.com/hiddify/hiddify-next/releases",
            )
        )
    elif platform == "mac":
        builder.row(
            InlineKeyboardButton(
                text="📥 دانلود Hiddify Next",
                url="https://github.com/hiddify/hiddify-next/releases",
            )
        )

    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="tutorial:menu")
    )

    await callback.message.edit_text(
        tutorial["steps"], reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data == "tutorial:menu")
async def tutorial_menu(callback: CallbackQuery):
    """Show tutorial platform selection."""
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
    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="main:menu"),
    )

    await callback.message.edit_text(
        "📖 <b>آموزش اتصال</b>\n\n"
        "پلتفرم خود را انتخاب کنید:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()
