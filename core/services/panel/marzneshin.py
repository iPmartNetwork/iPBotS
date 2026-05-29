"""Marzneshin panel service implementation."""
from typing import Optional, List
import aiohttp
from loguru import logger
from core.services.panel.base import BasePanelService, ClientInfo, InboundInfo


class MarzneshinService(BasePanelService):
    """Service for Marzneshin panel (similar to Marzban with minor API differences)."""

    def __init__(self, host: str, port: int, username: str, password: str, **kwargs):
        from core.services.encryption import encryption
        if password and len(password) > 50 and password.startswith("gAAAAA"):
            password = encryption.decrypt(password)
        super().__init__(host, port, username, password, **kwargs)
        self._base_url = f"{host}:{port}"
        self._token: Optional[str] = None

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def login(self) -> bool:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.post(
                    f"{self._base_url}/api/admin/token",
                    data={"username": self.username, "password": self.password, "grant_type": "password"},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._token = data.get("access_token")
                        return True
                    return False
        except Exception as e:
            logger.error(f"Marzneshin login error: {e}")
            return False

    async def get_inbounds(self) -> List[InboundInfo]:
        return []  # Similar to Marzban

    async def add_client(self, inbound_id, email, data_limit_gb, expire_days, ip_limit=1) -> Optional[ClientInfo]:
        # Similar to Marzban API
        from core.services.panel.marzban import MarzbanService
        # Reuse Marzban logic as Marzneshin has compatible API
        marzban = MarzbanService(self.host, self.port, self.username, self.password)
        marzban._token = self._token
        marzban._base_url = self._base_url
        return await marzban.add_client(inbound_id, email, data_limit_gb, expire_days, ip_limit)

    async def get_client(self, inbound_id, email) -> Optional[ClientInfo]:
        from core.services.panel.marzban import MarzbanService
        marzban = MarzbanService(self.host, self.port, self.username, self.password)
        marzban._token = self._token
        marzban._base_url = self._base_url
        return await marzban.get_client(inbound_id, email)

    async def update_client(self, inbound_id, client_id, email, **kwargs) -> bool:
        from core.services.panel.marzban import MarzbanService
        marzban = MarzbanService(self.host, self.port, self.username, self.password)
        marzban._token = self._token
        marzban._base_url = self._base_url
        return await marzban.update_client(inbound_id, client_id, email, **kwargs)

    async def delete_client(self, inbound_id, client_id) -> bool:
        from core.services.panel.marzban import MarzbanService
        marzban = MarzbanService(self.host, self.port, self.username, self.password)
        marzban._token = self._token
        marzban._base_url = self._base_url
        return await marzban.delete_client(inbound_id, client_id)

    async def reset_client_traffic(self, inbound_id, email) -> bool:
        return False

    async def get_client_traffic(self, email) -> Optional[dict]:
        return None

    async def get_subscription_url(self, client_id) -> Optional[str]:
        return f"{self._base_url}/sub/{client_id}"

    async def enable_client(self, inbound_id, client_id) -> bool:
        return await self.update_client(inbound_id, client_id, "", enable=True)

    async def disable_client(self, inbound_id, client_id) -> bool:
        return await self.update_client(inbound_id, client_id, "", enable=False)
