"""
Shared constants - synced with @dan/shared package.

These values are used for productivity classification, XP calculation,
and session tracking across the DAN platform.
"""

from typing import List

# ============ Domain Classification ============

# Study-related domains (productive)
STUDY_DOMAINS: List[str] = [
    # Learning platforms
    "coursera.org",
    "udemy.com",
    "edx.org",
    "khanacademy.org",
    "brilliant.org",
    "codecademy.com",
    "freecodecamp.org",
    "leetcode.com",
    "hackerrank.com",
    # Documentation
    "developer.mozilla.org",
    "docs.python.org",
    "stackoverflow.com",
    "github.com",
    "gitlab.com",
    # Productivity tools
    "notion.so",
    "docs.google.com",
    "overleaf.com",
    "quizlet.com",
    "anki.com",
    # Research
    "scholar.google.com",
    "arxiv.org",
    "jstor.org",
    "researchgate.net",
    # Note-taking
    "evernote.com",
    "onenote.com",
    "roamresearch.com",
    "obsidian.md",
]

# Entertainment/distraction domains (unproductive)
DISTRACTION_DOMAINS: List[str] = [
    "youtube.com",
    "netflix.com",
    "reddit.com",
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "twitch.tv",
    "discord.com",
    "spotify.com",
]


# ============ XP Calculation ============

XP_PER_MINUTE = 10
FOCUS_MULTIPLIER_MAX = 2.0
FOCUS_MULTIPLIER_MIN = 0.5

# Level thresholds (XP required for each level)
LEVEL_THRESHOLDS: List[int] = [
    0,      # Level 0
    100,    # Level 1
    250,    # Level 2
    500,    # Level 3
    1000,   # Level 4
    2000,   # Level 5
    3500,   # Level 6
    5500,   # Level 7
    8000,   # Level 8
    11000,  # Level 9
    15000,  # Level 10
    20000,  # Level 11
    26000,  # Level 12
    33000,  # Level 13
    41000,  # Level 14
    50000,  # Level 15
]


def calculate_level(xp: int) -> int:
    """Calculate user level from XP using threshold table."""
    level = 0
    for i, threshold in enumerate(LEVEL_THRESHOLDS):
        if xp >= threshold:
            level = i
        else:
            break
    return level


def calculate_xp_for_next_level(current_level: int) -> int:
    """Get XP required for the next level."""
    if current_level + 1 < len(LEVEL_THRESHOLDS):
        return LEVEL_THRESHOLDS[current_level + 1]
    # Beyond max level - use quadratic formula
    return (current_level + 1) ** 2 * 100


# ============ Productivity Weights ============

PRODUCTIVITY_WEIGHTS = {
    "focus": 0.3,
    "consistency": 0.25,
    "depth": 0.25,
    "engagement": 0.2,
}


# ============ Session Tracking ============

IDLE_THRESHOLD_SECONDS = 120  # 2 minutes
TRACKING_INTERVAL_SECONDS = 30
MIN_SESSION_DURATION_SECONDS = 60  # 1 minute
MAX_SESSION_DURATION_SECONDS = 8 * 60 * 60  # 8 hours


# ============ Activity Labels ============

ACTIVITY_LABELS = ["study", "distraction", "research"]


def classify_domain(domain: str) -> str:
    """
    Classify a domain as study, distraction, or neutral.
    
    Args:
        domain: The domain to classify (e.g., "github.com")
        
    Returns:
        "study", "distraction", or "neutral"
    """
    domain = domain.lower().strip()
    
    # Remove www prefix
    if domain.startswith("www."):
        domain = domain[4:]
    
    if any(study in domain for study in STUDY_DOMAINS):
        return "study"
    if any(distraction in domain for distraction in DISTRACTION_DOMAINS):
        return "distraction"
    
    return "neutral"


def calculate_focus_score(
    active_time: int,
    idle_time: int,
    tab_switches: int,
    duration: int,
) -> float:
    """
    Calculate focus score based on session metrics.
    
    Args:
        active_time: Time actively engaged (seconds)
        idle_time: Time idle (seconds)
        tab_switches: Number of tab/window switches
        duration: Total session duration (seconds)
        
    Returns:
        Focus score between 0.0 and 1.0
    """
    if duration <= 0:
        return 0.0
    
    # Active time ratio (0-1)
    active_ratio = active_time / duration if duration > 0 else 0
    
    # Tab switch penalty (more switches = lower focus)
    # Expected: ~1 switch per 5 minutes for focused work
    expected_switches = duration / 300
    switch_ratio = min(1.0, expected_switches / max(tab_switches, 1))
    
    # Idle penalty
    idle_ratio = 1 - (idle_time / duration) if duration > 0 else 0
    
    # Weighted average
    focus = (
        active_ratio * 0.4 +
        switch_ratio * 0.3 +
        idle_ratio * 0.3
    )
    
    return round(min(1.0, max(0.0, focus)), 2)
