"""Utility helper functions."""

import hashlib
import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID


def calculate_level(xp: int) -> int:
    """Calculate level from XP using exponential curve."""
    # Level formula: XP needed = level^2 * 100
    # Inverse: level = sqrt(xp / 100)
    return int(math.sqrt(xp / 100))


def xp_for_level(level: int) -> int:
    """Calculate XP required to reach a level."""
    return level * level * 100


def xp_progress_in_level(xp: int) -> Dict[str, int]:
    """Get XP progress within current level."""
    current_level = calculate_level(xp)
    xp_for_current = xp_for_level(current_level)
    xp_for_next = xp_for_level(current_level + 1)

    xp_in_level = xp - xp_for_current
    xp_needed = xp_for_next - xp_for_current

    return {
        "current_level": current_level,
        "xp_in_level": xp_in_level,
        "xp_needed": xp_needed,
        "progress_percent": round((xp_in_level / xp_needed) * 100, 1) if xp_needed > 0 else 100,
    }


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours}h {minutes}m"
        return f"{hours}h"


def get_week_range(date: Optional[datetime] = None) -> tuple:
    """Get start and end of week for a given date."""
    if date is None:
        date = datetime.utcnow()

    # Start of week (Monday)
    week_start = date - timedelta(days=date.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    # End of week (Sunday)
    week_end = week_start + timedelta(days=6)
    week_end = week_end.replace(hour=23, minute=59, second=59, microsecond=999999)

    return week_start, week_end


def generate_hash(content: str) -> str:
    """Generate SHA-256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()


def paginate_list(items: List[Any], skip: int = 0, limit: int = 20) -> Dict[str, Any]:
    """Paginate a list of items."""
    total = len(items)
    paginated = items[skip:skip + limit]

    return {
        "items": paginated,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + limit < total,
    }


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split("/")[0]
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return url


def is_valid_uuid(value: str) -> bool:
    """Check if string is a valid UUID."""
    try:
        UUID(value)
        return True
    except (ValueError, AttributeError):
        return False
