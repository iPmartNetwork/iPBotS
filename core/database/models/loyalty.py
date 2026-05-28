"""Loyalty points and rewards system."""

from typing import Optional, List

from sqlalchemy import String, Integer, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.models.base import Base


class LoyaltyConfig(Base):
    """Loyalty system configuration."""

    __tablename__ = "loyalty_configs"

    points_per_purchase_toman: Mapped[int] = mapped_column(Integer, default=1)  # 1 point per X toman
    points_per_referral: Mapped[int] = mapped_column(Integer, default=50)
    points_per_review: Mapped[int] = mapped_column(Integer, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class LoyaltyReward(Base):
    """Available rewards that can be redeemed with points."""

    __tablename__ = "loyalty_rewards"

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    points_required: Mapped[int] = mapped_column(Integer)
    reward_type: Mapped[str] = mapped_column(String(50))  # discount_percent, free_days, extra_traffic
    reward_value: Mapped[int] = mapped_column(Integer)  # percent or GB or days
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    stock: Mapped[int] = mapped_column(Integer, default=-1)  # -1 = unlimited
    icon: Mapped[str] = mapped_column(String(10), default="🎁")

    def __repr__(self):
        return f"<LoyaltyReward(name={self.name}, points={self.points_required})>"


class UserLoyalty(Base):
    """User loyalty points balance."""

    __tablename__ = "user_loyalty"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    available_points: Mapped[int] = mapped_column(Integer, default=0)
    spent_points: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[str] = mapped_column(String(50), default="bronze")  # bronze, silver, gold, diamond

    user: Mapped["User"] = relationship("User")


class LoyaltyTransaction(Base):
    """Loyalty points transaction history."""

    __tablename__ = "loyalty_transactions"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    points: Mapped[int] = mapped_column(Integer)  # positive = earned, negative = spent
    transaction_type: Mapped[str] = mapped_column(String(50))  # purchase, referral, redeem, bonus
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
