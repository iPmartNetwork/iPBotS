"""Mikrotik RouterOS service implementation."""
from typing import Optional, List
import aiohttp
from loguru import logger
from core.services.panel.base import BasePanelService, ClientInfo, InboundInfo


class MikrotikService(BasePanelService):
    """Service for Mikrotik RouterOS API."""

    def __init__(self, host: str, port: int, username: str, password: str, **kwargs):
        from core.services.encryption import encryption
        if password and len(password) > 50 and password.startswith("gAAAAA"):
            password = encryption.decrypt(password)
        super().__init__(host, port, username, password, **kwargs)
        self._base_url = f"{host}:{port}"

    def _auth(self):
        return aiohttp.BasicAuth(self.username, self.password)

    async def login(self) -> bool:
        try:
            async with aiohttp.ClientSession(
                auth=self._auth(),
                connector=aiohttp.TCPConnector(ssl=False),
            ) as session:
                async with session.get(f"{self._base_url}/rest/system/identity") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"Mikrotik connected: {data.get('name', 'unknown')}")
                        return True
                    return False
        except Exception as e:
            logger.error(f"Mikrotik login error: {e}")
            return False

    async def get_inbounds(self) -> List[InboundInfo]:
        return []

    async def add_client(self, inbound_id, email, data_limit_gb, expire_days, ip_limit=1) -> Optional[ClientInfo]:
        try:
            async with aiohttp.ClientSession(
                auth=self._auth(),
                connector=aiohttp.TCPConnector(ssl=False),
            ) as session:
                # Add PPP secret
                payload = {
                    "name": email,
                    "password": email[:8],
                    "service": "pppoe",
                    "profile": "default",
                    "comment": f"iPBotS|{data_limit_gb}GB|{expire_days}d",
                }
                async with session.put(
                    f"{self._base_url}/rest/ppp/secret",
                    json=payload,
                ) as resp:
                    if resp.status in (200, 201):
                        data = await resp.json()
                        return ClientInfo(
                            client_id=data.get(".id", email),
                            email=email,
                            enable=True,
                            up=0, down=0,
                            total=data_limit_gb * 1024**3,
                            expire_time=0,
                            inbound_id=inbound_id,
                        )
                    return None
        except Exception as e:
            logger.error(f"Mikrotik add client error: {e}")
            return None

    async def get_client(self, inbound_id, email) -> Optional[ClientInfo]:
        try:
            async with aiohttp.ClientSession(
                auth=self._auth(),
                connector=aiohttp.TCPConnector(ssl=False),
            ) as session:
                async with session.get(
                    f"{self._base_url}/rest/ppp/secret",
                    params={"name": email},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data:
                            item = data[0] if isinstance(data, list) else data
                            return ClientInfo(
                                client_id=item.get(".id", ""),
                                email=email,
                                enable=not item.get("disabled", False),
                                up=0, down=0, total=0,
                                expire_time=0,
                                inbound_id=inbound_id,
                            )
                    return None
        except Exception as e:
            logger.error(f"Mikrotik get client error: {e}")
            return None

    async def update_client(self, inbound_id, client_id, email, **kwargs) -> bool:
        try:
            payload = {}
            if kwargs.get("enable") is not None:
                payload["disabled"] = "false" if kwargs["enable"] else "true"

            async with aiohttp.ClientSession(
                auth=self._auth(),
                connector=aiohttp.TCPConnector(ssl=False),
            ) as session:
                async with session.patch(
                    f"{self._base_url}/rest/ppp/secret/{client_id}",
                    json=payload,
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Mikrotik update error: {e}")
            return False

    async def delete_client(self, inbound_id, client_id) -> bool:
        try:
            async with aiohttp.ClientSession(
                auth=self._auth(),
                connector=aiohttp.TCPConnector(ssl=False),
            ) as session:
                async with session.delete(
                    f"{self._base_url}/rest/ppp/secret/{client_id}",
                ) as resp:
                    return resp.status in (200, 204)
        except Exception as e:
            logger.error(f"Mikrotik delete error: {e}")
            return False

    async def reset_client_traffic(self, inbound_id, email) -> bool:
        return False

    async def get_client_traffic(self, email) -> Optional[dict]:
        return None

    async def get_subscription_url(self, client_id) -> Optional[str]:
        return None

    async def enable_client(self, inbound_id, client_id) -> bool:
        return await self.update_client(inbound_id, client_id, "", enable=True)

    async def disable_client(self, inbound_id, client_id) -> bool:
        return await self.update_client(inbound_id, client_id, "", enable=False)
