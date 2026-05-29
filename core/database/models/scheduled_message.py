"""Scheduled message model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, Boolean, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from core.database.models.base import Base


class ScheduledMessage(Base):
    """Scheduled message to be sent at a specific time."""
    __tablename__ = "scheduled_messages"

    message_text: Mapped[str] = mapped_column(Text)
    target: Mapped[str] = mapped_column(String(50), default="all")  # all, active, specific
    target_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    send_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int] = mapped_column(BigInteger)  # Admin telegram ID
