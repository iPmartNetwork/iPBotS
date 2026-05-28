"""Seed database with initial data (categories, plans, configs)."""

import asyncio
from datetime import datetime, timezone

from loguru import logger

from core.database.engine import get_session, create_tables
from core.database.models import (
    PlanCategory,
    Plan,
)
from core.database.models.trial import TrialConfig
from core.database.models.custom_plan import CustomPlanConfig
from core.database.models.loyalty import LoyaltyConfig, LoyaltyReward
from core.database.models.reseller import ResellerLevel
from core.database.models.discount import DiscountCode, DiscountType


async def seed_categories():
    """Create default plan categories."""
    categories = [
        {"name": "اقتصادی", "icon": "💰", "description": "پلن‌های مقرون‌به‌صرفه", "sort_order": 1},
        {"name": "استاندارد", "icon": "📦", "description": "پلن‌های متعادل", "sort_order": 2},
        {"name": "حرفه‌ای", "icon": "⚡", "description": "پلن‌های پرسرعت و حجم بالا", "sort_order": 3},
        {"name": "نامحدود", "icon": "♾️", "description": "بدون محدودیت ترافیک", "sort_order": 4},
    ]

    async with get_session() as session:
        for cat_data in categories:
            cat = PlanCategory(**cat_data)
            session.add(cat)
        logger.info(f"✓ {len(categories)} categories created")


async def seed_plans():
    """Create sample plans."""
    plans = [
        # Economic
        {"name": "پلن 5 گیگ", "category_id": 1, "data_limit_gb": 5, "duration_days": 30, "price": 30000, "ip_limit": 1, "sort_order": 1},
        {"name": "پلن 10 گیگ", "category_id": 1, "data_limit_gb": 10, "duration_days": 30, "price": 50000, "ip_limit": 1, "sort_order": 2},
        {"name": "پلن 20 گیگ", "category_id": 1, "data_limit_gb": 20, "duration_days": 30, "price": 85000, "ip_limit": 1, "sort_order": 3},

        # Standard
        {"name": "پلن 30 گیگ", "category_id": 2, "data_limit_gb": 30, "duration_days": 30, "price": 120000, "ip_limit": 2, "sort_order": 1},
        {"name": "پلن 50 گیگ", "category_id": 2, "data_limit_gb": 50, "duration_days": 30, "price": 180000, "ip_limit": 2, "sort_order": 2},
        {"name": "پلن 50 گیگ (60 روزه)", "category_id": 2, "data_limit_gb": 50, "duration_days": 60, "price": 300000, "ip_limit": 2, "sort_order": 3},

        # Professional
        {"name": "پلن 100 گیگ", "category_id": 3, "data_limit_gb": 100, "duration_days": 30, "price": 300000, "ip_limit": 3, "sort_order": 1},
        {"name": "پلن 200 گیگ", "category_id": 3, "data_limit_gb": 200, "duration_days": 30, "price": 500000, "ip_limit": 3, "sort_order": 2},
        {"name": "پلن 200 گیگ (90 روزه)", "category_id": 3, "data_limit_gb": 200, "duration_days": 90, "price": 1200000, "ip_limit": 3, "discount_percent": 10, "sort_order": 3},

        # Unlimited
        {"name": "نامحدود 30 روزه", "category_id": 4, "data_limit_gb": 0, "duration_days": 30, "price": 400000, "ip_limit": 2, "sort_order": 1},
        {"name": "نامحدود 60 روزه", "category_id": 4, "data_limit_gb": 0, "duration_days": 60, "price": 700000, "ip_limit": 2, "discount_percent": 5, "sort_order": 2},
        {"name": "نامحدود 90 روزه", "category_id": 4, "data_limit_gb": 0, "duration_days": 90, "price": 950000, "ip_limit": 3, "discount_percent": 10, "sort_order": 3},
    ]

    async with get_session() as session:
        for plan_data in plans:
            plan = Plan(**plan_data)
            session.add(plan)
        logger.info(f"✓ {len(plans)} plans created")


async def seed_trial_config():
    """Create trial configuration."""
    async with get_session() as session:
        config = TrialConfig(
            data_limit_gb=1,
            duration_hours=24,
            ip_limit=1,
            inbound_id=1,
            is_active=True,
            max_trials_per_user=1,
        )
        session.add(config)
        logger.info("✓ Trial config created (1GB / 24h)")


async def seed_custom_plan_config():
    """Create custom plan builder configuration."""
    async with get_session() as session:
        config = CustomPlanConfig(
            price_per_gb=4000,
            price_per_day=800,
            price_per_ip=15000,
            min_data_gb=5,
            max_data_gb=500,
            min_duration_days=7,
            max_duration_days=365,
            min_ip_limit=1,
            max_ip_limit=5,
            bulk_discount_threshold_gb=100,
            bulk_discount_percent=10,
            inbound_id=1,
            is_active=True,
        )
        session.add(config)
        logger.info("✓ Custom plan config created")


async def seed_loyalty():
    """Create loyalty system configuration."""
    async with get_session() as session:
        # Config
        config = LoyaltyConfig(
            points_per_purchase_toman=10000,  # 1 point per 10,000 toman
            points_per_referral=50,
            points_per_review=10,
            is_active=True,
        )
        session.add(config)

        # Rewards
        rewards = [
            {"name": "5% تخفیف خرید بعدی", "points_required": 100, "reward_type": "discount_percent", "reward_value": 5, "icon": "🏷️"},
            {"name": "10% تخفیف خرید بعدی", "points_required": 250, "reward_type": "discount_percent", "reward_value": 10, "icon": "🏷️"},
            {"name": "3 روز رایگان اضافه", "points_required": 150, "reward_type": "free_days", "reward_value": 3, "icon": "📅"},
            {"name": "7 روز رایگان اضافه", "points_required": 350, "reward_type": "free_days", "reward_value": 7, "icon": "📅"},
            {"name": "5 GB ترافیک اضافه", "points_required": 200, "reward_type": "extra_traffic", "reward_value": 5, "icon": "📊"},
            {"name": "20 GB ترافیک اضافه", "points_required": 500, "reward_type": "extra_traffic", "reward_value": 20, "icon": "📊"},
            {"name": "20% تخفیف ویژه", "points_required": 1000, "reward_type": "discount_percent", "reward_value": 20, "icon": "💎"},
        ]

        for reward_data in rewards:
            reward = LoyaltyReward(**reward_data)
            session.add(reward)

        logger.info(f"✓ Loyalty config + {len(rewards)} rewards created")


async def seed_reseller_levels():
    """Create reseller levels."""
    levels = [
        {"name": "برنزی", "discount_percent": 10, "min_purchase_amount": 0, "max_users": 30, "sort_order": 1},
        {"name": "نقره‌ای", "discount_percent": 15, "min_purchase_amount": 2000000, "max_users": 100, "sort_order": 2},
        {"name": "طلایی", "discount_percent": 20, "min_purchase_amount": 5000000, "max_users": 300, "can_set_custom_price": True, "sort_order": 3},
        {"name": "الماسی", "discount_percent": 25, "min_purchase_amount": 15000000, "max_users": 1000, "can_set_custom_price": True, "commission_percent": 5, "sort_order": 4},
    ]

    async with get_session() as session:
        for level_data in levels:
            level = ResellerLevel(**level_data)
            session.add(level)
        logger.info(f"✓ {len(levels)} reseller levels created")


async def seed_discount_codes():
    """Create initial discount codes."""
    codes = [
        {"code": "WELCOME20", "discount_type": DiscountType.PERCENT, "value": 20, "max_uses": 0, "one_per_user": True},
        {"code": "FIRST30", "discount_type": DiscountType.PERCENT, "value": 30, "max_uses": 0, "one_per_user": True},
        {"code": "COMEBACK20", "discount_type": DiscountType.PERCENT, "value": 20, "max_uses": 0, "one_per_user": True},
        {"code": "RENEW15", "discount_type": DiscountType.PERCENT, "value": 15, "max_uses": 0, "one_per_user": True},
        {"code": "VIP25", "discount_type": DiscountType.PERCENT, "value": 25, "max_uses": 50, "one_per_user": True},
    ]

    async with get_session() as session:
        for code_data in codes:
            code = DiscountCode(**code_data)
            session.add(code)
        logger.info(f"✓ {len(codes)} discount codes created")


async def run_seed():
    """Run all seed functions."""
    logger.info("🌱 Starting database seed...")

    await create_tables()
    logger.info("✓ Tables created")

    await seed_categories()
    await seed_plans()
    await seed_trial_config()
    await seed_custom_plan_config()
    await seed_loyalty()
    await seed_reseller_levels()
    await seed_discount_codes()

    logger.info("")
    logger.info("🎉 Database seeded successfully!")
    logger.info("")
    logger.info("📋 Summary:")
    logger.info("   • 4 plan categories")
    logger.info("   • 12 plans")
    logger.info("   • 1 trial config (1GB/24h)")
    logger.info("   • 1 custom plan config")
    logger.info("   • 7 loyalty rewards")
    logger.info("   • 4 reseller levels")
    logger.info("   • 5 discount codes")
    logger.info("")
    logger.info("⚠️  Don't forget to add a server via admin panel!")


if __name__ == "__main__":
    asyncio.run(run_seed())
