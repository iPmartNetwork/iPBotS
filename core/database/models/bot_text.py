"""Bot customizable texts model."""
from typing import Optional
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from core.database.models.base import Base


class BotText(Base):
    """Customizable bot texts that admin can change from bot."""
    __tablename__ = "bot_texts"

    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="general")
