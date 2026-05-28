"""Ticket support system models."""

from typing import Optional, List

from sqlalchemy import String, Integer, ForeignKey, Text, Enum as SQLEnum, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from core.database.models.base import Base


class TicketStatus(str, enum.Enum):
    """Ticket status."""

    OPEN = "open"
    ANSWERED = "answered"
    WAITING = "waiting"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    """Ticket priority."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Ticket(Base):
    """Support ticket."""

    __tablename__ = "tickets"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subject: Mapped[str] = mapped_column(String(300))
    status: Mapped[TicketStatus] = mapped_column(
        SQLEnum(TicketStatus), default=TicketStatus.OPEN
    )
    priority: Mapped[TicketPriority] = mapped_column(
        SQLEnum(TicketPriority), default=TicketPriority.MEDIUM
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tickets")
    messages: Mapped[List["TicketMessage"]] = relationship(
        "TicketMessage", back_populates="ticket", order_by="TicketMessage.id"
    )

    def __repr__(self):
        return f"<Ticket(id={self.id}, subject={self.subject}, status={self.status})>"


class TicketMessage(Base):
    """Message in a ticket."""

    __tablename__ = "ticket_messages"

    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"))
    sender_id: Mapped[int] = mapped_column(BigInteger)  # Telegram ID
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    message: Mapped[str] = mapped_column(Text)
    file_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="messages")

    def __repr__(self):
        return f"<TicketMessage(id={self.id}, ticket_id={self.ticket_id})>"
