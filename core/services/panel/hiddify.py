"""Hiddify panel service implementation."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List

import aiohttp
from loguru import logger

from core.services.panel.base import BasePanelService, ClientInfo, InboundInfo


class HiddifyService(BasePanelService):
    """Service for interacting with Hiddify Manager API."""

    def __init__(self, host: str, port: int, username: str, password: str, **kwargs):
        super().__init__(host, port, username, password, **kwargs)
        self._api_key = kwargs.get("hiddify_api_key", "")
        self._base_url = f"{host}:{port}"

    def _headers(self) -> dict:
        """Get API headers."""
        return {
            "Hiddify-API-Key": self._api_key,
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        """Build full URL."""
        return f"{self._base_url}/api/v2{path}"

    async def login(self) -> bool:
        """Verify API key is valid."""
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.get(
                    self._url("/admin/user/"),
                    headers=self._headers(),
                ) as resp:
                    if resp.status == 200:
                        logger.info(f"Hiddify API connected: {self._base_url}")
                        return True
                    logger.error(f"Hiddify login failed: {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"Hiddify login error: {e}")
            return False

    async def get_inbounds(self) -> List[InboundInfo]:
        """Get inbounds (proxies) from Hiddify."""
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.get(
                    self._url("/admin/proxy/"),
                    headers=self._headers(),
                ) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
                    inbounds = []
                    for i, item in enumerate(data):
                        inbounds.append(
                            InboundInfo(
                                id=i,
                                remark=item.get("name", ""),
                                protocol=item.get("transport", ""),
                                port=item.get("port", 0),
                                enable=item.get("enable", True),
                                total_clients=0,
                            )
                        )
                    return inbounds
        except Exception as e:
            logger.error(f"Hiddify get inbounds error: {e}")
            return []

    async def add_client(
        self,
        inbound_id: int,
        email: str,
        data_limit_gb: int,
        expire_days: int,
        ip_limit: int = 1,
    ) -> Optional[ClientInfo]:
        """Add a new user in Hiddify."""
        try:
            client_uuid = str(uuid.uuid4())
            expire_date = (
                datetime.now(timezone.utc) + timedelta(days=expire_days)
            ).strftime("%Y-%m-%d")

            payload = {
                "uuid": client_uuid,
                "name": email,
                "usage_limit_GB": data_limit_gb if data_limit_gb > 0 else 0,
                "package_days": expire_days,
                "last_reset_time": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "start_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "current_usage_GB": 0,
                "mode": "no_reset",
                "enable": True,
            }

            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.post(
                    self._url("/admin/user/"),
                    headers=self._headers(),
                    json=payload,
                ) as resp:
                    if resp.status in (200, 201):
                        logger.info(f"Hiddify client added: {email}")
                        data_limit_bytes = data_limit_gb * 1024 * 1024 * 1024 if data_limit_gb > 0 else 0
                        return ClientInfo(
                            client_id=client_uuid,
                            email=email,
                            enable=True,
                            up=0,
                            down=0,
                            total=data_limit_bytes,
                            expire_time=int(
                                (datetime.now(timezone.utc) + timedelta(days=expire_days)).timestamp() * 1000
                            ),
                            inbound_id=inbound_id,
                            sub_url=f"{self._base_url}/sub/{client_uuid}/",
                        )
                    error = await resp.text()
                    logger.error(f"Hiddify add client failed: {error}")
                    return None
        except Exception as e:
            logger.error(f"Hiddify add client error: {e}")
            return None

    async def get_client(self, inbound_id: int, email: str) -> Optional[ClientInfo]:
        """Get client info."""
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.get(
                    self._url("/admin/user/"),
                    headers=self._headers(),
                ) as resp:
                    if resp.status != 200:
                        return None
                    users = await resp.json()
                    for user in users:
                        if user.get("name") == email or user.get("uuid") == email:
                            usage_gb = user.get("current_usage_GB", 0)
                            limit_gb = user.get("usage_limit_GB", 0)
                            return ClientInfo(
                                client_id=user.get("uuid", ""),
                                email=user.get("name", ""),
                                enable=user.get("enable", True),
                                up=0,
                                down=int(usage_gb * 1024 * 1024 * 1024),
                                total=int(limit_gb * 1024 * 1024 * 1024) if limit_gb > 0 else 0,
                                expire_time=0,
                                inbound_id=inbound_id,
                                sub_url=f"{self._base_url}/sub/{user.get('uuid', '')}/",
                            )
                    return None
        except Exception as e:
            logger.error(f"Hiddify get client error: {e}")
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
        """Update client in Hiddify."""
        try:
            payload = {}
            if data_limit_gb is not None:
                payload["usage_limit_GB"] = data_limit_gb
            if expire_days is not None:
                payload["package_days"] = expire_days
            if enable is not None:
                payload["enable"] = enable

            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.patch(
                    self._url(f"/admin/user/{client_id}/"),
                    headers=self._headers(),
                    json=payload,
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"Hiddify update client error: {e}")
            return False

    async def delete_client(self, inbound_id: int, client_id: str) -> bool:
        """Delete client from Hiddify."""
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False)
            ) as session:
                async with session.delete(
                    self._url(f"/admin/user/{client_id}/"),
                    headers=self._headers(),
                ) as resp:
                    return resp.status in (200, 204)
        except Exception as e:
            logger.error(f"Hiddify delete client error: {e}")
            return False

    async def reset_client_traffic(self, inbound_id: int, email: str) -> bool:
        """Reset client traffic in Hiddify."""
        client = await self.get_client(inbound_id, email)
        if not client:
            return False
        return await self.update_client(
            inbound_id, client.client_id, email, data_limit_gb=None
        )

    async def get_client_traffic(self, email: str) -> Optional[dict]:
        """Get client traffic."""
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
        """Get subscription URL."""
        return f"{self._base_url}/sub/{client_id}/"

    async def enable_client(self, inbound_id: int, client_id: str) -> bool:
        """Enable client."""
        return await self.update_client(inbound_id, client_id, "", enable=True)

    async def disable_client(self, inbound_id: int, client_id: str) -> bool:
        """Disable client."""
        return await self.update_client(inbound_id, client_id, "", enable=False)
