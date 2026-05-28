"""Base panel service interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ClientInfo:
    """Client information from panel."""

    client_id: str
    email: str
    enable: bool
    up: int  # Upload bytes
    down: int  # Download bytes
    total: int  # Total traffic limit bytes
    expire_time: int  # Timestamp ms, 0 = unlimited
    inbound_id: int
    sub_url: Optional[str] = None
    config_links: Optional[List[str]] = None


@dataclass
class InboundInfo:
    """Inbound information from panel."""

    id: int
    remark: str
    protocol: str
    port: int
    enable: bool
    total_clients: int


class BasePanelService(ABC):
    """Abstract base class for panel services."""

    def __init__(self, host: str, port: int, username: str, password: str, **kwargs):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self._session_cookie: Optional[str] = None

    @abstractmethod
    async def login(self) -> bool:
        """Authenticate with the panel."""
        ...

    @abstractmethod
    async def get_inbounds(self) -> List[InboundInfo]:
        """Get all inbounds."""
        ...

    @abstractmethod
    async def add_client(
        self,
        inbound_id: int,
        email: str,
        data_limit_gb: int,
        expire_days: int,
        ip_limit: int = 1,
    ) -> Optional[ClientInfo]:
        """Add a new client to an inbound."""
        ...

    @abstractmethod
    async def get_client(self, inbound_id: int, email: str) -> Optional[ClientInfo]:
        """Get client info by email."""
        ...

    @abstractmethod
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
        ...

    @abstractmethod
    async def delete_client(self, inbound_id: int, client_id: str) -> bool:
        """Delete a client."""
        ...

    @abstractmethod
    async def reset_client_traffic(self, inbound_id: int, email: str) -> bool:
        """Reset client traffic usage."""
        ...

    @abstractmethod
    async def get_client_traffic(self, email: str) -> Optional[dict]:
        """Get client traffic stats."""
        ...

    @abstractmethod
    async def get_subscription_url(self, client_id: str) -> Optional[str]:
        """Get subscription URL for client."""
        ...

    @abstractmethod
    async def enable_client(self, inbound_id: int, client_id: str) -> bool:
        """Enable a client."""
        ...

    @abstractmethod
    async def disable_client(self, inbound_id: int, client_id: str) -> bool:
        """Disable a client."""
        ...
