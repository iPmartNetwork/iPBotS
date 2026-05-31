"""Subscription model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from core.database.models.base import Base


class SubscriptionStatus(str, enum.Enum):
    """Subscription status."""

    ACTIVE = "active"
    EXPIRED = "expired"
    DISABLED = "disabled"
    TRAFFIC_ENDED = "traffic_ended"
    PENDING = "pending"


class Subscription(Base):
    """User VPN subscription."""

    __tablename__ = "subscriptions"

    # User
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    plan_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("plans.id"), nullable=True
    )
    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id"))
    order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orders.id"), nullable=True
    )

    # Panel info
    panel_client_id: Mapped[str] = mapped_column(String(200))  # UUID or ID in panel
    panel_email: Mapped[str] = mapped_column(String(200))  # Email/username in panel
    inbound_id: Mapped[int] = mapped_column(Integer)

    # Config
    subscription_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config_links: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON

    # Limits
    data_limit_bytes: Mapped[int] = mapped_column(BigInteger)  # 0 = unlimited
    used_traffic_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    ip_limit: Mapped[int] = mapped_column(Integer, default=1)

    # Notification tracking
    notified_80: Mapped[bool] = mapped_column(Boolean, default=False)
    notified_95: Mapped[bool] = mapped_column(Boolean, default=False)
    notified_100: Mapped[bool] = mapped_column(Boolean, default=False)
    notified_3days: Mapped[bool] = mapped_column(Boolean, default=False)
    notified_1day: Mapped[bool] = mapped_column(Boolean, default=False)

    # Duration
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expire_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Status
    status: Mapped[SubscriptionStatus] = mapped_column(
        SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
    plan: Mapped["Plan"] = relationship("Plan")
    server: Mapped["Server"] = relationship("Server")

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, status={self.status})>"

    @property
    def used_traffic_gb(self) -> float:
        return round(self.used_traffic_bytes / (1024**3), 2)

    @property
    def data_limit_gb(self) -> float:
        if self.data_limit_bytes == 0:
            return 0
        return round(self.data_limit_bytes / (1024**3), 2)

    @property
    def remaining_traffic_gb(self) -> float:
        if self.data_limit_bytes == 0:
            return float("inf")
        remaining = self.data_limit_bytes - self.used_traffic_bytes
        return round(max(0, remaining) / (1024**3), 2)

    @property
    def traffic_percent(self) -> int:
        if self.data_limit_bytes == 0:
            return 0
        return int((self.used_traffic_bytes / self.data_limit_bytes) * 100)

    @property
    def is_expired(self) -> bool:
        from datetime import timezone
        return datetime.now(timezone.utc) > self.expire_date

    @property
    def remaining_days(self) -> int:
        from datetime import timezone
        delta = self.expire_date - datetime.now(timezone.utc)
        return max(0, delta.days)
