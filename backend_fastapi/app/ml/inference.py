"""Thread-safe ML inference service.

Uses thread pool executor to prevent blocking the async event loop.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import structlog

from app.config import get_settings
from app.ml.loader import get_models, get_model_version

logger = structlog.get_logger()
settings = get_settings()

# Thread pool for ML inference (CPU-bound operations)
_ml_executor: Optional[ThreadPoolExecutor] = None


def get_ml_executor() -> ThreadPoolExecutor:
    """Get or create the ML thread pool executor."""
    global _ml_executor
    if _ml_executor is None:
        _ml_executor = ThreadPoolExecutor(
            max_workers=settings.ml_thread_pool_size,
            thread_name_prefix="ml_worker",
        )
    return _ml_executor


def classify_activity_sync(text: str) -> Tuple[str, float]:
    """
    Classify activity using DistilBERT (synchronous).
    
    Args:
        text: Text to classify (page title, URL, etc.)
        
    Returns:
        Tuple of (label, confidence)
        Labels: 'study', 'distraction', 'research'
    """
    import torch

    models = get_models()
    model = models["distilbert"]
    tokenizer = models["distilbert_tokenizer"]

    if model is None or tokenizer is None:
        logger.warning("DistilBERT not loaded, returning default")
        return "study", 0.5

    try:
        # Tokenize input
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=128,
            padding=True,
        )

        # Run inference
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)
            pred_idx = torch.argmax(probs, dim=-1).item()
            confidence = probs[0][pred_idx].item()

        # Map index to label
        labels = ["study", "distraction", "research"]
        label = labels[pred_idx] if pred_idx < len(labels) else "study"

        return label, confidence

    except Exception as e:
        logger.error("DistilBERT inference failed", error=str(e))
        return "study", 0.5


def predict_productivity_sync(features: Dict[str, Any]) -> int:
    """
    Predict productivity score using XGBoost (synchronous).
    
    Args:
        features: Dictionary with keys: clicks, keystrokes, time_on_page, activity_label
        
    Returns:
        Productivity score (0-100)
    """
    import xgboost as xgb

    models = get_models()
    model = models["xgboost"]
    label_encoder = models["label_encoder"]

    if model is None:
        logger.warning("XGBoost not loaded, returning default")
        return 50

    try:
        # Encode activity label
        activity_label = features.get("activity_label", "study")
        if activity_label in label_encoder.classes_:
            activity_encoded = label_encoder.transform([activity_label])[0]
        else:
            activity_encoded = 0  # Default to 'study'

        # Prepare feature array
        # Expected order: clicks, keystrokes, time_on_page, activity_label_encoded
        feature_array = np.array([[
            features.get("clicks", 0),
            features.get("keystrokes", 0),
            features.get("time_on_page", 0),
            activity_encoded,
        ]])

        # Create DMatrix for XGBoost
        dmatrix = xgb.DMatrix(feature_array)

        # Predict
        prediction = model.predict(dmatrix)[0]

        # Ensure score is in 0-100 range
        score = int(min(100, max(0, prediction)))

        return score

    except Exception as e:
        logger.error("XGBoost inference failed", error=str(e))
        return 50


async def classify_activity(text: str) -> Tuple[str, float]:
    """
    Classify activity using DistilBERT (async, thread-safe).
    
    Runs inference in thread pool to avoid blocking event loop.
    """
    loop = asyncio.get_event_loop()
    executor = get_ml_executor()

    result = await loop.run_in_executor(executor, classify_activity_sync, text)
    return result


async def predict_productivity(features: Dict[str, Any]) -> int:
    """
    Predict productivity score using XGBoost (async, thread-safe).
    
    Runs inference in thread pool to avoid blocking event loop.
    """
    loop = asyncio.get_event_loop()
    executor = get_ml_executor()

    result = await loop.run_in_executor(executor, predict_productivity_sync, features)
    return result


async def process_session_ml(
    domains: List[str],
    clicks: int,
    keystrokes: int,
    duration: int,
) -> Dict[str, Any]:
    """
    Run full ML pipeline for a session.
    
    Args:
        domains: List of domain/page titles from session
        clicks: Total clicks during session
        keystrokes: Total keystrokes during session
        duration: Session duration in seconds
        
    Returns:
        Dictionary with ML results and tracking info
    """
    # Classify activity based on domains
    # Use most common domain or concatenate for classification
    text = " ".join(domains[:5]) if domains else "unknown"
    activity_label, confidence = await classify_activity(text)

    # Prepare features for productivity prediction
    features = {
        "clicks": clicks,
        "keystrokes": keystrokes,
        "time_on_page": duration,
        "activity_label": activity_label,
    }

    # Predict productivity
    productivity_score = await predict_productivity(features)

    # Calculate focus score (0-1) based on activity ratio
    # Higher for study/research, lower for distraction
    from app.constants import FOCUS_MULTIPLIER_MAX, FOCUS_MULTIPLIER_MIN
    
    focus_multipliers = {"study": 1.0, "research": 0.8, "distraction": 0.3}
    base_focus = focus_multipliers.get(activity_label, 0.5)
    
    # Adjust by confidence and clamp to valid range
    focus_score = base_focus * confidence
    focus_score = max(FOCUS_MULTIPLIER_MIN, min(FOCUS_MULTIPLIER_MAX, focus_score))

    return {
        "activity_label": activity_label,
        "productivity_score": productivity_score,
        "focus_score": round(focus_score, 2),
        "ml_model_version": get_model_version(),
        "ml_features": features,
    }
