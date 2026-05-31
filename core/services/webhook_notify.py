"""External webhook notification service - send events to Discord/Zapier/etc."""

from typing import Optional, Dict, Any
import aiohttp
from loguru import logger

from bot.config import settings


class WebhookNotifyService:
    """Send event notifications to external webhooks (Discord, Zapier, etc)."""

    def __init__(self):
        self.webhook_url = getattr(settings, "EXTERNAL_WEBHOOK_URL", "")
        self.discord_webhook = getattr(settings, "DISCORD_WEBHOOK_URL", "")

    async def send_event(self, event_type: str, data: Dict[str, Any]):
        """Send event to configured webhooks."""
        if self.webhook_url:
            await self._send_generic(event_type, data)
        if self.discord_webhook:
            await self._send_discord(event_type, data)

    async def _send_generic(self, event_type: str, data: Dict[str, Any]):
        """Send to generic webhook (Zapier, n8n, etc)."""
        payload = {
            "event": event_type,
            "data": data,
            "bot": "iPBotS",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status >= 400:
                        logger.warning(f"Webhook failed ({resp.status}): {event_type}")
        except Exception as e:
            logger.error(f"Webhook error: {e}")

    async def _send_discord(self, event_type: str, data: Dict[str, Any]):
        """Send to Discord webhook."""
        event_icons = {
            "purchase": "🛒",
            "payment": "💳",
            "new_user": "👤",
            "server_down": "🔴",
            "server_up": "🟢",
        }
        icon = event_icons.get(event_type, "📌")

        embed = {
            "title": f"{icon} {event_type}",
            "color": 5814783,  # Purple
            "fields": [
                {"name": k, "value": str(v), "inline": True}
                for k, v in data.items()
            ],
            "footer": {"text": "iPBotS © iPmart Network"},
        }

        payload = {"embeds": [embed]}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.discord_webhook,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status >= 400:
                        logger.warning(f"Discord webhook failed: {resp.status}")
        except Exception as e:
            logger.error(f"Discord webhook error: {e}")

    async def notify_purchase(self, user_name: str, plan_name: str, amount: int):
        """Notify about a new purchase."""
        await self.send_event("purchase", {
            "user": user_name,
            "plan": plan_name,
            "amount": f"{amount:,} تومان",
        })

    async def notify_new_user(self, user_name: str, user_id: int):
        """Notify about a new user registration."""
        await self.send_event("new_user", {
            "name": user_name,
            "id": str(user_id),
        })

    async def notify_server_status(self, server_name: str, is_online: bool):
        """Notify about server status change."""
        event = "server_up" if is_online else "server_down"
        await self.send_event(event, {
            "server": server_name,
            "status": "Online" if is_online else "Offline",
        })
