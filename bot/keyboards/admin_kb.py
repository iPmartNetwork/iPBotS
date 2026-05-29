"""Admin keyboards."""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


class AdminKeyboards:
    """Admin keyboard builders."""

    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Admin main menu."""
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="📊 داشبورد"),
            KeyboardButton(text="👥 کاربران"),
        )
        builder.row(
            KeyboardButton(text="🖥️ سرورها"),
            KeyboardButton(text="📋 پلن‌ها"),
        )
        builder.row(
            KeyboardButton(text="💳 پرداخت‌ها"),
            KeyboardButton(text="🎁 تخفیف‌ها"),
        )
        builder.row(
            KeyboardButton(text="📢 ارسال پیام"),
            KeyboardButton(text="🎫 تیکت‌ها"),
        )
        builder.row(
            KeyboardButton(text="⚙️ تنظیمات"),
            KeyboardButton(text="🗄️ پشتیبان‌گیری"),
        )
        builder.row(
            KeyboardButton(text="🔙 منوی کاربری"),
        )
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def dashboard() -> InlineKeyboardMarkup:
        """Dashboard actions."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔄 بروزرسانی", callback_data="admin:dashboard:refresh"),
        )
        builder.row(
            InlineKeyboardButton(
                text="📈 گزارش روزانه", callback_data="admin:report:daily"
            ),
            InlineKeyboardButton(
                text="📊 گزارش ماهانه", callback_data="admin:report:monthly"
            ),
        )
        return builder.as_markup()

    @staticmethod
    def user_management(user_id: int) -> InlineKeyboardMarkup:
        """User management actions."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="📦 سرویس‌ها", callback_data=f"admin:user:subs:{user_id}"
            ),
            InlineKeyboardButton(
                text="💰 کیف پول", callback_data=f"admin:user:wallet:{user_id}"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="➕ شارژ کیف پول", callback_data=f"admin:user:credit:{user_id}"
            ),
            InlineKeyboardButton(
                text="🎁 هدیه سرویس", callback_data=f"admin:user:gift:{user_id}"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="🚫 مسدود", callback_data=f"admin:user:ban:{user_id}"
            ),
            InlineKeyboardButton(
                text="✅ رفع مسدودی", callback_data=f"admin:user:unban:{user_id}"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="📩 ارسال پیام", callback_data=f"admin:user:msg:{user_id}"
            ),
        )
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:users:list")
        )
        return builder.as_markup()

    @staticmethod
    def server_list(servers: list) -> InlineKeyboardMarkup:
        """Server list keyboard."""
        builder = InlineKeyboardBuilder()
        for server in servers:
            status = "🟢" if server.is_active else "🔴"
            builder.row(
                InlineKeyboardButton(
                    text=f"{status} {server.flag} {server.name}",
                    callback_data=f"admin:server:detail:{server.id}",
                )
            )
        builder.row(
            InlineKeyboardButton(
                text="➕ افزودن سرور", callback_data="admin:server:add"
            )
        )
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:menu")
        )
        return builder.as_markup()

    @staticmethod
    def server_detail(server_id: int) -> InlineKeyboardMarkup:
        """Server detail actions."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="✏️ ویرایش", callback_data=f"admin:server:edit:{server_id}"
            ),
            InlineKeyboardButton(
                text="🔄 تست اتصال", callback_data=f"admin:server:test:{server_id}"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="📊 وضعیت", callback_data=f"admin:server:status:{server_id}"
            ),
            InlineKeyboardButton(
                text="🗑️ حذف", callback_data=f"admin:server:delete:{server_id}"
            ),
        )
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:servers:list")
        )
        return builder.as_markup()

    @staticmethod
    def plan_management() -> InlineKeyboardMarkup:
        """Plan management menu."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="📋 لیست پلن‌ها", callback_data="admin:plans:list"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="➕ پلن جدید", callback_data="admin:plan:add"
            ),
            InlineKeyboardButton(
                text="📁 دسته‌بندی‌ها", callback_data="admin:categories:list"
            ),
        )
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:menu")
        )
        return builder.as_markup()

    @staticmethod
    def payment_pending(payment_id: int) -> InlineKeyboardMarkup:
        """Pending payment actions (for card2card)."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="✅ تأیید پرداخت", callback_data=f"admin:pay:approve:{payment_id}"
            ),
            InlineKeyboardButton(
                text="❌ رد پرداخت", callback_data=f"admin:pay:reject:{payment_id}"
            ),
        )
        return builder.as_markup()

    @staticmethod
    def broadcast_options() -> InlineKeyboardMarkup:
        """Broadcast message options."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="📢 ارسال به همه", callback_data="admin:broadcast:all"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="👥 ارسال به فعال‌ها", callback_data="admin:broadcast:active"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="📋 ارسال به دسته خاص", callback_data="admin:broadcast:select"
            ),
        )
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:menu")
        )
        return builder.as_markup()

    @staticmethod
    def discount_management() -> InlineKeyboardMarkup:
        """Discount management menu."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="📋 لیست کدها", callback_data="admin:discount:list"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="➕ کد جدید", callback_data="admin:discount:add"
            ),
            InlineKeyboardButton(
                text="🎁 گیفت کارت", callback_data="admin:giftcard:add"
            ),
        )
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:menu")
        )
        return builder.as_markup()

    @staticmethod
    def settings_menu() -> InlineKeyboardMarkup:
        """Settings menu."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="💳 درگاه‌های پرداخت", callback_data="admin:settings:payment"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="👥 مدیریت ادمین‌ها", callback_data="admin:settings:admins"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="📝 متن‌ها و پیام‌ها", callback_data="admin:settings:texts"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="🔔 اعلان‌ها", callback_data="admin:settings:notifications"
            ),
        )
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin:menu")
        )
        return builder.as_markup()

    @staticmethod
    def confirm_action(action: str, target_id: int) -> InlineKeyboardMarkup:
        """Generic confirm/cancel keyboard."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="✅ تأیید", callback_data=f"admin:confirm:{action}:{target_id}"
            ),
            InlineKeyboardButton(
                text="❌ انصراف", callback_data=f"admin:cancel:{action}:{target_id}"
            ),
        )
        return builder.as_markup()
