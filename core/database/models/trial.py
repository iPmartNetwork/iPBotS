"""Free trial model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, Integer, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models.base import Base


class TrialConfig(Base):
    """Trial configuration (admin sets these)."""

    __tablename__ = "trial_configs"

    data_limit_gb: Mapped[int] = mapped_column(Integer, default=1)
    duration_hours: Mapped[int] = mapped_column(Integer, default=24)
    ip_limit: Mapped[int] = mapped_column(Integer, default=1)
    server_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("servers.id"), nullable=True
    )
    inbound_id: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_trials_per_user: Mapped[int] = mapped_column(Integer, default=1)


class TrialUsage(Base):
    """Track which users have used trial."""

    __tablename__ = "trial_usages"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    subscription_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("subscriptions.id"), nullable=True
    )
    used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
