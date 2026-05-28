"""Base payment service interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class PaymentResult:
    """Payment creation result."""

    success: bool
    payment_url: Optional[str] = None
    transaction_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class VerifyResult:
    """Payment verification result."""

    success: bool
    ref_id: Optional[str] = None
    amount: int = 0
    error: Optional[str] = None


class BasePaymentService(ABC):
    """Abstract base class for payment services."""

    @abstractmethod
    async def create_payment(
        self,
        amount: int,
        description: str,
        order_id: str,
        user_email: Optional[str] = None,
        user_phone: Optional[str] = None,
    ) -> PaymentResult:
        """Create a new payment."""
        ...

    @abstractmethod
    async def verify_payment(
        self, authority: str, amount: int
    ) -> VerifyResult:
        """Verify a payment."""
        ...
