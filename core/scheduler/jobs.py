"""Scheduled jobs for background tasks."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from bot.config import settings

scheduler = AsyncIOScheduler()


async def check_expired_subscriptions():
    """Check and disable expired subscriptions."""
    from core.database.engine import get_session
    from core.database.models import Subscription, SubscriptionStatus
    from sqlalchemy import select, update
    from datetime import datetime, timezone

    logger.info("Checking expired subscriptions...")

    async with get_session() as session:
        now = datetime.now(timezone.utc)

        # Find expired active subscriptions
        stmt = (
            select(Subscription)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .where(Subscription.expire_date < now)
        )
        result = await session.execute(stmt)
        expired = result.scalars().all()

        for sub in expired:
            sub.status = SubscriptionStatus.EXPIRED
            sub.is_active = False
            logger.info(f"Subscription {sub.id} expired for user {sub.user_id}")

            # TODO: Disable on panel
            # TODO: Notify user

        logger.info(f"Processed {len(expired)} expired subscriptions.")


async def check_traffic_limits():
    """Check subscriptions that exceeded traffic limit."""
    from core.database.engine import get_session
    from core.database.models import Subscription, SubscriptionStatus
    from sqlalchemy import select

    logger.info("Checking traffic limits...")

    async with get_session() as session:
        stmt = (
            select(Subscription)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .where(Subscription.data_limit_bytes > 0)
        )
        result = await session.execute(stmt)
        subs = result.scalars().all()

        for sub in subs:
            if sub.used_traffic_bytes >= sub.data_limit_bytes:
                sub.status = SubscriptionStatus.TRAFFIC_ENDED
                sub.is_active = False
                logger.info(f"Subscription {sub.id} traffic ended for user {sub.user_id}")


async def sync_traffic_from_panels():
    """Sync traffic usage from panels."""
    from core.database.engine import get_session
    from core.database.models import Subscription, Server, SubscriptionStatus
    from core.services.panel.xui import XUIService
    from core.services.panel.hiddify import HiddifyService
    from core.database.models.server import PanelType
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    logger.info("Syncing traffic from panels...")

    async with get_session() as session:
        stmt = (
            select(Subscription)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .options(selectinload(Subscription.server))
        )
        result = await session.execute(stmt)
        subs = result.scalars().all()

        for sub in subs:
            try:
                server = sub.server
                if not server:
                    continue

                if server.panel_type == PanelType.XUI:
                    service = XUIService(
                        host=server.host,
                        port=server.port,
                        username=server.username,
                        password=server.password,
                        api_path=server.api_path,
                    )
                else:
                    service = HiddifyService(
                        host=server.host,
                        port=server.port,
                        username=server.username,
                        password=server.password,
                        hiddify_api_key=server.hiddify_api_key,
                    )

                traffic = await service.get_client_traffic(sub.panel_email)
                if traffic:
                    sub.used_traffic_bytes = traffic["used"]

            except Exception as e:
                logger.error(f"Traffic sync error for sub {sub.id}: {e}")

    logger.info("Traffic sync completed.")


async def send_expiry_notifications():
    """Send notifications for subscriptions expiring soon."""
    from core.database.engine import get_session
    from core.database.models import Subscription, SubscriptionStatus
    from sqlalchemy import select
    from datetime import datetime, timezone, timedelta

    logger.info("Sending expiry notifications...")

    async with get_session() as session:
        now = datetime.now(timezone.utc)

        # Notify 3 days before expiry
        notify_before = now + timedelta(days=3)

        stmt = (
            select(Subscription)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .where(Subscription.expire_date <= notify_before)
            .where(Subscription.expire_date > now)
        )
        result = await session.execute(stmt)
        expiring = result.scalars().all()

        from bot.loader import bot
        from core.services.notification import NotificationService

        notifier = NotificationService(bot)
        for sub in expiring:
            days_left = (sub.expire_date - now).days
            await notifier.notify_subscription_expiring(sub.user_id, days_left)

    logger.info(f"Sent {len(expiring)} expiry notifications.")


async def process_auto_renewals():
    """Process auto-renewal for subscriptions about to expire."""
    from core.database.engine import get_session
    from core.database.models import (
        Subscription, SubscriptionStatus, Wallet, WalletTransaction,
        TransactionType, User, Server
    )
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from datetime import datetime, timezone, timedelta

    logger.info("Processing auto-renewals...")

    async with get_session() as session:
        now = datetime.now(timezone.utc)
        # Auto-renew 1 day before expiry
        renew_before = now + timedelta(days=1)

        stmt = (
            select(Subscription)
            .where(Subscription.status == SubscriptionStatus.ACTIVE)
            .where(Subscription.auto_renew == True)
            .where(Subscription.expire_date <= renew_before)
            .where(Subscription.expire_date > now)
            .options(selectinload(Subscription.plan))
        )
        result = await session.execute(stmt)
        subs_to_renew = result.scalars().all()

        renewed = 0
        for sub in subs_to_renew:
            if not sub.plan:
                continue

            # Check wallet balance
            wallet_stmt = select(Wallet).where(Wallet.user_id == sub.user_id)
            wallet_result = await session.execute(wallet_stmt)
            wallet = wallet_result.scalar_one_or_none()

            if not wallet or wallet.balance < sub.plan.final_price:
                # Not enough balance - notify user
                from bot.loader import bot
                try:
                    await bot.send_message(
                        sub.user_id,
                        f"⚠️ <b>تمدید خودکار ناموفق</b>\n\n"
                        f"موجودی کیف پول برای تمدید سرویس «{sub.plan.name}» کافی نیست.\n"
                        f"مبلغ مورد نیاز: {sub.plan.final_price:,} تومان\n"
                        f"موجودی فعلی: {wallet.balance if wallet else 0:,} تومان\n\n"
                        f"لطفاً کیف پول خود را شارژ کنید."
                    )
                except Exception:
                    pass
                continue

            # Deduct and renew
            wallet.balance -= sub.plan.final_price
            wallet.total_spent += sub.plan.final_price

            tx = WalletTransaction(
                wallet_id=wallet.id,
                transaction_type=TransactionType.PURCHASE,
                amount=sub.plan.final_price,
                balance_after=wallet.balance,
                description=f"تمدید خودکار: {sub.plan.name}",
                reference_id=f"autorenew_{sub.id}",
            )
            session.add(tx)

            # Extend subscription
            sub.expire_date = sub.expire_date + timedelta(days=sub.plan.duration_days)
            if sub.plan.data_limit_gb > 0:
                sub.data_limit_bytes = sub.plan.data_limit_gb * 1024 * 1024 * 1024
                sub.used_traffic_bytes = 0

            # Update on panel
            try:
                from core.services.panel.xui import XUIService
                from core.services.panel.hiddify import HiddifyService
                from core.services.panel.marzban import MarzbanService
                from core.database.models.server import PanelType

                server = await session.get(Server, sub.server_id) if sub.server_id else None
                if server:
                    if server.panel_type == PanelType.XUI:
                        panel_svc = XUIService(host=server.host, port=server.port,
                                              username=server.username, password=server.password,
                                              api_path=server.api_path)
                    elif server.panel_type == PanelType.MARZBAN:
                        panel_svc = MarzbanService(host=server.host, port=server.port,
                                                  username=server.username, password=server.password)
                    else:
                        panel_svc = HiddifyService(host=server.host, port=server.port,
                                                  username=server.username, password=server.password,
                                                  hiddify_api_key=server.hiddify_api_key)

                    await panel_svc.update_client(
                        inbound_id=sub.inbound_id,
                        client_id=sub.panel_client_id,
                        email=sub.panel_email,
                        data_limit_gb=sub.plan.data_limit_gb if sub.plan else None,
                        expire_days=sub.plan.duration_days if sub.plan else None,
                        enable=True,
                    )
            except Exception as e:
                logger.error(f"Auto-renew panel update failed for sub {sub.id}: {e}")

            renewed += 1

            # Notify user
            from bot.loader import bot
            try:
                await bot.send_message(
                    sub.user_id,
                    f"✅ <b>تمدید خودکار موفق</b>\n\n"
                    f"سرویس «{sub.plan.name}» تمدید شد.\n"
                    f"📅 انقضای جدید: {sub.expire_date.strftime('%Y/%m/%d')}\n"
                    f"💰 مبلغ: {sub.plan.final_price:,} تومان (از کیف پول)"
                )
            except Exception:
                pass

    logger.info(f"Auto-renewed {renewed} subscriptions.")


async def auto_backup():
    """Automatic database backup."""
    import subprocess
    import os
    from datetime import datetime

    if not settings.BACKUP_ENABLED:
        return

    logger.info("Running auto backup...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backups/backup_{timestamp}.sql"

    os.makedirs("backups", exist_ok=True)

    cmd = (
        f"pg_dump -h {settings.DB_HOST} -p {settings.DB_PORT} "
        f"-U {settings.DB_USER} -d {settings.DB_NAME} > {backup_file}"
    )

    try:
        env = os.environ.copy()
        env["PGPASSWORD"] = settings.DB_PASSWORD
        subprocess.run(cmd, shell=True, env=env, check=True)
        logger.info(f"Backup created: {backup_file}")

        # Send to Telegram
        if settings.BACKUP_CHAT_ID:
            from bot.loader import bot
            from aiogram.types import FSInputFile

            doc = FSInputFile(backup_file)
            await bot.send_document(
                settings.BACKUP_CHAT_ID,
                doc,
                caption=f"🗄️ پشتیبان خودکار\n📅 {timestamp}",
            )
    except Exception as e:
        logger.error(f"Backup failed: {e}")


async def check_server_health():
    """Check health of all servers."""
    from core.services.health_check import health_checker

    logger.info("Running health check...")
    results = await health_checker.check_all_servers()

    for result in results:
        if not result["is_online"]:
            await health_checker.notify_server_down(result)

    down_count = sum(1 for r in results if not r["is_online"])
    logger.info(f"Health check done: {len(results)} servers, {down_count} down")


async def send_daily_report():
    """Send daily report to admins."""
    from core.services.daily_report import report_service
    await report_service.send_daily_report()


async def send_weekly_report():
    """Send weekly report to admins."""
    from core.services.daily_report import report_service
    await report_service.send_weekly_report()


async def marketing_inactive_reminder():
    """Send marketing message to inactive users."""
    from core.services.marketing import marketing_service
    await marketing_service.send_inactive_reminder()


async def marketing_expired_offer():
    """Send offer to users with expired subscriptions."""
    from core.services.marketing import marketing_service
    await marketing_service.send_expired_offer()


async def marketing_first_purchase():
    """Nudge users who never purchased."""
    from core.services.marketing import marketing_service
    await marketing_service.send_first_purchase_nudge()


async def marketing_traffic_warning():
    """Warn users about high traffic usage."""
    from core.services.marketing import marketing_service
    await marketing_service.send_traffic_warning()


def start_scheduler():
    """Start the scheduler with all jobs."""
    # Check expired subscriptions every 30 minutes
    scheduler.add_job(
        check_expired_subscriptions,
        IntervalTrigger(minutes=30),
        id="check_expired",
        replace_existing=True,
    )

    # Sync traffic every 15 minutes
    scheduler.add_job(
        sync_traffic_from_panels,
        IntervalTrigger(minutes=15),
        id="sync_traffic",
        replace_existing=True,
    )

    # Check traffic limits every 20 minutes
    scheduler.add_job(
        check_traffic_limits,
        IntervalTrigger(minutes=20),
        id="check_traffic",
        replace_existing=True,
    )

    # Send expiry notifications every 6 hours
    scheduler.add_job(
        send_expiry_notifications,
        IntervalTrigger(hours=6),
        id="expiry_notifications",
        replace_existing=True,
    )

    # Process auto-renewals every 4 hours
    scheduler.add_job(
        process_auto_renewals,
        IntervalTrigger(hours=4),
        id="auto_renewals",
        replace_existing=True,
    )

    # Auto backup
    if settings.BACKUP_ENABLED:
        scheduler.add_job(
            auto_backup,
            IntervalTrigger(hours=settings.BACKUP_INTERVAL_HOURS),
            id="auto_backup",
            replace_existing=True,
        )

    # Health check every 5 minutes
    scheduler.add_job(
        check_server_health,
        IntervalTrigger(minutes=5),
        id="health_check",
        replace_existing=True,
    )

    # Daily report at 23:00
    from apscheduler.triggers.cron import CronTrigger

    scheduler.add_job(
        send_daily_report,
        CronTrigger(hour=23, minute=0),
        id="daily_report",
        replace_existing=True,
    )

    # Weekly report on Fridays at 22:00
    scheduler.add_job(
        send_weekly_report,
        CronTrigger(day_of_week="fri", hour=22, minute=0),
        id="weekly_report",
        replace_existing=True,
    )

    # Marketing: inactive users reminder (daily at 18:00)
    scheduler.add_job(
        marketing_inactive_reminder,
        CronTrigger(hour=18, minute=0),
        id="marketing_inactive",
        replace_existing=True,
    )

    # Marketing: expired offer (daily at 10:00)
    scheduler.add_job(
        marketing_expired_offer,
        CronTrigger(hour=10, minute=0),
        id="marketing_expired",
        replace_existing=True,
    )

    # Marketing: first purchase nudge (daily at 14:00)
    scheduler.add_job(
        marketing_first_purchase,
        CronTrigger(hour=14, minute=0),
        id="marketing_first_purchase",
        replace_existing=True,
    )

    # Marketing: traffic warning (every 6 hours)
    scheduler.add_job(
        marketing_traffic_warning,
        IntervalTrigger(hours=6),
        id="marketing_traffic",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with all jobs.")
