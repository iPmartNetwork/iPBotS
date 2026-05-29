"""IBSng panel service implementation."""
from typing import Optional, List
import aiohttp
from loguru import logger
from core.services.panel.base import BasePanelService, ClientInfo, InboundInfo


class IBSngService(BasePanelService):
    """Service for IBSng radius panel."""

    def __init__(self, host: str, port: int, username: str, password: str, **kwargs):
        from core.services.encryption import encryption
        if password and len(password) > 50 and password.startswith("gAAAAA"):
            password = encryption.decrypt(password)
        super().__init__(host, port, username, password, **kwargs)
        self._base_url = f"{host}:{port}"
        self._auth_cookie = None

    async def login(self) -> bool:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.post(
                    f"{self._base_url}/IBSng/admin/",
                    data={"username": self.username, "password": self.password},
                ) as resp:
                    if resp.status == 200:
                        self._auth_cookie = resp.cookies
                        logger.info(f"IBSng login successful: {self._base_url}")
                        return True
                    return False
        except Exception as e:
            logger.error(f"IBSng login error: {e}")
            return False

    async def get_inbounds(self) -> List[InboundInfo]:
        return []

    async def add_client(self, inbound_id, email, data_limit_gb, expire_days, ip_limit=1) -> Optional[ClientInfo]:
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                # IBSng uses XML-RPC or form-based API
                payload = {
                    "normal_username": email,
                    "normal_password": email[:8],
                    "group_name": "default",
                    "credit": str(data_limit_gb * 1024),  # MB
                    "duration": str(expire_days),
                }
                async with session.post(
                    f"{self._base_url}/IBSng/admin/user/add_new_users.php",
                    data=payload,
                    cookies=self._auth_cookie,
                ) as resp:
                    if resp.status == 200:
                        return ClientInfo(
                            client_id=email,
                            email=email,
                            enable=True,
                            up=0, down=0,
                            total=data_limit_gb * 1024**3,
                            expire_time=0,
                            inbound_id=inbound_id,
                        )
                    return None
        except Exception as e:
            logger.error(f"IBSng add client error: {e}")
            return None

    async def get_client(self, inbound_id, email) -> Optional[ClientInfo]:
        return None

    async def update_client(self, inbound_id, client_id, email, **kwargs) -> bool:
        return False

    async def delete_client(self, inbound_id, client_id) -> bool:
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
