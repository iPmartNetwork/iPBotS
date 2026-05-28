"""Auto-renewal system handlers."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select

from core.database.engine import get_session
from core.database.models import User, Subscription, SubscriptionStatus

router = Router(name="auto_renew")


@router.callback_query(F.data.startswith("sub:autorenew:toggle:"))
async def toggle_auto_renew(callback: CallbackQuery, db_user: User):
    """Toggle auto-renewal for a subscription."""
    sub_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        sub = await session.get(Subscription, sub_id)
        if not sub or sub.user_id != db_user.id:
            await callback.answer("⚠️ سرویس یافت نشد.", show_alert=True)
            return

        sub.auto_renew = not sub.auto_renew
        new_status = sub.auto_renew

    if new_status:
        await callback.answer(
            "✅ تمدید خودکار فعال شد.\n"
            "سرویس شما قبل از انقضا از کیف پول تمدید می‌شود.",
            show_alert=True,
        )
    else:
        await callback.answer("❌ تمدید خودکار غیرفعال شد.", show_alert=True)


@router.callback_query(F.data.startswith("sub:renew:"))
async def renew_subscription(callback: CallbackQuery, db_user: User):
    """Manually renew a subscription."""
    sub_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        from sqlalchemy.orm import selectinload

        stmt = (
            select(Subscription)
            .where(Subscription.id == sub_id)
            .where(Subscription.user_id == db_user.id)
            .options(selectinload(Subscription.plan))
        )
        result = await session.execute(stmt)
        sub = result.scalar_one_or_none()

    if not sub:
        await callback.answer("⚠️ سرویس یافت نشد.", show_alert=True)
        return

    if not sub.plan:
        await callback.answer("⚠️ پلن مرتبط یافت نشد.", show_alert=True)
        return

    plan = sub.plan

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"💰 پرداخت از کیف پول ({plan.final_price:,} ت)",
                    callback_data=f"renew:wallet:{sub_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💳 پرداخت آنلاین",
                    callback_data=f"renew:zarinpal:{sub_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔙 انصراف",
                    callback_data=f"sub:detail:{sub_id}",
                ),
            ],
        ]
    )

    text = (
        f"🔄 <b>تمدید سرویس</b>\n\n"
        f"📋 پلن: {plan.name}\n"
        f"📊 حجم: {plan.display_data}\n"
        f"⏱️ مدت: {plan.display_duration}\n"
        f"💰 مبلغ: <b>{plan.final_price:,}</b> تومان\n\n"
        f"روش پرداخت را انتخاب کنید:"
    )

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("renew:wallet:"))
async def renew_with_wallet(callback: CallbackQuery, db_user: User):
    """Renew subscription using wallet."""
    sub_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        from sqlalchemy.orm import selectinload
        from core.database.models import Wallet, WalletTransaction, TransactionType
        from core.database.models.server import PanelType
        from datetime import datetime, timezone, timedelta

        sub = await session.get(Subscription, sub_id)
        if not sub or sub.user_id != db_user.id:
            await callback.answer("⚠️ خطا.", show_alert=True)
            return

        plan_stmt = select(Subscription).where(Subscription.id == sub_id).options(
            selectinload(Subscription.plan)
        )
        plan_result = await session.execute(plan_stmt)
        sub_with_plan = plan_result.scalar_one()
        plan = sub_with_plan.plan

        if not plan:
            await callback.answer("⚠️ پلن یافت نشد.", show_alert=True)
            return

        # Check wallet
        wallet_stmt = select(Wallet).where(Wallet.user_id == db_user.id)
        wallet_result = await session.execute(wallet_stmt)
        wallet = wallet_result.scalar_one_or_none()

        if not wallet or wallet.balance < plan.final_price:
            await callback.answer(
                f"⚠️ موجودی کافی نیست.\n"
                f"موجودی: {wallet.balance if wallet else 0:,}\n"
                f"مورد نیاز: {plan.final_price:,}",
                show_alert=True,
            )
            return

        # Deduct from wallet
        wallet.balance -= plan.final_price
        wallet.total_spent += plan.final_price

        tx = WalletTransaction(
            wallet_id=wallet.id,
            transaction_type=TransactionType.PURCHASE,
            amount=plan.final_price,
            balance_after=wallet.balance,
            description=f"تمدید سرویس: {plan.name}",
            reference_id=f"renew_{sub_id}",
        )
        session.add(tx)

        # Extend subscription
        now = datetime.now(timezone.utc)
        if sub.expire_date > now:
            # Still active - extend from current expiry
            sub.expire_date = sub.expire_date + timedelta(days=plan.duration_days)
        else:
            # Expired - start fresh
            sub.start_date = now
            sub.expire_date = now + timedelta(days=plan.duration_days)

        sub.status = SubscriptionStatus.ACTIVE
        sub.is_active = True

        # Reset traffic if plan has limit
        if plan.data_limit_gb > 0:
            sub.data_limit_bytes = plan.data_limit_gb * 1024 * 1024 * 1024
            sub.used_traffic_bytes = 0

    # Update on panel
    from core.services.panel.xui import XUIService
    from core.services.panel.hiddify import HiddifyService
    from core.database.models import Server

    async with get_session() as session:
        server = await session.get(Server, sub.server_id)

    if server:
        if server.panel_type == PanelType.XUI:
            panel = XUIService(
                host=server.host, port=server.port,
                username=server.username, password=server.password,
                api_path=server.api_path,
            )
        else:
            panel = HiddifyService(
                host=server.host, port=server.port,
                username=server.username, password=server.password,
                hiddify_api_key=server.hiddify_api_key,
            )

        await panel.update_client(
            inbound_id=sub.inbound_id,
            client_id=sub.panel_client_id,
            email=sub.panel_email,
            data_limit_gb=plan.data_limit_gb,
            expire_days=plan.duration_days,
            enable=True,
        )

    await callback.message.edit_text(
        f"✅ <b>سرویس تمدید شد!</b>\n\n"
        f"📋 پلن: {plan.name}\n"
        f"📅 انقضای جدید: {sub.expire_date.strftime('%Y/%m/%d')}\n"
        f"💰 مبلغ: {plan.final_price:,} تومان (از کیف پول)"
    )
    await callback.answer("✅ تمدید موفق!")
