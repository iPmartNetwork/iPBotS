"""Bot text customization service - read/write customizable texts."""

from typing import Optional, Dict
from sqlalchemy import select
from loguru import logger

from core.database.engine import get_session
from core.database.models.bot_text import BotText

# Default texts (fallback if not in DB)
DEFAULT_TEXTS: Dict[str, dict] = {
    # Start & General
    "welcome": {
        "value": "👋 سلام <b>{name}</b>!\n\n🚀 به ربات فروش VPN خوش آمدید.\n\nاز منوی زیر می‌توانید سرویس مورد نظر خود را خریداری کنید.\n\n📌 در صورت نیاز به راهنمایی، از بخش پشتیبانی استفاده کنید.\n\n<i>© iPmart Network</i>",
        "description": "پیام خوش‌آمدگویی",
        "category": "general",
    },
    "help": {
        "value": "📖 <b>راهنمای ربات</b>\n\n🛒 <b>خرید سرویس</b> - مشاهده و خرید پلن‌های VPN\n📦 <b>سرویس‌های من</b> - مدیریت سرویس‌های فعال\n💰 <b>کیف پول</b> - شارژ و مدیریت موجودی\n👥 <b>زیرمجموعه</b> - لینک دعوت و درآمد\n📞 <b>پشتیبانی</b> - ارسال تیکت\n👤 <b>حساب کاربری</b> - اطلاعات حساب\n\n💡 برای شروع خرید، روی «خرید سرویس» کلیک کنید.",
        "description": "متن راهنما",
        "category": "general",
    },
    # Shop
    "shop_title": {
        "value": "🛒 <b>فروشگاه</b>\n\nدسته‌بندی مورد نظر خود را انتخاب کنید:",
        "description": "عنوان فروشگاه",
        "category": "shop",
    },
    "shop_empty": {
        "value": "⚠️ در حال حاضر سرویسی موجود نیست.",
        "description": "فروشگاه خالی",
        "category": "shop",
    },
    "purchase_success": {
        "value": "✅ <b>سرویس شما فعال شد!</b>\n\n📋 پلن: {plan_name}\n📊 حجم: {data}\n⏱️ مدت: {duration}\n🖥️ سرور: {server}\n\n🔗 <b>لینک اشتراک:</b>\n<code>{sub_url}</code>\n\n📱 لینک بالا را در اپلیکیشن V2Ray خود وارد کنید.",
        "description": "پیام موفقیت خرید",
        "category": "shop",
    },
    # Wallet
    "wallet_title": {
        "value": "💰 <b>کیف پول</b>\n\n💵 موجودی: <b>{balance}</b> تومان\n📥 مجموع واریز: {deposited} تومان\n📤 مجموع خرید: {spent} تومان",
        "description": "عنوان کیف پول",
        "category": "wallet",
    },
    # Support
    "support_title": {
        "value": "📞 <b>پشتیبانی</b>\n\nاز طریق سیستم تیکت می‌توانید سوالات و مشکلات خود را مطرح کنید.",
        "description": "عنوان پشتیبانی",
        "category": "support",
    },
    "ticket_created": {
        "value": "✅ <b>تیکت #{ticket_id} ایجاد شد</b>\n\n📌 موضوع: {subject}\n\nپاسخ تیکت شما به زودی ارسال خواهد شد.",
        "description": "پیام ایجاد تیکت",
        "category": "support",
    },
    # Referral
    "referral_title": {
        "value": "👥 <b>سیستم زیرمجموعه‌گیری</b>\n\n🔗 لینک دعوت شما:\n<code>{link}</code>\n\n👥 تعداد زیرمجموعه‌ها: {count}\n💰 درآمد کل: {earnings} تومان\n📊 درصد پورسانت: {percent}%\n\n💡 با اشتراک لینک دعوت، از هر خرید زیرمجموعه‌ها {percent}% پورسانت دریافت کنید.",
        "description": "متن زیرمجموعه",
        "category": "referral",
    },
    # Forced Join
    "forced_join": {
        "value": "⚠️ <b>عضویت اجباری</b>\n\nبرای استفاده از ربات، ابتدا در کانال‌های زیر عضو شوید:",
        "description": "پیام جوین اجباری",
        "category": "general",
    },
    # Anti-spam
    "antispam_warning": {
        "value": "🚫 <b>ضد اسپم</b>\n\nلطفاً کمی صبر کنید و دوباره تلاش کنید.",
        "description": "پیام ضد اسپم",
        "category": "general",
    },
    # Services
    "no_services": {
        "value": "📦 <b>سرویس‌های من</b>\n\nشما هنوز سرویسی خریداری نکرده‌اید.\nاز بخش «خرید سرویس» اقدام کنید.",
        "description": "بدون سرویس",
        "category": "services",
    },
}

# In-memory cache
_text_cache: Dict[str, str] = {}
_cache_loaded: bool = False


async def load_texts_cache():
    """Load all texts from DB into memory cache."""
    global _text_cache, _cache_loaded
    try:
        async with get_session() as session:
            stmt = select(BotText)
            result = await session.execute(stmt)
            texts = result.scalars().all()

            _text_cache = {t.key: t.value for t in texts}
            _cache_loaded = True
    except Exception as e:
        logger.error(f"Failed to load texts cache: {e}")
        _cache_loaded = False


async def get_text(key: str, **kwargs) -> str:
    """Get a customizable text by key with variable substitution.

    Falls back to DEFAULT_TEXTS if not in DB.
    Supports {variable} substitution via kwargs.
    """
    global _cache_loaded

    # Load cache on first call
    if not _cache_loaded:
        await load_texts_cache()

    # Try cache first
    text = _text_cache.get(key)

    # Fallback to defaults
    if text is None:
        default = DEFAULT_TEXTS.get(key)
        if default:
            text = default["value"]
        else:
            text = key  # Return key itself as last resort

    # Substitute variables
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            pass  # Return text without substitution if error

    return text


async def set_text(key: str, value: str) -> bool:
    """Set/update a text in the database and cache."""
    global _text_cache

    try:
        async with get_session() as session:
            stmt = select(BotText).where(BotText.key == key)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.value = value
            else:
                default = DEFAULT_TEXTS.get(key, {})
                new_text = BotText(
                    key=key,
                    value=value,
                    description=default.get("description", ""),
                    category=default.get("category", "general"),
                )
                session.add(new_text)

        # Update cache
        _text_cache[key] = value
        return True
    except Exception as e:
        logger.error(f"Failed to set text '{key}': {e}")
        return False


async def reset_text(key: str) -> bool:
    """Reset a text to its default value."""
    default = DEFAULT_TEXTS.get(key)
    if not default:
        return False

    return await set_text(key, default["value"])


def get_all_text_keys() -> Dict[str, dict]:
    """Get all available text keys with their descriptions."""
    return DEFAULT_TEXTS
