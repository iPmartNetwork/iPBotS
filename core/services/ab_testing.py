"""A/B Testing service for optimizing conversion."""
import hashlib
from typing import Optional, Dict, Any
from sqlalchemy import String, Integer, Boolean, Text, Float
from sqlalchemy.orm import Mapped, mapped_column
from core.database.models.base import Base


class ABTest(Base):
    """A/B test experiment."""
    __tablename__ = "ab_tests"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    variant_a: Mapped[str] = mapped_column(Text)  # Control
    variant_b: Mapped[str] = mapped_column(Text)  # Treatment
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Results
    impressions_a: Mapped[int] = mapped_column(Integer, default=0)
    impressions_b: Mapped[int] = mapped_column(Integer, default=0)
    conversions_a: Mapped[int] = mapped_column(Integer, default=0)
    conversions_b: Mapped[int] = mapped_column(Integer, default=0)

    @property
    def conversion_rate_a(self) -> float:
        if self.impressions_a == 0:
            return 0
        return round(self.conversions_a / self.impressions_a * 100, 2)

    @property
    def conversion_rate_b(self) -> float:
        if self.impressions_b == 0:
            return 0
        return round(self.conversions_b / self.impressions_b * 100, 2)

    @property
    def winner(self) -> str:
        if self.conversion_rate_a > self.conversion_rate_b:
            return "A"
        elif self.conversion_rate_b > self.conversion_rate_a:
            return "B"
        return "tie"


def get_variant(user_id: int, test_name: str) -> str:
    """Deterministically assign user to A or B variant."""
    hash_input = f"{user_id}:{test_name}"
    hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
    return "B" if hash_value % 2 == 0 else "A"
