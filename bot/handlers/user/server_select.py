"""Server selection and location change handlers."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select

from core.database.engine import get_session
from core.database.models import User, Server, Subscription, SubscriptionStatus
from core.database.models.server_monitoring import ServerStatus

router = Router(name="server_select")


@router.callback_query(F.data.startswith("server:select:"))
async def show_available_servers(callback: CallbackQuery, db_user: User):
    """Show available servers for selection."""
    plan_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        stmt = (
            select(Server)
            .where(Server.is_active == True)
            .order_by(Server.location)
        )
        result = await session.execute(stmt)
        servers = result.scalars().all()

    if not servers:
        await callback.answer("⚠️ سروری در دسترس نیست.", show_alert=True)
        return

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()

    text = "🌍 <b>انتخاب سرور</b>\n\nسرور مورد نظر خود را انتخاب کنید:\n\n"

    for server in servers:
        # Calculate load
        load_percent = 0
        if server.max_users > 0:
            load_percent = int((server.current_users / server.max_users) * 100)

        load_bar = _get_load_indicator(load_percent)
        status = "🟢" if not server.is_full else "🔴"

        text += (
            f"{status} {server.flag} <b>{server.name}</b>\n"
            f"   📍 {server.location} | {load_bar} {load_percent}%\n\n"
        )

        if not server.is_full:
            builder.row(
                InlineKeyboardButton(
                    text=f"{server.flag} {server.name} ({server.location})",
                    callback_data=f"buy:server:{plan_id}:{server.id}",
                )
            )

    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"shop:plan:{plan_id}")
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("sub:change_server:"))
async def change_server(callback: CallbackQuery, db_user: User):
    """Change server/location for existing subscription."""
    sub_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        sub = await session.get(Subscription, sub_id)
        if not sub or sub.user_id != db_user.id:
            await callback.answer("⚠️ سرویس یافت نشد.", show_alert=True)
            return

        if sub.status != SubscriptionStatus.ACTIVE:
            await callback.answer("⚠️ فقط سرویس‌های فعال قابل تغییر هستند.", show_alert=True)
            return

        # Get available servers
        stmt = (
            select(Server)
            .where(Server.is_active == True)
            .where(Server.id != sub.server_id)
        )
        result = await session.execute(stmt)
        servers = result.scalars().all()

    if not servers:
        await callback.answer("⚠️ سرور دیگری در دسترس نیست.", show_alert=True)
        return

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()

    text = "🔄 <b>تغییر سرور</b>\n\nسرور جدید را انتخاب کنید:\n\n"

    for server in servers:
        if not server.is_full:
            builder.row(
                InlineKeyboardButton(
                    text=f"{server.flag} {server.name}",
                    callback_data=f"sub:migrate:{sub_id}:{server.id}",
                )
            )

    builder.row(
        InlineKeyboardButton(text="🔙 انصراف", callback_data=f"sub:detail:{sub_id}")
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("sub:migrate:"))
async def migrate_subscription(callback: CallbackQuery, db_user: User):
    """Migrate subscription to new server."""
    parts = callback.data.split(":")
    sub_id = int(parts[2])
    new_server_id = int(parts[3])

    async with get_session() as session:
        from sqlalchemy.orm import selectinload

        sub = await session.get(Subscription, sub_id)
        if not sub or sub.user_id != db_user.id:
            await callback.answer("⚠️ خطا.", show_alert=True)
            return

        old_server = await session.get(Server, sub.server_id)
        new_server = await session.get(Server, new_server_id)

        if not new_server or new_server.is_full:
            await callback.answer("⚠️ سرور انتخابی در دسترس نیست.", show_alert=True)
            return

    await callback.message.edit_text(
        f"🔄 <b>در حال انتقال...</b>\n\n"
        f"از: {old_server.flag} {old_server.name}\n"
        f"به: {new_server.flag} {new_server.name}\n\n"
        f"⏳ لطفاً صبر کنید..."
    )

    # Delete from old server, create on new server
    from core.services.panel.xui import XUIService
    from core.services.panel.hiddify import HiddifyService
    from core.database.models.server import PanelType

    # Delete from old
    if old_server.panel_type == PanelType.XUI:
        old_panel = XUIService(
            host=old_server.host, port=old_server.port,
            username=old_server.username, password=old_server.password,
            api_path=old_server.api_path,
        )
    else:
        old_panel = HiddifyService(
            host=old_server.host, port=old_server.port,
            username=old_server.username, password=old_server.password,
            hiddify_api_key=old_server.hiddify_api_key,
        )

    await old_panel.delete_client(sub.inbound_id, sub.panel_client_id)

    # Create on new
    if new_server.panel_type == PanelType.XUI:
        new_panel = XUIService(
            host=new_server.host, port=new_server.port,
            username=new_server.username, password=new_server.password,
            api_path=new_server.api_path,
        )
    else:
        new_panel = HiddifyService(
            host=new_server.host, port=new_server.port,
            username=new_server.username, password=new_server.password,
            hiddify_api_key=new_server.hiddify_api_key,
        )

    remaining_days = sub.remaining_days
    remaining_gb = int(sub.remaining_traffic_gb) if sub.data_limit_bytes > 0 else 0

    client = await new_panel.add_client(
        inbound_id=sub.inbound_id,
        email=sub.panel_email,
        data_limit_gb=remaining_gb,
        expire_days=remaining_days,
        ip_limit=sub.ip_limit,
    )

    if client:
        # Update subscription
        sub_url = await new_panel.get_subscription_url(client.client_id)

        async with get_session() as session:
            sub_obj = await session.get(Subscription, sub_id)
            sub_obj.server_id = new_server_id
            sub_obj.panel_client_id = client.client_id
            sub_obj.subscription_url = sub_url

        await callback.message.edit_text(
            f"✅ <b>انتقال موفق!</b>\n\n"
            f"🖥️ سرور جدید: {new_server.flag} {new_server.name}\n\n"
            f"🔗 لینک جدید:\n<code>{sub_url}</code>\n\n"
            f"⚠️ لطفاً لینک جدید را در اپلیکیشن خود جایگزین کنید."
        )
    else:
        await callback.message.edit_text(
            "❌ خطا در انتقال. لطفاً با پشتیبانی تماس بگیرید."
        )

    await callback.answer()


def _get_load_indicator(percent: int) -> str:
    """Get load indicator emoji."""
    if percent < 30:
        return "🟢"
    elif percent < 60:
        return "🟡"
    elif percent < 85:
        return "🟠"
    else:
        return "🔴"
