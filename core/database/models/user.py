"""User model."""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import BigInteger, Boolean, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.models.base import Base


class User(Base):
    """Telegram user model."""

    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), default="")
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    language: Mapped[str] = mapped_column(String(5), default="fa")

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_seller: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Referral
    referral_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    referred_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    referral_earnings: Mapped[int] = mapped_column(Integer, default=0)  # in Toman

    # Stats
    total_purchases: Mapped[int] = mapped_column(Integer, default=0)
    total_spent: Mapped[int] = mapped_column(Integer, default=0)  # in Toman
    last_activity: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Preferences
    preferred_currency: Mapped[str] = mapped_column(String(5), default="IRT")

    # Relationships
    referred_by: Mapped[Optional["User"]] = relationship(
        "User", remote_side="User.id", backref="referrals"
    )
    wallet: Mapped[Optional["Wallet"]] = relationship(
        "Wallet", back_populates="user", uselist=False
    )
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="user"
    )
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")
    tickets: Mapped[List["Ticket"]] = relationship("Ticket", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"

    @property
    def full_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name

    @property
    def mention(self) -> str:
        if self.username:
            return f"@{self.username}"
        return f'<a href="tg://user?id={self.telegram_id}">{self.full_name}</a>'
