"""OpenAI client with caching and metadata tracking."""

import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import structlog
from openai import OpenAI

from app.config import get_settings
from app.database import SessionLocal
from app.models.gamification import AICache

logger = structlog.get_logger()
settings = get_settings()

# OpenAI client (lazy initialization)
_openai_client: Optional[OpenAI] = None


def get_openai_client() -> OpenAI:
    """Get or create OpenAI client."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def generate_prompt_hash(prompt: str, model: str) -> str:
    """Generate hash for prompt caching."""
    content = f"{model}:{prompt}"
    return hashlib.sha256(content.encode()).hexdigest()[:64]


def get_cached_response(prompt_hash: str) -> Optional[str]:
    """Get cached AI response if available and not expired."""
    db = SessionLocal()
    try:
        cache_entry = db.query(AICache).filter(
            AICache.prompt_hash == prompt_hash,
            (AICache.expires_at.is_(None) | (AICache.expires_at > datetime.utcnow())),
        ).first()

        if cache_entry:
            logger.info("AI cache hit", prompt_hash=prompt_hash[:8])
            return cache_entry.response
        return None
    finally:
        db.close()


def save_to_cache(
    prompt_hash: str,
    model: str,
    response: str,
    tokens_used: int,
    ttl_hours: int = 24,
) -> None:
    """Save AI response to cache."""
    db = SessionLocal()
    try:
        cache_entry = AICache(
            prompt_hash=prompt_hash,
            model=model,
            response=response,
            tokens_used=tokens_used,
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours),
        )
        db.merge(cache_entry)  # Upsert
        db.commit()
        logger.info("AI response cached", prompt_hash=prompt_hash[:8])
    except Exception as e:
        logger.error("Failed to cache AI response", error=str(e))
        db.rollback()
    finally:
        db.close()


async def generate_completion(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 500,
    temperature: float = 0.7,
    use_cache: bool = True,
    cache_ttl_hours: int = 24,
) -> Dict[str, Any]:
    """
    Generate completion from OpenAI with caching.
    
    Args:
        prompt: User prompt
        system_prompt: System prompt for context
        model: OpenAI model to use
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
        use_cache: Whether to use caching
        cache_ttl_hours: Cache TTL in hours
        
    Returns:
        Dictionary with response, model, tokens_used, prompt_hash
    """
    model = model or settings.openai_model
    
    # Check cache
    prompt_hash = generate_prompt_hash(prompt, model)
    if use_cache:
        cached = get_cached_response(prompt_hash)
        if cached:
            return {
                "response": cached,
                "model": model,
                "tokens_used": 0,
                "prompt_hash": prompt_hash,
                "cached": True,
            }

    # Build messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    # Call OpenAI
    try:
        client = get_openai_client()
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        response = completion.choices[0].message.content
        tokens_used = completion.usage.total_tokens if completion.usage else 0

        # Cache the response
        if use_cache and response:
            save_to_cache(prompt_hash, model, response, tokens_used, cache_ttl_hours)

        return {
            "response": response,
            "model": model,
            "tokens_used": tokens_used,
            "prompt_hash": prompt_hash,
            "cached": False,
        }

    except Exception as e:
        logger.error("OpenAI API error", error=str(e))
        raise


async def generate_session_summary_text(
    topic: str,
    duration_minutes: int,
    domains: list,
    productivity_score: Optional[int],
    activity_label: Optional[str],
) -> str:
    """Generate a brief summary for a study session."""
    from app.ai.prompts import SESSION_SUMMARY_PROMPT

    prompt = SESSION_SUMMARY_PROMPT.format(
        topic=topic,
        duration=duration_minutes,
        domains=", ".join(domains[:5]),
        productivity=productivity_score or "N/A",
        activity=activity_label or "N/A",
    )

    result = await generate_completion(
        prompt=prompt,
        system_prompt="You are a productivity assistant. Generate brief, encouraging session summaries.",
        max_tokens=150,
        temperature=0.7,
    )

    return result["response"]


async def generate_task_breakdown_text(
    task_title: str,
    task_description: Optional[str],
    estimated_minutes: Optional[int],
) -> Dict[str, Any]:
    """Break down a complex task into subtasks."""
    from app.ai.prompts import TASK_BREAKDOWN_PROMPT

    prompt = TASK_BREAKDOWN_PROMPT.format(
        title=task_title,
        description=task_description or "No additional description",
        estimated=estimated_minutes or "Unknown",
    )

    result = await generate_completion(
        prompt=prompt,
        system_prompt="You are a productivity assistant. Break down tasks into actionable subtasks with time estimates.",
        max_tokens=500,
        temperature=0.5,
        use_cache=False,  # Task breakdowns should be unique
    )

    # Parse the response (assuming structured format)
    return {
        "raw_response": result["response"],
        "model": result["model"],
        "tokens_used": result["tokens_used"],
    }


async def generate_weekly_summary_text(
    total_hours: float,
    total_sessions: int,
    avg_productivity: int,
    top_topics: list,
    streak: int,
    xp_earned: int,
) -> Dict[str, Any]:
    """Generate weekly productivity summary."""
    from app.ai.prompts import WEEKLY_SUMMARY_PROMPT

    topics_str = ", ".join([f"{t['topic']} ({t['minutes']}min)" for t in top_topics[:5]])

    prompt = WEEKLY_SUMMARY_PROMPT.format(
        hours=total_hours,
        sessions=total_sessions,
        productivity=avg_productivity,
        topics=topics_str,
        streak=streak,
        xp=xp_earned,
    )

    result = await generate_completion(
        prompt=prompt,
        system_prompt="You are a supportive productivity coach. Generate motivating weekly summaries with actionable insights.",
        max_tokens=400,
        temperature=0.7,
        cache_ttl_hours=168,  # Cache for a week
    )

    return {
        "summary": result["response"],
        "model": result["model"],
        "prompt_hash": result["prompt_hash"],
    }
