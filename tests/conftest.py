"""Shared test fixtures for iPBotS."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


@pytest.fixture
def mock_settings():
    """Mock bot settings."""
    settings = MagicMock()
    settings.BOT_TOKEN = "123456:ABC-DEF"
    settings.ADMIN_IDS = "12345,67890"
    settings.admin_ids_list = [12345, 67890]
    settings.APP_SECRET_KEY = "test-secret-key"
    settings.ZARINPAL_MERCHANT_ID = "test-merchant"
    settings.ZARINPAL_SANDBOX = True
    settings.ZARINPAL_CALLBACK_URL = "http://localhost/callback"
    settings.STRIPE_SECRET_KEY = "sk_test_123"
    settings.STRIPE_CALLBACK_URL = "http://localhost/stripe/callback"
    settings.NOWPAYMENTS_API_KEY = "test-np-key"
    settings.NOWPAYMENTS_IPN_SECRET = "test-ipn-secret"
    settings.database_url = "sqlite+aiosqlite:///test.db"
    settings.redis_url = "redis://localhost:6379/1"
    settings.WEBHOOK_PATH = "/api/telegram/webhook"
    settings.WEBHOOK_PORT = 8443
    return settings


@pytest.fixture
def mock_user():
    """Create a mock user object."""
    user = MagicMock()
    user.id = 1
    user.telegram_id = 123456789
    user.username = "testuser"
    user.full_name = "Test User"
    user.total_purchases = 3
    user.total_spent = 150000
    user.is_active = True
    user.is_banned = False
    user.last_activity = datetime(2026, 5, 20, tzinfo=timezone.utc)
    user.language = "fa"
    user.referral_code = "ABC123"
    user.referred_by_id = None
    return user


@pytest.fixture
def mock_plan():
    """Create a mock plan object."""
    plan = MagicMock()
    plan.id = 1
    plan.name = "پلن تست"
    plan.price = 50000
    plan.final_price = 50000
    plan.data_limit_gb = 10
    plan.duration_days = 30
    plan.is_active = True
    plan.sort_order = 1
    plan.discount_percent = 0
    plan.ip_limit = 2
    plan.description = "پلن تست 10 گیگ"
    return plan


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.execute = AsyncMock()
    session.scalar = AsyncMock(return_value=0)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_bot():
    """Create a mock bot instance."""
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    bot.send_document = AsyncMock()
    return bot
