"""Family plan model - one subscription shared by multiple users."""

from typing import Optional, List

from sqlalchemy import Integer, ForeignKey, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database.models.base import Base


class FamilyGroup(Base):
    """Family group - owner + members sharing a subscription."""

    __tablename__ = "family_groups"

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"))
    name: Mapped[str] = mapped_column(String(100), default="خانواده من")
    max_members: Mapped[int] = mapped_column(Integer, default=5)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    owner: Mapped["User"] = relationship("User", foreign_keys=[owner_id])
    members: Mapped[List["FamilyMember"]] = relationship("FamilyMember", back_populates="group")


class FamilyMember(Base):
    """Member of a family group."""

    __tablename__ = "family_members"

    group_id: Mapped[int] = mapped_column(ForeignKey("family_groups.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    group: Mapped["FamilyGroup"] = relationship("FamilyGroup", back_populates="members")
    user: Mapped["User"] = relationship("User")
