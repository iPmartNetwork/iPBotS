"""Protocol configuration model."""
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from core.database.models.base import Base


class ProtocolConfig(Base):
    """Protocol configuration for servers."""
    __tablename__ = "protocol_configs"

    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id"))
    protocol: Mapped[str] = mapped_column(String(50))  # vless, vmess, trojan, shadowsocks
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    flow: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # xtls-rprx-vision
    security: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # tls, reality
    network: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # tcp, ws, grpc
    extra_config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
