"""Server model for VPN panels."""

from typing import Optional

from sqlalchemy import Boolean, String, Integer, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from core.database.models.base import Base


class PanelType(str, enum.Enum):
    """Supported panel types."""

    XUI = "3x-ui"
    HIDDIFY = "hiddify"
    MARZBAN = "marzban"


class Server(Base):
    """VPN server/panel configuration."""

    __tablename__ = "servers"

    name: Mapped[str] = mapped_column(String(200))
    panel_type: Mapped[PanelType] = mapped_column(SQLEnum(PanelType))

    # Connection
    host: Mapped[str] = mapped_column(String(500))  # Panel URL
    port: Mapped[int] = mapped_column(Integer, default=443)
    username: Mapped[str] = mapped_column(String(200))
    password: Mapped[str] = mapped_column(String(500))  # Encrypted
    api_path: Mapped[str] = mapped_column(String(200), default="")

    # For Hiddify
    hiddify_api_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Server info
    location: Mapped[str] = mapped_column(String(100), default="🌍")
    flag: Mapped[str] = mapped_column(String(10), default="🇩🇪")
    max_users: Mapped[int] = mapped_column(Integer, default=0)  # 0 = unlimited
    current_users: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return f"<Server(id={self.id}, name={self.name}, type={self.panel_type})>"

    @property
    def panel_url(self) -> str:
        return f"{self.host}:{self.port}"

    @property
    def is_full(self) -> bool:
        if self.max_users == 0:
            return False
        return self.current_users >= self.max_users
