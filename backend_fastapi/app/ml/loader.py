"""ML model loading - preloaded at startup for fast inference."""

import os
from typing import Any, Dict, Optional

import structlog

from app.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# Global model storage (singleton pattern)
_models: Dict[str, Any] = {
    "distilbert": None,
    "distilbert_tokenizer": None,
    "xgboost": None,
    "label_encoder": None,
}

# Model versions for tracking
MODEL_VERSIONS = {
    "distilbert": "v1.0",
    "xgboost": "v1.0",
}


def load_models() -> None:
    """
    Load all ML models at application startup.
    
    This is called during FastAPI lifespan startup to ensure
    models are ready before handling requests.
    """
    global _models

    models_path = settings.ml_models_path

    # Load DistilBERT for text classification
    try:
        _models["distilbert"], _models["distilbert_tokenizer"] = _load_distilbert(
            os.path.join(models_path, "distilbert-model")
        )
        logger.info("DistilBERT model loaded", version=MODEL_VERSIONS["distilbert"])
    except Exception as e:
        logger.error("Failed to load DistilBERT", error=str(e))
        _models["distilbert"] = None
        _models["distilbert_tokenizer"] = None

    # Load XGBoost for productivity prediction
    try:
        _models["xgboost"], _models["label_encoder"] = _load_xgboost(
            os.path.join(models_path, "xgboost_productivity.json")
        )
        logger.info("XGBoost model loaded", version=MODEL_VERSIONS["xgboost"])
    except Exception as e:
        logger.error("Failed to load XGBoost", error=str(e))
        _models["xgboost"] = None
        _models["label_encoder"] = None


def _load_distilbert(model_path: str):
    """Load DistilBERT model and tokenizer."""
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"DistilBERT model not found at {model_path}")

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)

    # Set to evaluation mode
    model.eval()

    return model, tokenizer


def _load_xgboost(model_path: str):
    """Load XGBoost model."""
    import xgboost as xgb
    from sklearn.preprocessing import LabelEncoder

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"XGBoost model not found at {model_path}")

    model = xgb.Booster()
    model.load_model(model_path)

    # Create label encoder for activity labels
    # Labels: study=0, distraction=1, research=2
    label_encoder = LabelEncoder()
    label_encoder.classes_ = ["study", "distraction", "research"]

    return model, label_encoder


def get_models() -> Dict[str, Any]:
    """Get loaded models dictionary."""
    return _models


def get_model_version() -> str:
    """Get combined model version string for tracking."""
    versions = []
    if _models["distilbert"] is not None:
        versions.append(f"distilbert-{MODEL_VERSIONS['distilbert']}")
    if _models["xgboost"] is not None:
        versions.append(f"xgb-{MODEL_VERSIONS['xgboost']}")
    return "+".join(versions) if versions else "none"


def models_ready() -> bool:
    """Check if models are loaded and ready."""
    return _models["distilbert"] is not None and _models["xgboost"] is not None
