"""3x-ui (Sanaei) panel service implementation."""

import json
import uuid
import time
from typing import Optional, List

import aiohttp
from loguru import logger

from core.services.panel.base import BasePanelService, ClientInfo, InboundInfo


class XUIService(BasePanelService):
    """Service for interacting with 3x-ui panel API."""

    def __init__(self, host: str, port: int, username: str, password: str, **kwargs):
        super().__init__(host, port, username, password, **kwargs)
        self._cookie_jar = aiohttp.CookieJar(unsafe=True)
        self._base_url = f"{host}:{port}"
        self._api_path = kwargs.get("api_path", "")

    def _url(self, path: str) -> str:
        """Build full URL."""
        if self._api_path:
            return f"{self._base_url}/{self._api_path}{path}"
        return f"{self._base_url}{path}"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get HTTP session."""
        return aiohttp.ClientSession(
            cookie_jar=self._cookie_jar,
            connector=aiohttp.TCPConnector(ssl=False),
        )

    async def login(self) -> bool:
        """Login to 3x-ui panel."""
        try:
            async with await self._get_session() as session:
                async with session.post(
                    self._url("/login"),
                    data={"username": self.username, "password": self.password},
                ) as resp:
                    data = await resp.json()
                    if data.get("success"):
                        logger.info(f"Successfully logged in to {self._base_url}")
                        return True
                    logger.error(f"Login failed: {data}")
                    return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    async def get_inbounds(self) -> List[InboundInfo]:
        """Get all inbounds from panel."""
        try:
            async with await self._get_session() as session:
                await self._ensure_logged_in(session)
                async with session.get(self._url("/panel/api/inbounds/list")) as resp:
                    data = await resp.json()
                    if not data.get("success"):
                        return []

                    inbounds = []
                    for item in data.get("obj", []):
                        settings = json.loads(item.get("settings", "{}"))
                        clients = settings.get("clients", [])
                        inbounds.append(
                            InboundInfo(
                                id=item["id"],
                                remark=item.get("remark", ""),
                                protocol=item.get("protocol", ""),
                                port=item.get("port", 0),
                                enable=item.get("enable", False),
                                total_clients=len(clients),
                            )
                        )
                    return inbounds
        except Exception as e:
            logger.error(f"Get inbounds error: {e}")
            return []

    async def add_client(
        self,
        inbound_id: int,
        email: str,
        data_limit_gb: int,
        expire_days: int,
        ip_limit: int = 1,
    ) -> Optional[ClientInfo]:
        """Add a new client to an inbound."""
        try:
            client_uuid = str(uuid.uuid4())
            expire_time = int((time.time() + expire_days * 86400) * 1000) if expire_days > 0 else 0
            data_limit = data_limit_gb * 1024 * 1024 * 1024 if data_limit_gb > 0 else 0

            client_data = {
                "id": inbound_id,
                "settings": json.dumps(
                    {
                        "clients": [
                            {
                                "id": client_uuid,
                                "flow": "",
                                "email": email,
                                "limitIp": ip_limit,
                                "totalGB": data_limit,
                                "expiryTime": expire_time,
                                "enable": True,
                                "tgId": "",
                                "subId": email,
                                "reset": 0,
                            }
                        ]
                    }
                ),
            }

            async with await self._get_session() as session:
                await self._ensure_logged_in(session)
                async with session.post(
                    self._url("/panel/api/inbounds/addClient"),
                    data=client_data,
                ) as resp:
                    result = await resp.json()
                    if result.get("success"):
                        logger.info(f"Client added: {email} to inbound {inbound_id}")
                        return ClientInfo(
                            client_id=client_uuid,
                            email=email,
                            enable=True,
                            up=0,
                            down=0,
                            total=data_limit,
                            expire_time=expire_time,
                            inbound_id=inbound_id,
                        )
                    logger.error(f"Add client failed: {result}")
                    return None
        except Exception as e:
            logger.error(f"Add client error: {e}")
            return None

    async def get_client(self, inbound_id: int, email: str) -> Optional[ClientInfo]:
        """Get client info by email."""
        try:
            async with await self._get_session() as session:
                await self._ensure_logged_in(session)
                async with session.get(
                    self._url(f"/panel/api/inbounds/getClientTraffics/{email}")
                ) as resp:
                    data = await resp.json()
                    if data.get("success") and data.get("obj"):
                        obj = data["obj"]
                        return ClientInfo(
                            client_id=obj.get("id", ""),
                            email=obj.get("email", email),
                            enable=obj.get("enable", True),
                            up=obj.get("up", 0),
                            down=obj.get("down", 0),
                            total=obj.get("total", 0),
                            expire_time=obj.get("expiryTime", 0),
                            inbound_id=obj.get("inboundId", inbound_id),
                        )
                    return None
        except Exception as e:
            logger.error(f"Get client error: {e}")
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
        """Update client settings."""
        try:
            # First get current client info
            current = await self.get_client(inbound_id, email)
            if not current:
                return False

            # Build update data
            update_data = {
                "id": client_id,
                "flow": "",
                "email": email,
                "limitIp": ip_limit if ip_limit is not None else 1,
                "totalGB": (
                    data_limit_gb * 1024 * 1024 * 1024
                    if data_limit_gb is not None
                    else current.total
                ),
                "expiryTime": (
                    int((time.time() + expire_days * 86400) * 1000)
                    if expire_days is not None
                    else current.expire_time
                ),
                "enable": enable if enable is not None else current.enable,
                "tgId": "",
                "subId": email,
                "reset": 0,
            }

            payload = {
                "id": inbound_id,
                "settings": json.dumps({"clients": [update_data]}),
            }

            async with await self._get_session() as session:
                await self._ensure_logged_in(session)
                async with session.post(
                    self._url(f"/panel/api/inbounds/updateClient/{client_id}"),
                    data=payload,
                ) as resp:
                    result = await resp.json()
                    return result.get("success", False)
        except Exception as e:
            logger.error(f"Update client error: {e}")
            return False

    async def delete_client(self, inbound_id: int, client_id: str) -> bool:
        """Delete a client."""
        try:
            async with await self._get_session() as session:
                await self._ensure_logged_in(session)
                async with session.post(
                    self._url(f"/panel/api/inbounds/{inbound_id}/delClient/{client_id}")
                ) as resp:
                    result = await resp.json()
                    return result.get("success", False)
        except Exception as e:
            logger.error(f"Delete client error: {e}")
            return False

    async def reset_client_traffic(self, inbound_id: int, email: str) -> bool:
        """Reset client traffic."""
        try:
            async with await self._get_session() as session:
                await self._ensure_logged_in(session)
                async with session.post(
                    self._url(f"/panel/api/inbounds/{inbound_id}/resetClientTraffic/{email}")
                ) as resp:
                    result = await resp.json()
                    return result.get("success", False)
        except Exception as e:
            logger.error(f"Reset traffic error: {e}")
            return False

    async def get_client_traffic(self, email: str) -> Optional[dict]:
        """Get client traffic stats."""
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
        return f"{self._base_url}/sub/{client_id}"

    async def enable_client(self, inbound_id: int, client_id: str) -> bool:
        """Enable a client."""
        # Get email first from client_id
        return await self.update_client(inbound_id, client_id, "", enable=True)

    async def disable_client(self, inbound_id: int, client_id: str) -> bool:
        """Disable a client."""
        return await self.update_client(inbound_id, client_id, "", enable=False)

    async def _ensure_logged_in(self, session: aiohttp.ClientSession):
        """Ensure we have a valid session."""
        # Try a simple request to check if session is valid
        try:
            async with session.post(
                self._url("/login"),
                data={"username": self.username, "password": self.password},
            ) as resp:
                await resp.json()
        except Exception:
            pass
