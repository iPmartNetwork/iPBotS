"""Reseller (agency) system models."""

from typing import Optional, List

from sqlalchemy import Boolean, String, Integer, ForeignKey, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.models.base import Base


class ResellerLevel(Base):
    """Reseller tier/level configuration."""

    __tablename__ = "reseller_levels"

    name: Mapped[str] = mapped_column(String(100))  # e.g. Bronze, Silver, Gold
    discount_percent: Mapped[int] = mapped_column(Integer, default=10)
    min_purchase_amount: Mapped[int] = mapped_column(Integer, default=0)  # Toman to qualify
    max_users: Mapped[int] = mapped_column(Integer, default=50)  # Max clients they can have
    can_set_custom_price: Mapped[bool] = mapped_column(Boolean, default=False)
    commission_percent: Mapped[int] = mapped_column(Integer, default=0)  # Extra commission
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self):
        return f"<ResellerLevel(name={self.name}, discount={self.discount_percent}%)>"


class Reseller(Base):
    """Reseller account."""

    __tablename__ = "resellers"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    level_id: Mapped[int] = mapped_column(ForeignKey("reseller_levels.id"))
    shop_name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Financial
    balance: Mapped[int] = mapped_column(Integer, default=0)  # Toman
    total_sales: Mapped[int] = mapped_column(Integer, default=0)
    total_revenue: Mapped[int] = mapped_column(Integer, default=0)
    total_clients: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Custom branding
    custom_welcome_msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    support_contact: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    level: Mapped["ResellerLevel"] = relationship("ResellerLevel")

    def __repr__(self):
        return f"<Reseller(shop={self.shop_name}, user_id={self.user_id})>"


class ResellerTransaction(Base):
    """Reseller financial transactions."""

    __tablename__ = "reseller_transactions"

    reseller_id: Mapped[int] = mapped_column(ForeignKey("resellers.id"))
    amount: Mapped[int] = mapped_column(Integer)
    transaction_type: Mapped[str] = mapped_column(String(50))  # deposit, sale, withdraw
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    balance_after: Mapped[int] = mapped_column(Integer)

    reseller: Mapped["Reseller"] = relationship("Reseller")
