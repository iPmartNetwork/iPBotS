"""User keyboards."""

from typing import List, Optional

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


class UserKeyboards:
    """User keyboard builders."""

    @staticmethod
    def main_menu() -> ReplyKeyboardMarkup:
        """Main menu keyboard."""
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="🛒 خرید سرویس"),
            KeyboardButton(text="📦 سرویس‌های من"),
        )
        builder.row(
            KeyboardButton(text="💰 کیف پول"),
            KeyboardButton(text="👥 زیرمجموعه"),
        )
        builder.row(
            KeyboardButton(text="⭐ باشگاه مشتریان"),
            KeyboardButton(text="🏪 نمایندگی"),
        )
        builder.row(
            KeyboardButton(text="📞 پشتیبانی"),
            KeyboardButton(text="👤 حساب کاربری"),
        )
        builder.row(
            KeyboardButton(text="📖 آموزش اتصال"),
        )
        return builder.as_markup(resize_keyboard=True)

    @staticmethod
    def shop_categories(categories: list) -> InlineKeyboardMarkup:
        """Shop categories keyboard."""
        builder = InlineKeyboardBuilder()

        # Trial button
        builder.row(
            InlineKeyboardButton(
                text="🎁 تست رایگان",
                callback_data="shop:trial",
            )
        )

        for cat in categories:
            builder.row(
                InlineKeyboardButton(
                    text=f"{cat.icon} {cat.name}",
                    callback_data=f"shop:category:{cat.id}",
                )
            )

        # Custom plan
        builder.row(
            InlineKeyboardButton(
                text="🛠️ ساخت پلن سفارشی",
                callback_data="shop:custom",
            )
        )

        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="shop:back")
        )
        return builder.as_markup()

    @staticmethod
    def plan_list(plans: list) -> InlineKeyboardMarkup:
        """Plans list keyboard."""
        builder = InlineKeyboardBuilder()
        for plan in plans:
            price_text = f"{plan.final_price:,} تومان"
            if plan.discount_percent > 0:
                price_text += f" ({plan.discount_percent}% تخفیف)"
            builder.row(
                InlineKeyboardButton(
                    text=f"📋 {plan.name} | {plan.display_data} | {plan.display_duration} | {price_text}",
                    callback_data=f"shop:plan:{plan.id}",
                )
            )
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="shop:categories")
        )
        return builder.as_markup()

    @staticmethod
    def plan_detail(plan_id: int, has_discount_code: bool = True) -> InlineKeyboardMarkup:
        """Plan detail with purchase options."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="💳 پرداخت آنلاین (زرین‌پال)",
                callback_data=f"pay:zarinpal:{plan_id}",
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="💰 پرداخت از کیف پول",
                callback_data=f"pay:wallet:{plan_id}",
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🪙 پرداخت ارز دیجیتال",
                callback_data=f"pay:crypto:{plan_id}",
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="🏦 کارت به کارت",
                callback_data=f"pay:card2card:{plan_id}",
            )
        )
        if has_discount_code:
            builder.row(
                InlineKeyboardButton(
                    text="🎁 کد تخفیف دارم",
                    callback_data=f"discount:apply:{plan_id}",
                )
            )
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="shop:categories")
        )
        return builder.as_markup()

    @staticmethod
    def wallet_menu() -> InlineKeyboardMarkup:
        """Wallet menu keyboard."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="➕ شارژ کیف پول", callback_data="wallet:charge"),
        )
        builder.row(
            InlineKeyboardButton(
                text="📜 تاریخچه تراکنش‌ها", callback_data="wallet:history"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="💸 برداشت موجودی", callback_data="wallet:withdraw"
            ),
        )
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="main:menu")
        )
        return builder.as_markup()

    @staticmethod
    def subscription_list(subscriptions: list) -> InlineKeyboardMarkup:
        """User subscriptions list."""
        builder = InlineKeyboardBuilder()
        for sub in subscriptions:
            status_icon = "✅" if sub.is_active else "❌"
            builder.row(
                InlineKeyboardButton(
                    text=f"{status_icon} {sub.plan.name if sub.plan else 'تست رایگان'} | {sub.remaining_days} روز",
                    callback_data=f"sub:detail:{sub.id}",
                )
            )
        if not subscriptions:
            builder.row(
                InlineKeyboardButton(
                    text="🛒 خرید سرویس جدید", callback_data="shop:categories"
                )
            )
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="main:menu")
        )
        return builder.as_markup()

    @staticmethod
    def subscription_detail(sub_id: int, is_active: bool) -> InlineKeyboardMarkup:
        """Subscription detail actions."""
        builder = InlineKeyboardBuilder()
        if is_active:
            builder.row(
                InlineKeyboardButton(
                    text="📊 آمار مصرف", callback_data=f"sub:stats:{sub_id}"
                ),
                InlineKeyboardButton(
                    text="🔗 لینک اتصال", callback_data=f"sub:config:{sub_id}"
                ),
            )
            builder.row(
                InlineKeyboardButton(
                    text="📱 QR Code", callback_data=f"sub:qrcode:{sub_id}"
                ),
                InlineKeyboardButton(
                    text="🔄 تمدید", callback_data=f"sub:renew:{sub_id}"
                ),
            )
            builder.row(
                InlineKeyboardButton(
                    text="⬆️ ارتقا", callback_data=f"sub:upgrade:{sub_id}"
                ),
                InlineKeyboardButton(
                    text="🌍 تغییر سرور", callback_data=f"sub:change_server:{sub_id}"
                ),
            )
            builder.row(
                InlineKeyboardButton(
                    text="🔁 تمدید خودکار", callback_data=f"sub:autorenew:toggle:{sub_id}"
                ),
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text="🔄 خرید مجدد", callback_data=f"sub:rebuy:{sub_id}"
                ),
            )
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="sub:list")
        )
        return builder.as_markup()

    @staticmethod
    def referral_menu(referral_code: str) -> InlineKeyboardMarkup:
        """Referral menu."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="📋 کپی لینک دعوت",
                callback_data=f"ref:copy:{referral_code}",
            )
        )
        builder.row(
            InlineKeyboardButton(
                text="👥 لیست زیرمجموعه‌ها", callback_data="ref:list"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="💸 برداشت درآمد", callback_data="ref:withdraw"
            ),
        )
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="main:menu")
        )
        return builder.as_markup()

    @staticmethod
    def support_menu() -> InlineKeyboardMarkup:
        """Support menu."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="📝 ارسال تیکت جدید", callback_data="ticket:new"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="📋 تیکت‌های من", callback_data="ticket:list"
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text="❓ سوالات متداول", callback_data="support:faq"
            ),
        )
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="main:menu")
        )
        return builder.as_markup()

    @staticmethod
    def confirm_purchase(order_id: int) -> InlineKeyboardMarkup:
        """Confirm purchase keyboard."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="✅ تأیید و پرداخت", callback_data=f"order:confirm:{order_id}"
            ),
            InlineKeyboardButton(
                text="❌ انصراف", callback_data=f"order:cancel:{order_id}"
            ),
        )
        return builder.as_markup()

    @staticmethod
    def crypto_options(plan_id: int) -> InlineKeyboardMarkup:
        """Crypto payment options."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text="NowPayments", callback_data=f"pay:nowpay:{plan_id}"
            ),
            InlineKeyboardButton(
                text="Cryptomus", callback_data=f"pay:cryptomus:{plan_id}"
            ),
        )
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"shop:plan:{plan_id}")
        )
        return builder.as_markup()

    @staticmethod
    def back_button(callback_data: str = "main:menu") -> InlineKeyboardMarkup:
        """Simple back button."""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔙 بازگشت", callback_data=callback_data)
        )
        return builder.as_markup()
