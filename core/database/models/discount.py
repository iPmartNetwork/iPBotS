"""Discount code model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
import enum

from core.database.models.base import Base


class DiscountType(str, enum.Enum):
    """Discount type."""

    PERCENT = "percent"
    FIXED = "fixed"  # Fixed amount in Toman


class DiscountCode(Base):
    """Discount/Gift code."""

    __tablename__ = "discount_codes"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    discount_type: Mapped[DiscountType] = mapped_column(SQLEnum(DiscountType))
    value: Mapped[int] = mapped_column(Integer)  # Percent or Toman amount
    max_uses: Mapped[int] = mapped_column(Integer, default=1)  # 0 = unlimited
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    min_amount: Mapped[int] = mapped_column(Integer, default=0)  # Min order amount
    max_discount: Mapped[int] = mapped_column(Integer, default=0)  # Max discount, 0 = no limit

    # Validity
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expire_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Restrictions
    plan_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Specific plan only
    one_per_user: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self):
        return f"<DiscountCode(code={self.code}, type={self.discount_type}, value={self.value})>"

    @property
    def is_valid(self) -> bool:
        if not self.is_active:
            return False
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        if self.expire_date:
            from datetime import timezone
            if datetime.now(timezone.utc) > self.expire_date:
                return False
        return True

    def calculate_discount(self, amount: int) -> int:
        """Calculate discount amount for given order amount."""
        if amount < self.min_amount:
            return 0
        if self.discount_type == DiscountType.PERCENT:
            discount = int(amount * self.value / 100)
        else:
            discount = self.value
        if self.max_discount > 0:
            discount = min(discount, self.max_discount)
        return min(discount, amount)
