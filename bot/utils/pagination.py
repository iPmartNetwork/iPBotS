"""Pagination utility for inline keyboards."""

from typing import List, Any
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def paginate_items(
    items: List[Any],
    page: int = 1,
    per_page: int = 8,
) -> tuple:
    """Paginate a list of items.
    
    Returns: (page_items, total_pages, current_page)
    """
    total = len(items)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    return items[start:end], total_pages, page


def add_pagination_buttons(
    builder: InlineKeyboardBuilder,
    current_page: int,
    total_pages: int,
    callback_prefix: str,
):
    """Add pagination navigation buttons to keyboard."""
    if total_pages <= 1:
        return
    
    buttons = []
    if current_page > 1:
        buttons.append(InlineKeyboardButton(
            text="◀️ قبلی",
            callback_data=f"{callback_prefix}:{current_page - 1}"
        ))
    
    buttons.append(InlineKeyboardButton(
        text=f"📄 {current_page}/{total_pages}",
        callback_data="noop"
    ))
    
    if current_page < total_pages:
        buttons.append(InlineKeyboardButton(
            text="بعدی ▶️",
            callback_data=f"{callback_prefix}:{current_page + 1}"
        ))
    
    builder.row(*buttons)
