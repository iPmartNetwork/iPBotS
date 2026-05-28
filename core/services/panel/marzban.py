"""Marzban panel service implementation."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List

import aiohttp
from loguru import logger

from core.services.panel.base import BasePanelService, ClientInfo, InboundInfo


class MarzbanService(BasePanelService):
    """Service for interacting with Marzban panel API."""

    def __init__(self, host: str, port: int, username: str, password: str, **kwargs):
        super().__init__(host, port, username, password, **kwargs)
        self._base_url = f"{host}:{port}"
        self._token: Optional[str] = None

    def _headers(self) -> dict:
        """Get API headers with auth token."""
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _url(self, path: str) -> str:
        """Build full URL."""
        return f"{self._base_url}/api{path}"

    async def login(self) -> bool:
        """Authenticate with Marzban panel."""
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.post(
                    f"{self._base_url}/api/admin/token",
                    data={
                        "username": self.username,
                        "password": self.password,
                        "grant_type": "password",
                    },
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self._token = data.get("access_token")
                        logger.info(f"Marzban login successful: {self._base_url}")
                        return True
                    logger.error(f"Marzban login failed: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"Marzban login error: {e}")
            return False

    async def _ensure_token(self):
        """Ensure we have a valid token."""
        if not self._token:
            await self.login()

    async def get_inbounds(self) -> List[InboundInfo]:
        """Get inbounds from Marzban."""
        try:
            await self._ensure_token()
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.get(
                    self._url("/inbounds"),
                    headers=self._headers(),
                ) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    inbounds = []
                    for protocol, items in data.items():
                        for item in items:
                            inbounds.append(
                                InboundInfo(
                                    id=hash(item.get("tag", "")),
                                    remark=item.get("tag", ""),
                                    protocol=protocol,
                                    port=item.get("port", 0),
                                    enable=True,
                                    total_clients=0,
                                )
                            )
                    return inbounds
        except Exception as e:
            logger.error(f"Marzban get inbounds error: {e}")
            return []

    async def add_client(
        self,
        inbound_id: int,
        email: str,
        data_limit_gb: int,
        expire_days: int,
        ip_limit: int = 1,
    ) -> Optional[ClientInfo]:
        """Add a new user in Marzban."""
        try:
            await self._ensure_token()

            expire_timestamp = int(
                (datetime.now(timezone.utc) + timedelta(days=expire_days)).timestamp()
            )
            data_limit_bytes = data_limit_gb * 1024 * 1024 * 1024 if data_limit_gb > 0 else 0

            payload = {
                "username": email,
                "proxies": {
                    "vless": {"flow": ""},
                    "vmess": {},
                    "trojan": {},
                },
                "inbounds": {},
                "expire": expire_timestamp,
                "data_limit": data_limit_bytes,
                "data_limit_reset_strategy": "no_reset",
                "status": "active",
                "note": f"Created by bot at {datetime.now().isoformat()}",
            }

            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.post(
                    self._url("/user"),
                    headers=self._headers(),
                    json=payload,
                ) as resp:
                    if resp.status in (200, 201):
                        data = await resp.json()
                        logger.info(f"Marzban client added: {email}")

                        # Get subscription URL
                        sub_url = data.get("subscription_url", "")
                        links = data.get("links", [])

                        return ClientInfo(
                            client_id=email,
                            email=email,
                            enable=True,
                            up=0,
                            down=0,
                            total=data_limit_bytes,
                            expire_time=expire_timestamp * 1000,
                            inbound_id=inbound_id,
                            sub_url=f"{self._base_url}{sub_url}" if sub_url else None,
                            config_links=links,
                        )
                    else:
                        error = await resp.text()
                        logger.error(f"Marzban add client failed: {error}")
                        return None
        except Exception as e:
            logger.error(f"Marzban add client error: {e}")
            return None

    async def get_client(self, inbound_id: int, email: str) -> Optional[ClientInfo]:
        """Get client info from Marzban."""
        try:
            await self._ensure_token()
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.get(
                    self._url(f"/user/{email}"),
                    headers=self._headers(),
                ) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()

                    used_traffic = data.get("used_traffic", 0)
                    data_limit = data.get("data_limit", 0)
                    expire = data.get("expire", 0)

                    return ClientInfo(
                        client_id=email,
                        email=email,
                        enable=data.get("status") == "active",
                        up=data.get("lifetime_used_traffic", 0) // 2,
                        down=data.get("lifetime_used_traffic", 0) // 2,
                        total=data_limit,
                        expire_time=expire * 1000 if expire else 0,
                        inbound_id=inbound_id,
                        sub_url=f"{self._base_url}{data.get('subscription_url', '')}",
                    )
        except Exception as e:
            logger.error(f"Marzban get client error: {e}")
            return None

    async def update_client(
        self,
        inbound_id: int,
        client_id: str,
        email: str,
        data_limit_gb: Optional[int] = None,
        expire_days: Optional[int] = None,
        ip_limit: Optional[int] = None,
        enable: Optional[bool] = None,
    ) -> bool:
        """Update client in Marzban."""
        try:
            await self._ensure_token()
            payload = {}

            if data_limit_gb is not None:
                payload["data_limit"] = data_limit_gb * 1024 * 1024 * 1024 if data_limit_gb > 0 else 0

            if expire_days is not None:
                payload["expire"] = int(
                    (datetime.now(timezone.utc) + timedelta(days=expire_days)).timestamp()
                )

            if enable is not None:
                payload["status"] = "active" if enable else "disabled"

            username = client_id or email

            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.put(
                    self._url(f"/user/{username}"),
                    headers=self._headers(),
                    json=payload,
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Marzban update client error: {e}")
            return False

    async def delete_client(self, inbound_id: int, client_id: str) -> bool:
        """Delete client from Marzban."""
        try:
            await self._ensure_token()
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.delete(
                    self._url(f"/user/{client_id}"),
                    headers=self._headers(),
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Marzban delete client error: {e}")
            return False

    async def reset_client_traffic(self, inbound_id: int, email: str) -> bool:
        """Reset client traffic in Marzban."""
        try:
            await self._ensure_token()
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.post(
                    self._url(f"/user/{email}/reset"),
                    headers=self._headers(),
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Marzban reset traffic error: {e}")
            return False

    async def get_client_traffic(self, email: str) -> Optional[dict]:
        """Get client traffic from Marzban."""
        client = await self.get_client(0, email)
        if client:
            return {
                "up": client.up,
                "down": client.down,
                "total": client.total,
                "used": client.up + client.down,
            }
        return None

    async def get_subscription_url(self, client_id: str) -> Optional[str]:
        """Get subscription URL from Marzban."""
        try:
            await self._ensure_token()
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.get(
                    self._url(f"/user/{client_id}"),
                    headers=self._headers(),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        sub_url = data.get("subscription_url", "")
                        return f"{self._base_url}{sub_url}" if sub_url else None
            return None
        except Exception as e:
            logger.error(f"Marzban get sub URL error: {e}")
            return None

    async def enable_client(self, inbound_id: int, client_id: str) -> bool:
        """Enable client."""
        return await self.update_client(inbound_id, client_id, "", enable=True)

    async def disable_client(self, inbound_id: int, client_id: str) -> bool:
        """Disable client."""
        return await self.update_client(inbound_id, client_id, "", enable=False)
