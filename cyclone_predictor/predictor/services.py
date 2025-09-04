from __future__ import annotations

from functools import lru_cache
import os
from typing import List, Tuple, Optional

import joblib
import numpy as np
from django.conf import settings


def get_model_path() -> str:
    """Resolve the model path from settings or fallback to default in app data dir."""
    default_path = os.path.join(settings.BASE_DIR, "predictor", "data", "cyclone_model.pkl")
    return getattr(settings, "CYCLONE_MODEL_PATH", default_path)


@lru_cache(maxsize=1)
def load_model():
    """Load and cache the ML model once per process.

    Returns
    -------
    Any
        The deserialized model object.
    Raises
    ------
    FileNotFoundError
        If the model file does not exist.
    Exception
        If joblib fails to load the model file.
    """
    model_path = get_model_path()
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at: {model_path}")
    return joblib.load(model_path)


def _predict_proba_safe(model, X: np.ndarray) -> Optional[float]:
    """Best-effort extraction of positive-class probability.

    Tries predict_proba, then falls back to a hard decision if unavailable.
    Returns a probability in [0,1] if possible, otherwise None.
    """
    try:
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X)
            if proba is not None:
                # Binary classifier convention: class 1 is positive/cyclone
                if proba.ndim == 2 and proba.shape[1] >= 2:
                    return float(proba[:, 1][0])
                if proba.ndim == 1 and proba.size >= 1:
                    return float(proba[0])
    except Exception:
        # Ignore and fall back
        pass

    try:
        # As a last resort, convert class prediction to a pseudo-probability
        y = model.predict(X)[0]
        return 1.0 if int(y) == 1 else 0.0
    except Exception:
        return None


def predict(features: List[float]) -> Tuple[int, Optional[float]]:
    """Run a prediction using the cached model.

    Parameters
    ----------
    features : List[float]
        Ordered feature vector with 9 elements:
        [sea_surface_temp, pressure, humidity, wind_shear, vorticity, latitude, ocean_depth, proximity, disturbance]

    Returns
    -------
    Tuple[int, Optional[float]]
        (predicted_class, probability_of_cyclone) where probability may be None if unavailable.
    """
    model = load_model()
    X = np.asarray([features], dtype=float)
    y = model.predict(X)[0]
    proba = _predict_proba_safe(model, X)
    return int(y), proba
