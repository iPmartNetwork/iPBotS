"""Plan and PlanCategory models."""

from typing import Optional, List

from sqlalchemy import Boolean, String, Integer, BigInteger, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.models.base import Base


class PlanCategory(Base):
    """Category for grouping plans."""

    __tablename__ = "plan_categories"

    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[str] = mapped_column(String(10), default="📦")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    plans: Mapped[List["Plan"]] = relationship("Plan", back_populates="category")

    def __repr__(self):
        return f"<PlanCategory(id={self.id}, name={self.name})>"


class Plan(Base):
    """VPN subscription plan."""

    __tablename__ = "plans"

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Category
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("plan_categories.id"), nullable=True
    )

    # Specs
    data_limit_gb: Mapped[int] = mapped_column(Integer)  # GB, 0 = unlimited
    duration_days: Mapped[int] = mapped_column(Integer)  # Days
    ip_limit: Mapped[int] = mapped_column(Integer, default=1)  # Concurrent connections
    speed_limit: Mapped[int] = mapped_column(Integer, default=0)  # Mbps, 0 = unlimited

    # Pricing
    price: Mapped[int] = mapped_column(Integer)  # Toman
    price_usd: Mapped[int] = mapped_column(Integer, default=0)  # Cents
    discount_percent: Mapped[int] = mapped_column(Integer, default=0)

    # Server assignment
    server_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("servers.id"), nullable=True
    )
    inbound_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    stock: Mapped[int] = mapped_column(Integer, default=-1)  # -1 = unlimited
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    category: Mapped[Optional["PlanCategory"]] = relationship(
        "PlanCategory", back_populates="plans"
    )
    server: Mapped[Optional["Server"]] = relationship("Server")

    def __repr__(self):
        return f"<Plan(id={self.id}, name={self.name}, price={self.price})>"

    @property
    def final_price(self) -> int:
        """Calculate price after discount."""
        if self.discount_percent > 0:
            return int(self.price * (100 - self.discount_percent) / 100)
        return self.price

    @property
    def display_data(self) -> str:
        if self.data_limit_gb == 0:
            return "♾️ نامحدود"
        return f"{self.data_limit_gb} GB"

    @property
    def display_duration(self) -> str:
        if self.duration_days >= 30:
            months = self.duration_days // 30
            return f"{months} ماه"
        return f"{self.duration_days} روز"
