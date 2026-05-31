"""A/B Test database model."""

from sqlalchemy import String, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models.base import Base


class ABTest(Base):
    """A/B test experiment model."""

    __tablename__ = "ab_tests"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
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

    @property
    def total_impressions(self) -> int:
        return self.impressions_a + self.impressions_b

    @property
    def total_conversions(self) -> int:
        return self.conversions_a + self.conversions_b
