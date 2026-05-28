"""Admin server connection test handler."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select

from bot.filters.admin import AdminFilter
from core.database.engine import get_session
from core.database.models import Server
from core.database.models.server import PanelType
from core.services.panel.xui import XUIService
from core.services.panel.hiddify import HiddifyService
from core.services.panel.marzban import MarzbanService
from core.services.health_check import health_checker

router = Router(name="admin_test_connection")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.callback_query(F.data.startswith("admin:server:fulltest:"))
async def full_server_test(callback: CallbackQuery):
    """Run comprehensive server test."""
    server_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        server = await session.get(Server, server_id)

    if not server:
        await callback.answer("⚠️ سرور یافت نشد.", show_alert=True)
        return

    await callback.message.edit_text(
        f"🔄 <b>تست جامع سرور: {server.name}</b>\n\n"
        f"⏳ در حال بررسی..."
    )

    results = []

    # Test 1: Ping/Connection
    health_result = await health_checker.check_server(server)
    if health_result["is_online"]:
        results.append(f"✅ اتصال: موفق ({health_result['ping_ms']}ms)")
    else:
        results.append(f"❌ اتصال: ناموفق ({health_result.get('error', 'Unknown')})")
        await callback.message.edit_text(
            f"🔴 <b>تست سرور: {server.name}</b>\n\n" + "\n".join(results)
        )
        return

    # Test 2: Login
    if server.panel_type == PanelType.XUI:
        panel = XUIService(
            host=server.host, port=server.port,
            username=server.username, password=server.password,
            api_path=server.api_path,
        )
    elif server.panel_type == PanelType.HIDDIFY:
        panel = HiddifyService(
            host=server.host, port=server.port,
            username=server.username, password=server.password,
            hiddify_api_key=server.hiddify_api_key,
        )
    else:
        panel = MarzbanService(
            host=server.host, port=server.port,
            username=server.username, password=server.password,
        )

    login_ok = await panel.login()
    if login_ok:
        results.append("✅ ورود: موفق")
    else:
        results.append("❌ ورود: ناموفق (یوزر/پسورد اشتباه؟)")
        await callback.message.edit_text(
            f"🟡 <b>تست سرور: {server.name}</b>\n\n" + "\n".join(results)
        )
        return

    # Test 3: Get Inbounds
    inbounds = await panel.get_inbounds()
    if inbounds:
        results.append(f"✅ اینباندها: {len(inbounds)} عدد")
        for ib in inbounds[:5]:
            results.append(f"   • {ib.remark} ({ib.protocol}) - Port {ib.port}")
    else:
        results.append("⚠️ اینباند: هیچ اینباندی یافت نشد")

    # Test 4: Server capacity
    results.append(f"\n📊 <b>وضعیت:</b>")
    results.append(f"   👥 کاربران: {server.current_users}/{server.max_users or '♾️'}")
    results.append(f"   📍 لوکیشن: {server.flag} {server.location}")
    results.append(f"   🔌 نوع پنل: {server.panel_type.value}")

    # Final result
    status = "🟢" if login_ok else "🔴"
    await callback.message.edit_text(
        f"{status} <b>تست سرور: {server.name}</b>\n\n" + "\n".join(results)
    )
    await callback.answer("✅ تست کامل شد")
