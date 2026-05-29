"""Review and rating model."""

from typing import Optional

from sqlalchemy import Integer, ForeignKey, Text, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models.base import Base


class Review(Base):
    """User review after purchase."""

    __tablename__ = "reviews"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"))
    rating: Mapped[int] = mapped_column(Integer)  # 1-5 stars
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    server_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
