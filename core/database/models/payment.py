"""Payment model."""

from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, Text, Enum as SQLEnum, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from core.database.models.base import Base


class PaymentStatus(str, enum.Enum):
    """Payment status."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    """Payment methods."""

    ZARINPAL = "zarinpal"
    NOWPAYMENTS = "nowpayments"
    CRYPTOMUS = "cryptomus"
    CARD2CARD = "card2card"
    WALLET = "wallet"
    ADMIN = "admin"  # Manual by admin
    STRIPE = "stripe"
    IDPAY = "idpay"


class Payment(Base):
    """Payment transaction."""

    __tablename__ = "payments"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orders.id"), nullable=True
    )

    # Payment info
    method: Mapped[PaymentMethod] = mapped_column(SQLEnum(PaymentMethod))
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus), default=PaymentStatus.PENDING
    )
    amount: Mapped[int] = mapped_column(Integer)  # Toman
    amount_usd: Mapped[int] = mapped_column(Integer, default=0)  # Cents

    # Gateway info
    gateway_transaction_id: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    gateway_ref_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    gateway_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Card2Card specific
    card_receipt_image: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    card_sender_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Admin
    verified_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    admin_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    order: Mapped[Optional["Order"]] = relationship("Order")

    def __repr__(self):
        return f"<Payment(id={self.id}, method={self.method}, status={self.status})>"
