"""Dynamic pricing service - automatic discounts based on time/demand."""
from datetime import datetime, timezone
from typing import Optional
from loguru import logger


class DynamicPricingService:
    """Adjust prices based on time of day, demand, and user behavior."""

    # Off-peak hours (local time) - apply discount
    OFF_PEAK_HOURS = list(range(1, 7))  # 1 AM - 6 AM
    OFF_PEAK_DISCOUNT = 10  # percent

    # Low demand days
    LOW_DEMAND_DAYS = [1, 2]  # Monday, Tuesday (0=Monday)
    LOW_DEMAND_DISCOUNT = 5  # percent

    def calculate_discount(self, base_price: int, user_purchases: int = 0) -> dict:
        """Calculate dynamic discount for current time.
        
        Returns: {"final_price": int, "discount_percent": int, "reason": str}
        """
        now = datetime.now(timezone.utc)
        total_discount = 0
        reasons = []

        # Off-peak hour discount
        if now.hour in self.OFF_PEAK_HOURS:
            total_discount += self.OFF_PEAK_DISCOUNT
            reasons.append(f"ساعات کم‌ترافیک ({self.OFF_PEAK_DISCOUNT}%)")

        # Low demand day discount
        if now.weekday() in self.LOW_DEMAND_DAYS:
            total_discount += self.LOW_DEMAND_DISCOUNT
            reasons.append(f"روز کم‌تقاضا ({self.LOW_DEMAND_DISCOUNT}%)")

        # Loyalty discount (returning customers)
        if user_purchases >= 5:
            loyalty_discount = 5
            total_discount += loyalty_discount
            reasons.append(f"مشتری وفادار ({loyalty_discount}%)")

        # Cap at 25%
        total_discount = min(total_discount, 25)

        final_price = int(base_price * (100 - total_discount) / 100)

        return {
            "final_price": final_price,
            "discount_percent": total_discount,
            "reason": " + ".join(reasons) if reasons else "",
            "original_price": base_price,
        }

    def is_off_peak(self) -> bool:
        """Check if current time is off-peak."""
        return datetime.now(timezone.utc).hour in self.OFF_PEAK_HOURS


dynamic_pricing = DynamicPricingService()
