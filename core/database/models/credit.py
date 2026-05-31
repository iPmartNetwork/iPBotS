"""Credit (buy now pay later) system model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, ForeignKey, Boolean, DateTime, BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column
from core.database.models.base import Base


class UserCredit(Base):
    """User credit limit and balance."""
    __tablename__ = "user_credits"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    credit_limit: Mapped[int] = mapped_column(Integer, default=0)  # Max credit in Toman
    used_credit: Mapped[int] = mapped_column(Integer, default=0)  # Currently used
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Eligibility
    min_purchases_required: Mapped[int] = mapped_column(Integer, default=3)
    min_spent_required: Mapped[int] = mapped_column(Integer, default=200000)
    
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    @property
    def available_credit(self) -> int:
        return max(0, self.credit_limit - self.used_credit)
