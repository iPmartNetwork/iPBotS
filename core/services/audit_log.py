"""Audit logging service for tracking admin actions."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Integer, BigInteger, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from core.database.models.base import Base
from core.database.engine import get_session


class AuditLog(Base):
    """Audit log entry for admin actions."""

    __tablename__ = "audit_logs"

    admin_id: Mapped[int] = mapped_column(BigInteger)  # Telegram ID
    action: Mapped[str] = mapped_column(String(100))
    target_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class AuditService:
    """Service for recording audit logs."""

    @staticmethod
    async def log(
        admin_id: int,
        action: str,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        details: Optional[str] = None,
    ):
        """Record an audit log entry."""
        async with get_session() as session:
            entry = AuditLog(
                admin_id=admin_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details=details,
            )
            session.add(entry)

    @staticmethod
    async def log_user_action(admin_id: int, action: str, user_id: int, details: str = ""):
        """Log an action on a user."""
        await AuditService.log(
            admin_id=admin_id,
            action=action,
            target_type="user",
            target_id=user_id,
            details=details,
        )

    @staticmethod
    async def log_server_action(admin_id: int, action: str, server_id: int, details: str = ""):
        """Log an action on a server."""
        await AuditService.log(
            admin_id=admin_id,
            action=action,
            target_type="server",
            target_id=server_id,
            details=details,
        )

    @staticmethod
    async def log_payment_action(admin_id: int, action: str, payment_id: int, details: str = ""):
        """Log a payment action."""
        await AuditService.log(
            admin_id=admin_id,
            action=action,
            target_type="payment",
            target_id=payment_id,
            details=details,
        )

    @staticmethod
    async def get_recent_logs(limit: int = 50) -> list:
        """Get recent audit logs."""
        from sqlalchemy import select

        async with get_session() as session:
            stmt = (
                select(AuditLog)
                .order_by(AuditLog.id.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    @staticmethod
    async def get_admin_logs(admin_id: int, limit: int = 20) -> list:
        """Get logs for a specific admin."""
        from sqlalchemy import select

        async with get_session() as session:
            stmt = (
                select(AuditLog)
                .where(AuditLog.admin_id == admin_id)
                .order_by(AuditLog.id.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return result.scalars().all()
