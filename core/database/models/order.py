"""Order model."""

from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from core.database.models.base import Base


class OrderStatus(str, enum.Enum):
    """Order status."""

    PENDING = "pending"
    PAID = "paid"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    FAILED = "failed"


class OrderType(str, enum.Enum):
    """Order type."""

    NEW = "new"
    RENEW = "renew"
    UPGRADE = "upgrade"
    WALLET_CHARGE = "wallet_charge"


class Order(Base):
    """Purchase order."""

    __tablename__ = "orders"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    plan_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("plans.id"), nullable=True
    )

    # Order details
    order_type: Mapped[OrderType] = mapped_column(SQLEnum(OrderType))
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus), default=OrderStatus.PENDING
    )

    # Pricing
    amount: Mapped[int] = mapped_column(Integer)  # Final amount in Toman
    original_amount: Mapped[int] = mapped_column(Integer)  # Before discount
    discount_amount: Mapped[int] = mapped_column(Integer, default=0)
    discount_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Payment
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Subscription reference
    subscription_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("subscriptions.id"), nullable=True
    )

    # Notes
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    plan: Mapped[Optional["Plan"]] = relationship("Plan")

    def __repr__(self):
        return f"<Order(id={self.id}, user_id={self.user_id}, status={self.status})>"
