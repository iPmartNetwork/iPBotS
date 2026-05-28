"""User repository for database operations."""

from typing import Optional, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.models import User


class UserRepository:
    """Repository for User model operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by internal ID."""
        return await self.session.get(User, user_id)

    async def get_by_referral_code(self, code: str) -> Optional[User]:
        """Get user by referral code."""
        stmt = select(User).where(User.referral_code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_active(self) -> List[User]:
        """Get all active (non-banned) users."""
        stmt = select(User).where(User.is_banned == False)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_total_count(self) -> int:
        """Get total user count."""
        result = await self.session.scalar(select(func.count(User.id)))
        return result or 0

    async def get_referrals(self, user_id: int) -> List[User]:
        """Get user's referrals."""
        stmt = select(User).where(User.referred_by_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def ban_user(self, user_id: int, reason: str) -> bool:
        """Ban a user."""
        user = await self.get_by_id(user_id)
        if user:
            user.is_banned = True
            user.ban_reason = reason
            return True
        return False

    async def unban_user(self, user_id: int) -> bool:
        """Unban a user."""
        user = await self.get_by_id(user_id)
        if user:
            user.is_banned = False
            user.ban_reason = None
            return True
        return False
