"""Persian (Farsi) locale strings."""

MESSAGES = {
    # General
    "welcome": "👋 سلام <b>{name}</b>!\n\n🚀 به ربات فروش VPN خوش آمدید.",
    "main_menu": "🏠 منوی اصلی",
    "back": "🔙 بازگشت",
    "cancel": "❌ انصراف",
    "confirm": "✅ تأیید",
    "error": "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.",
    "not_found": "⚠️ یافت نشد.",

    # Shop
    "shop_title": "🛒 فروشگاه",
    "shop_categories": "دسته‌بندی مورد نظر خود را انتخاب کنید:",
    "shop_no_plans": "⚠️ در حال حاضر سرویسی موجود نیست.",
    "shop_plan_detail": (
        "📋 <b>{name}</b>\n\n"
        "📊 حجم: {data}\n"
        "⏱️ مدت: {duration}\n"
        "👥 کاربر همزمان: {ip_limit}\n"
        "💰 قیمت: <b>{price}</b> تومان"
    ),

    # Wallet
    "wallet_title": "💰 کیف پول",
    "wallet_balance": "💵 موجودی: <b>{balance}</b> تومان",
    "wallet_charge_prompt": "مبلغ مورد نظر را به تومان وارد کنید:",
    "wallet_min_amount": "❌ حداقل مبلغ {min} تومان است.",
    "wallet_insufficient": "⚠️ موجودی کیف پول کافی نیست.",

    # Payment
    "payment_success": "✅ پرداخت با موفقیت انجام شد!",
    "payment_failed": "❌ پرداخت ناموفق بود.",
    "payment_pending": "⏳ در انتظار تأیید پرداخت...",
    "payment_card_info": (
        "💳 <b>اطلاعات کارت:</b>\n\n"
        "شماره کارت: <code>{card}</code>\n"
        "به نام: {holder}\n"
        "مبلغ: <b>{amount}</b> تومان"
    ),

    # Subscription
    "sub_created": "✅ سرویس شما فعال شد!",
    "sub_expired": "⏰ سرویس شما منقضی شده است.",
    "sub_traffic_ended": "📊 ترافیک سرویس شما تمام شده است.",
    "sub_expiring_soon": "⚠️ سرویس شما تا {days} روز دیگر منقضی می‌شود.",

    # Referral
    "referral_title": "👥 سیستم زیرمجموعه‌گیری",
    "referral_link": "🔗 لینک دعوت شما:\n<code>{link}</code>",
    "referral_bonus": "💰 پورسانت: {percent}% از هر خرید",
    "referral_withdraw_min": "⚠️ حداقل مبلغ برداشت {min} تومان است.",

    # Support
    "ticket_created": "✅ تیکت #{id} ایجاد شد.",
    "ticket_replied": "📩 تیکت #{id} پاسخ جدیدی دریافت کرد.",
    "ticket_closed": "🔒 تیکت #{id} بسته شد.",

    # Admin
    "admin_panel": "🛡️ پنل مدیریت",
    "admin_user_banned": "✅ کاربر مسدود شد.",
    "admin_payment_approved": "✅ پرداخت تأیید شد.",
    "admin_payment_rejected": "❌ پرداخت رد شد.",
    "admin_broadcast_done": "✅ ارسال پیام انبوه تمام شد.",
}
