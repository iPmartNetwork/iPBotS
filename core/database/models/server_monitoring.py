"""Server monitoring and load balancing models."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, ForeignKey, Float, DateTime, String, Boolean, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.models.base import Base


class ServerStatus(Base):
    """Server health status snapshots."""

    __tablename__ = "server_statuses"

    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id"), index=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=True)
    ping_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cpu_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    disk_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bandwidth_up: Mapped[int] = mapped_column(BigInteger, default=0)  # bytes/s
    bandwidth_down: Mapped[int] = mapped_column(BigInteger, default=0)  # bytes/s
    active_connections: Mapped[int] = mapped_column(Integer, default=0)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    server: Mapped["Server"] = relationship("Server")


class LoadBalanceRule(Base):
    """Load balancing rules for distributing users across servers."""

    __tablename__ = "load_balance_rules"

    name: Mapped[str] = mapped_column(String(200))
    strategy: Mapped[str] = mapped_column(String(50), default="least_users")
    # Strategies: least_users, round_robin, random, weighted, least_load
    max_users_per_server: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Thresholds for auto-migration
    cpu_threshold: Mapped[int] = mapped_column(Integer, default=80)  # percent
    memory_threshold: Mapped[int] = mapped_column(Integer, default=85)
    connection_threshold: Mapped[int] = mapped_column(Integer, default=200)
