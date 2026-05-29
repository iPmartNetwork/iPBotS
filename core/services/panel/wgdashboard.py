"""WGDashboard (WireGuard) service implementation."""
from typing import Optional, List
import aiohttp
from loguru import logger
from core.services.panel.base import BasePanelService, ClientInfo, InboundInfo


class WGDashboardService(BasePanelService):
    """Service for WGDashboard (WireGuard management panel)."""

    def __init__(self, host: str, port: int, username: str, password: str, **kwargs):
        from core.services.encryption import encryption
        if password and len(password) > 50 and password.startswith("gAAAAA"):
            password = encryption.decrypt(password)
        super().__init__(host, port, username, password, **kwargs)
        self._base_url = f"{host}:{port}"
        self._api_key = None

    async def login(self) -> bool:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.post(
                    f"{self._base_url}/api/authenticate",
                    json={"username": self.username, "password": self.password},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("status"):
                            self._api_key = data.get("data", {}).get("token", "")
                            logger.info(f"WGDashboard connected: {self._base_url}")
                            return True
                    return False
        except Exception as e:
            logger.error(f"WGDashboard login error: {e}")
            return False

    def _headers(self):
        return {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}

    async def get_inbounds(self) -> List[InboundInfo]:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.get(
                    f"{self._base_url}/api/getWireguardConfigurations",
                    headers=self._headers(),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        configs = data.get("data", [])
                        return [
                            InboundInfo(
                                id=i,
                                remark=cfg.get("Name", f"wg{i}"),
                                protocol="wireguard",
                                port=cfg.get("ListenPort", 51820),
                                enable=cfg.get("Status", True),
                                total_clients=len(cfg.get("Peers", [])),
                            )
                            for i, cfg in enumerate(configs)
                        ]
                    return []
        except Exception as e:
            logger.error(f"WGDashboard get inbounds error: {e}")
            return []

    async def add_client(self, inbound_id, email, data_limit_gb, expire_days, ip_limit=1) -> Optional[ClientInfo]:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                payload = {
                    "name": email,
                    "data_limit": data_limit_gb * 1024**3 if data_limit_gb > 0 else 0,
                    "expire_days": expire_days,
                }
                async with session.post(
                    f"{self._base_url}/api/addPeer/wg0",
                    headers=self._headers(),
                    json=payload,
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        peer = data.get("data", {})
                        return ClientInfo(
                            client_id=peer.get("id", email),
                            email=email,
                            enable=True,
                            up=0, down=0,
                            total=data_limit_gb * 1024**3,
                            expire_time=0,
                            inbound_id=inbound_id,
                            config_links=[peer.get("config", "")],
                        )
                    return None
        except Exception as e:
            logger.error(f"WGDashboard add client error: {e}")
            return None

    async def get_client(self, inbound_id, email) -> Optional[ClientInfo]:
        return None

    async def update_client(self, inbound_id, client_id, email, **kwargs) -> bool:
        return False

    async def delete_client(self, inbound_id, client_id) -> bool:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.post(
                    f"{self._base_url}/api/deletePeer/wg0",
                    headers=self._headers(),
                    json={"id": client_id},
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"WGDashboard delete error: {e}")
            return False

    async def reset_client_traffic(self, inbound_id, email) -> bool:
        return False

    async def get_client_traffic(self, email) -> Optional[dict]:
        return None

    async def get_subscription_url(self, client_id) -> Optional[str]:
        return None

    async def enable_client(self, inbound_id, client_id) -> bool:
        return False

    async def disable_client(self, inbound_id, client_id) -> bool:
        return False
