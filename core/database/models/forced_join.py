"""Forced channel join model."""
from typing import Optional
from sqlalchemy import String, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from core.database.models.base import Base


class ForcedChannel(Base):
    """Channel that users must join before using the bot."""
    __tablename__ = "forced_channels"

    channel_id: Mapped[str] = mapped_column(String(100))  # @channel or -100xxx
    channel_name: Mapped[str] = mapped_column(String(200))
    channel_url: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
