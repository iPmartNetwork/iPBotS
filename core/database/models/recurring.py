"""Recurring subscription (auto-payment) model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, ForeignKey, Boolean, String, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from core.database.models.base import Base


class RecurringSubscription(Base):
    """Recurring payment subscription - auto-charges wallet monthly."""
    __tablename__ = "recurring_subscriptions"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    server_id: Mapped[Optional[int]] = mapped_column(ForeignKey("servers.id"), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    interval_days: Mapped[int] = mapped_column(Integer, default=30)  # Payment interval
    next_payment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    total_payments: Mapped[int] = mapped_column(Integer, default=0)
    failed_payments: Mapped[int] = mapped_column(Integer, default=0)
    max_failures: Mapped[int] = mapped_column(Integer, default=3)  # Cancel after X failures
    
    payment_method: Mapped[str] = mapped_column(String(50), default="wallet")
    last_payment_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
