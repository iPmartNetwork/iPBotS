"""Custom plan builder model."""

from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models.base import Base


class CustomPlanConfig(Base):
    """Configuration for custom plan builder."""

    __tablename__ = "custom_plan_configs"

    # Price per unit
    price_per_gb: Mapped[int] = mapped_column(Integer, default=5000)  # Toman per GB
    price_per_day: Mapped[int] = mapped_column(Integer, default=1000)  # Toman per day
    price_per_ip: Mapped[int] = mapped_column(Integer, default=10000)  # Toman per extra IP

    # Limits
    min_data_gb: Mapped[int] = mapped_column(Integer, default=5)
    max_data_gb: Mapped[int] = mapped_column(Integer, default=500)
    min_duration_days: Mapped[int] = mapped_column(Integer, default=7)
    max_duration_days: Mapped[int] = mapped_column(Integer, default=365)
    min_ip_limit: Mapped[int] = mapped_column(Integer, default=1)
    max_ip_limit: Mapped[int] = mapped_column(Integer, default=5)

    # Discount for bulk
    bulk_discount_threshold_gb: Mapped[int] = mapped_column(Integer, default=100)
    bulk_discount_percent: Mapped[int] = mapped_column(Integer, default=10)

    # Server assignment
    server_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("servers.id"), nullable=True
    )
    inbound_id: Mapped[int] = mapped_column(Integer, default=1)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def calculate_price(self, data_gb: int, duration_days: int, ip_limit: int) -> int:
        """Calculate price for custom plan."""
        base_price = (
            data_gb * self.price_per_gb
            + duration_days * self.price_per_day
            + max(0, ip_limit - 1) * self.price_per_ip
        )

        # Apply bulk discount
        if data_gb >= self.bulk_discount_threshold_gb:
            discount = int(base_price * self.bulk_discount_percent / 100)
            base_price -= discount

        return base_price
