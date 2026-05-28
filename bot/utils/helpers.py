"""Helper utility functions."""

import hashlib
import secrets
import string
from datetime import datetime, timezone


def generate_random_string(length: int = 12) -> str:
    """Generate a random alphanumeric string."""
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable string."""
    if bytes_value == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    value = float(bytes_value)

    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1

    return f"{value:.2f} {units[unit_index]}"


def format_number(number: int) -> str:
    """Format number with comma separator."""
    return f"{number:,}"


def time_ago(dt: datetime) -> str:
    """Get human readable time difference."""
    now = datetime.now(timezone.utc)
    diff = now - dt

    seconds = diff.total_seconds()
    if seconds < 60:
        return "لحظاتی پیش"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} دقیقه پیش"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} ساعت پیش"
    else:
        days = int(seconds / 86400)
        return f"{days} روز پیش"


def hash_string(value: str) -> str:
    """Create SHA256 hash of a string."""
    return hashlib.sha256(value.encode()).hexdigest()


def mask_card_number(card: str) -> str:
    """Mask card number for display."""
    clean = card.replace("-", "").replace(" ", "")
    if len(clean) >= 12:
        return f"{clean[:4]}-****-****-{clean[-4:]}"
    return card
