"""Dedicated IP product model."""
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Boolean, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from core.database.models.base import Base


class DedicatedIP(Base):
    """Dedicated IP address for sale."""
    __tablename__ = "dedicated_ips"

    ip_address: Mapped[str] = mapped_column(String(50))
    server_id: Mapped[int] = mapped_column(ForeignKey("servers.id"))
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    price_monthly: Mapped[int] = mapped_column(Integer)  # Toman per month
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    location: Mapped[str] = mapped_column(String(100), default="")
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
