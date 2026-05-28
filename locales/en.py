"""English locale strings."""

MESSAGES = {
    # General
    "welcome": "👋 Hello <b>{name}</b>!\n\n🚀 Welcome to VPN Shop Bot.",
    "main_menu": "🏠 Main Menu",
    "back": "🔙 Back",
    "cancel": "❌ Cancel",
    "confirm": "✅ Confirm",
    "error": "❌ An error occurred. Please try again.",
    "not_found": "⚠️ Not found.",

    # Shop
    "shop_title": "🛒 Shop",
    "shop_categories": "Select a category:",
    "shop_no_plans": "⚠️ No plans available at the moment.",
    "shop_plan_detail": (
        "📋 <b>{name}</b>\n\n"
        "📊 Data: {data}\n"
        "⏱️ Duration: {duration}\n"
        "👥 Concurrent users: {ip_limit}\n"
        "💰 Price: <b>{price}</b>"
    ),

    # Wallet
    "wallet_title": "💰 Wallet",
    "wallet_balance": "💵 Balance: <b>{balance}</b>",
    "wallet_charge_prompt": "Enter the amount to charge:",
    "wallet_min_amount": "❌ Minimum amount is {min}.",
    "wallet_insufficient": "⚠️ Insufficient wallet balance.",

    # Payment
    "payment_success": "✅ Payment successful!",
    "payment_failed": "❌ Payment failed.",
    "payment_pending": "⏳ Waiting for payment confirmation...",
    "payment_card_info": (
        "💳 <b>Card Info:</b>\n\n"
        "Card Number: <code>{card}</code>\n"
        "Holder: {holder}\n"
        "Amount: <b>{amount}</b>"
    ),

    # Subscription
    "sub_created": "✅ Your service is now active!",
    "sub_expired": "⏰ Your service has expired.",
    "sub_traffic_ended": "📊 Your traffic has been used up.",
    "sub_expiring_soon": "⚠️ Your service expires in {days} days.",

    # Referral
    "referral_title": "👥 Referral System",
    "referral_link": "🔗 Your referral link:\n<code>{link}</code>",
    "referral_bonus": "💰 Commission: {percent}% of each purchase",
    "referral_withdraw_min": "⚠️ Minimum withdrawal is {min}.",

    # Support
    "ticket_created": "✅ Ticket #{id} created.",
    "ticket_replied": "📩 Ticket #{id} has a new reply.",
    "ticket_closed": "🔒 Ticket #{id} closed.",

    # Admin
    "admin_panel": "🛡️ Admin Panel",
    "admin_user_banned": "✅ User banned.",
    "admin_payment_approved": "✅ Payment approved.",
    "admin_payment_rejected": "❌ Payment rejected.",
    "admin_broadcast_done": "✅ Broadcast completed.",
}
