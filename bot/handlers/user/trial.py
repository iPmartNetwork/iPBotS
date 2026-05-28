"""Free trial handlers."""

from datetime import datetime, timezone, timedelta

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, func

from bot.keyboards.user_kb import UserKeyboards
from core.database.engine import get_session
from core.database.models import (
    User,
    Server,
    Subscription,
    SubscriptionStatus,
)
from core.database.models.trial import TrialConfig, TrialUsage
from core.database.models.server import PanelType
from core.services.panel.xui import XUIService
from core.services.panel.hiddify import HiddifyService

router = Router(name="trial")


@router.callback_query(F.data == "shop:trial")
async def request_trial(callback: CallbackQuery, db_user: User):
    """Request a free trial."""
    async with get_session() as session:
        # Check trial config
        config_stmt = select(TrialConfig).where(TrialConfig.is_active == True)
        config_result = await session.execute(config_stmt)
        trial_config = config_result.scalar_one_or_none()

        if not trial_config:
            await callback.answer("⚠️ تست رایگان در حال حاضر غیرفعال است.", show_alert=True)
            return

        # Check if user already used trial
        usage_count = await session.scalar(
            select(func.count(TrialUsage.id)).where(
                TrialUsage.user_id == db_user.id
            )
        )

        if usage_count >= trial_config.max_trials_per_user:
            await callback.answer(
                "⚠️ شما قبلاً از تست رایگان استفاده کرده‌اید.", show_alert=True
            )
            return

        # Get server
        server = None
        if trial_config.server_id:
            server = await session.get(Server, trial_config.server_id)
        else:
            stmt = select(Server).where(Server.is_active == True, Server.is_default == True)
            result = await session.execute(stmt)
            server = result.scalar_one_or_none()

        if not server:
            await callback.answer("⚠️ سروری در دسترس نیست.", show_alert=True)
            return

        # Create client on panel
        email = f"trial_{db_user.telegram_id}_{int(datetime.now().timestamp())}"
        expire_hours = trial_config.duration_hours

        if server.panel_type == PanelType.XUI:
            panel = XUIService(
                host=server.host,
                port=server.port,
                username=server.username,
                password=server.password,
                api_path=server.api_path,
            )
        else:
            panel = HiddifyService(
                host=server.host,
                port=server.port,
                username=server.username,
                password=server.password,
                hiddify_api_key=server.hiddify_api_key,
            )

        # Convert hours to days for panel (minimum 1 day)
        expire_days = max(1, expire_hours // 24)

        client = await panel.add_client(
            inbound_id=trial_config.inbound_id,
            email=email,
            data_limit_gb=trial_config.data_limit_gb,
            expire_days=expire_days,
            ip_limit=trial_config.ip_limit,
        )

        if not client:
            await callback.answer("❌ خطا در ایجاد سرویس تست.", show_alert=True)
            return

        # Get subscription URL
        sub_url = await panel.get_subscription_url(client.client_id)

        # Save subscription
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            user_id=db_user.id,
            plan_id=None,
            server_id=server.id,
            panel_client_id=client.client_id,
            panel_email=email,
            inbound_id=trial_config.inbound_id,
            subscription_url=sub_url,
            data_limit_bytes=trial_config.data_limit_gb * 1024 * 1024 * 1024,
            ip_limit=trial_config.ip_limit,
            start_date=now,
            expire_date=now + timedelta(hours=expire_hours),
            status=SubscriptionStatus.ACTIVE,
        )
        session.add(subscription)
        await session.flush()

        # Record trial usage
        trial_usage = TrialUsage(
            user_id=db_user.id,
            subscription_id=subscription.id,
            used_at=now,
        )
        session.add(trial_usage)

    # Send success message
    success_text = (
        f"🎉 <b>سرویس تست رایگان فعال شد!</b>\n\n"
        f"📊 حجم: {trial_config.data_limit_gb} GB\n"
        f"⏱️ مدت: {expire_hours} ساعت\n"
        f"🖥️ سرور: {server.flag} {server.name}\n\n"
    )

    if sub_url:
        success_text += f"🔗 <b>لینک اشتراک:</b>\n<code>{sub_url}</code>\n\n"

    success_text += (
        "📱 لینک بالا را در اپلیکیشن V2Ray وارد کنید.\n\n"
        "💡 برای خرید سرویس کامل از منوی «خرید سرویس» اقدام کنید."
    )

    await callback.message.edit_text(success_text)
    await callback.answer("✅ سرویس تست فعال شد!")
