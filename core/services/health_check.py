"""Server health monitoring service."""

import asyncio
import time
from datetime import datetime, timezone
from typing import Optional, Dict, List

import aiohttp
from loguru import logger
from sqlalchemy import select

from core.database.engine import get_session
from core.database.models import Server
from core.database.models.server import PanelType
from core.database.models.server_monitoring import ServerStatus


class HealthCheckService:
    """Service for monitoring server health."""

    def __init__(self):
        self._last_results: Dict[int, dict] = {}

    async def check_server(self, server: Server) -> dict:
        """Check a single server's health."""
        result = {
            "server_id": server.id,
            "server_name": server.name,
            "is_online": False,
            "ping_ms": None,
            "error": None,
            "checked_at": datetime.now(timezone.utc),
        }

        try:
            start_time = time.time()

            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as session:
                # Try to reach the panel
                url = f"{server.host}:{server.port}"

                if server.panel_type == PanelType.XUI:
                    # Try login endpoint
                    async with session.post(
                        f"{url}/login",
                        data={"username": server.username, "password": server.password},
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            result["is_online"] = data.get("success", False)
                        else:
                            result["is_online"] = resp.status < 500

                elif server.panel_type == PanelType.HIDDIFY:
                    # Try API endpoint
                    headers = {"Hiddify-API-Key": server.hiddify_api_key or ""}
                    async with session.get(
                        f"{url}/api/v2/admin/user/",
                        headers=headers,
                    ) as resp:
                        result["is_online"] = resp.status == 200

                # For Marzban
                elif hasattr(PanelType, 'MARZBAN') and server.panel_type == PanelType.MARZBAN:
                    async with session.post(
                        f"{url}/api/admin/token",
                        data={"username": server.username, "password": server.password},
                    ) as resp:
                        result["is_online"] = resp.status == 200

            end_time = time.time()
            result["ping_ms"] = int((end_time - start_time) * 1000)

        except asyncio.TimeoutError:
            result["error"] = "Timeout (10s)"
            result["is_online"] = False
        except aiohttp.ClientError as e:
            result["error"] = f"Connection error: {str(e)[:100]}"
            result["is_online"] = False
        except Exception as e:
            result["error"] = f"Error: {str(e)[:100]}"
            result["is_online"] = False

        self._last_results[server.id] = result
        return result

    async def check_all_servers(self) -> List[dict]:
        """Check all active servers."""
        async with get_session() as session:
            stmt = select(Server).where(Server.is_active == True)
            result = await session.execute(stmt)
            servers = result.scalars().all()

        results = []
        for server in servers:
            check_result = await self.check_server(server)
            results.append(check_result)

            # Save to database
            async with get_session() as session:
                status = ServerStatus(
                    server_id=server.id,
                    is_online=check_result["is_online"],
                    ping_ms=check_result["ping_ms"],
                    checked_at=check_result["checked_at"],
                )
                session.add(status)

        return results

    async def get_down_servers(self) -> List[dict]:
        """Get list of servers that are currently down."""
        return [
            r for r in self._last_results.values()
            if not r.get("is_online")
        ]

    def get_last_result(self, server_id: int) -> Optional[dict]:
        """Get last health check result for a server."""
        return self._last_results.get(server_id)

    async def notify_server_down(self, server_result: dict):
        """Send notification when a server goes down."""
        from bot.loader import bot
        from bot.config import settings

        message = (
            f"🔴 <b>سرور قطع شد!</b>\n\n"
            f"🖥️ نام: {server_result['server_name']}\n"
            f"⏱️ زمان: {server_result['checked_at'].strftime('%H:%M:%S')}\n"
        )
        if server_result.get("error"):
            message += f"❌ خطا: {server_result['error']}\n"

        message += "\n⚠️ لطفاً بررسی کنید."

        for admin_id in settings.admin_ids_list:
            try:
                await bot.send_message(admin_id, message)
            except Exception:
                pass

    async def notify_server_recovered(self, server_result: dict):
        """Send notification when a server recovers."""
        from bot.loader import bot
        from bot.config import settings

        message = (
            f"🟢 <b>سرور بازیابی شد!</b>\n\n"
            f"🖥️ نام: {server_result['server_name']}\n"
            f"📶 پینگ: {server_result['ping_ms']}ms\n"
            f"⏱️ زمان: {server_result['checked_at'].strftime('%H:%M:%S')}"
        )

        for admin_id in settings.admin_ids_list:
            try:
                await bot.send_message(admin_id, message)
            except Exception:
                pass


# Singleton
health_checker = HealthCheckService()

