"""A/B Testing service for optimizing conversion."""
import hashlib
from typing import Optional, Dict, Any

# Re-export model from its proper location
from core.database.models.ab_test import ABTest


def get_variant(user_id: int, test_name: str) -> str:
    """Deterministically assign user to A or B variant."""
    hash_input = f"{user_id}:{test_name}"
    hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
    return "B" if hash_value % 2 == 0 else "A"
