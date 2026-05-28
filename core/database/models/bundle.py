"""Bundle (package deal) models."""

from typing import Optional, List

from sqlalchemy import String, Integer, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.models.base import Base


class Bundle(Base):
    """Bundle - multiple plans sold together at a discount."""

    __tablename__ = "bundles"

    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[str] = mapped_column(String(10), default="📦")

    # Pricing
    original_price: Mapped[int] = mapped_column(Integer)  # Sum of individual prices
    bundle_price: Mapped[int] = mapped_column(Integer)  # Discounted price
    discount_percent: Mapped[int] = mapped_column(Integer, default=0)

    # Bulk options
    min_quantity: Mapped[int] = mapped_column(Integer, default=1)
    max_quantity: Mapped[int] = mapped_column(Integer, default=10)
    bulk_discount_per_unit: Mapped[int] = mapped_column(Integer, default=0)  # Extra discount per unit

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    stock: Mapped[int] = mapped_column(Integer, default=-1)  # -1 = unlimited
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    items: Mapped[List["BundleItem"]] = relationship("BundleItem", back_populates="bundle")

    def __repr__(self):
        return f"<Bundle(name={self.name}, price={self.bundle_price})>"

    @property
    def savings(self) -> int:
        """Calculate savings amount."""
        return self.original_price - self.bundle_price

    @property
    def savings_percent(self) -> int:
        """Calculate savings percentage."""
        if self.original_price == 0:
            return 0
        return int((self.savings / self.original_price) * 100)

    def calculate_bulk_price(self, quantity: int) -> int:
        """Calculate price for bulk purchase."""
        base = self.bundle_price * quantity
        if self.bulk_discount_per_unit > 0 and quantity > 1:
            discount = self.bulk_discount_per_unit * (quantity - 1)
            base -= discount
        return max(base, 0)


class BundleItem(Base):
    """Individual item in a bundle."""

    __tablename__ = "bundle_items"

    bundle_id: Mapped[int] = mapped_column(ForeignKey("bundles.id"))
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    bundle: Mapped["Bundle"] = relationship("Bundle", back_populates="items")
    plan: Mapped["Plan"] = relationship("Plan")

    def __repr__(self):
        return f"<BundleItem(bundle_id={self.bundle_id}, plan_id={self.plan_id})>"
