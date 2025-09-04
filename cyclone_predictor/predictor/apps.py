from django.apps import AppConfig
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class PredictorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'predictor'

    def ready(self):
        # Optionally preload the ML model on app startup to reduce first-request latency.
        preload = getattr(settings, 'PREDICTOR_PRELOAD_MODEL', True)
        if not preload:
            return
        try:
            from .services import load_model
            load_model()
            logger.info("Predictor: model preloaded successfully.")
        except Exception as exc:
            logger.warning("Predictor: model preload skipped or failed: %s", exc)
