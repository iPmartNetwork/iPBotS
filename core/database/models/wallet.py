"""Wallet and transaction models."""

from typing import Optional, List

from sqlalchemy import String, Integer, ForeignKey, Text, Enum as SQLEnum, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from core.database.models.base import Base


class TransactionType(str, enum.Enum):
    """Wallet transaction type."""

    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    PURCHASE = "purchase"
    REFUND = "refund"
    REFERRAL_BONUS = "referral_bonus"
    ADMIN_CREDIT = "admin_credit"
    ADMIN_DEBIT = "admin_debit"


class Wallet(Base):
    """User wallet."""

    __tablename__ = "wallets"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    balance: Mapped[int] = mapped_column(Integer, default=0)  # Toman
    total_deposited: Mapped[int] = mapped_column(Integer, default=0)
    total_spent: Mapped[int] = mapped_column(Integer, default=0)
    is_frozen: Mapped[bool] = mapped_column(default=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="wallet")
    transactions: Mapped[List["WalletTransaction"]] = relationship(
        "WalletTransaction", back_populates="wallet", order_by="WalletTransaction.id.desc()"
    )

    def __repr__(self):
        return f"<Wallet(user_id={self.user_id}, balance={self.balance})>"


class WalletTransaction(Base):
    """Wallet transaction record."""

    __tablename__ = "wallet_transactions"

    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"))
    transaction_type: Mapped[TransactionType] = mapped_column(SQLEnum(TransactionType))
    amount: Mapped[int] = mapped_column(Integer)  # Always positive
    balance_after: Mapped[int] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Relationships
    wallet: Mapped["Wallet"] = relationship("Wallet", back_populates="transactions")

    def __repr__(self):
        return f"<WalletTransaction(id={self.id}, type={self.transaction_type}, amount={self.amount})>"
