"""Pydantic schemas for API documentation."""

from pydantic import BaseModel
from typing import Optional, List


# --- Common ---

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str


# --- Payment Callbacks ---

class PaymentCallbackResponse(BaseModel):
    """Payment callback HTML response info."""
    message: str
    success: bool


# --- WebApp Schemas ---

class WebAppUserResponse(BaseModel):
    """User info for Mini App."""
    id: int
    name: str
    username: Optional[str]
    balance: int
    total_purchases: int
    total_spent: int
    referral_code: str
    referral_count: int
    language: str


class WebAppCategoryResponse(BaseModel):
    """Plan category for Mini App."""
    id: int
    name: str
    icon: str


class WebAppPlanResponse(BaseModel):
    """Plan for Mini App."""
    id: int
    name: str
    data: str
    duration: str
    price: int
    discount: int
    ip_limit: int
    description: Optional[str]


class WebAppServiceResponse(BaseModel):
    """User subscription for Mini App."""
    id: int
    plan_name: str
    is_active: bool
    used_gb: float
    total_gb: str
    traffic_percent: int
    remaining_days: int
    expire_date: str
    sub_url: Optional[str]


class WebAppWalletTransaction(BaseModel):
    """Wallet transaction."""
    type: str
    amount: int
    description: str
    date: str


class WebAppWalletResponse(BaseModel):
    """Wallet info for Mini App."""
    balance: int
    total_deposited: int
    total_spent: int
    transactions: List[WebAppWalletTransaction]


class OrderCreateResponse(BaseModel):
    """Order creation response."""
    order_id: int
    plan_name: str
    original_price: int
    final_price: int
    discount_percent: int
    discount_reason: str
    payment_method: str


class OrderPayResponse(BaseModel):
    """Order payment response."""
    status: str
    payment_url: Optional[str] = None
    message: Optional[str] = None


class OrderStatusResponse(BaseModel):
    """Order status response."""
    id: int
    status: str
    amount: int
    created_at: Optional[str]
