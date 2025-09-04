from __future__ import annotations

import json
import time
import logging

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, permissions, status

from .forms import CycloneForm
from .models import CyclonePrediction
from .services import predict as run_prediction, load_model

logger = logging.getLogger(__name__)

# Feature order for the model. Keep this consistent with training.
FEATURE_ORDER = [
    "sea_surface_temp",
    "pressure",
    "humidity",
    "wind_shear",
    "vorticity",
    "latitude",
    "ocean_depth",
    "proximity",
    "disturbance",
]

# Optionally warm-load the model once on import to surface errors early (non-fatal for UI)
try:
    load_model()
except Exception:
    # Keep homepage functional even if model is missing; errors will surface on predict
    pass


@require_http_methods(["GET", "POST"])
def home(request):
    prediction_label = None
    probability = None
    error = None

    if request.method == "POST":
        form = CycloneForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            features = [data[f] for f in FEATURE_ORDER]
            try:
                start = time.perf_counter()
                y, proba = run_prediction(features)
                latency_ms = (time.perf_counter() - start) * 1000.0
                logger.info("prediction latency_ms=%.2f", latency_ms)

                probability = proba
                prediction_label = "Cyclone" if y == 1 else "No Cyclone"

                # Save in DB
                cyclone_record = form.save(commit=False)
                cyclone_record.prediction = int(y)
                cyclone_record.save()

                return render(request, "home.html", {
                    "form": CycloneForm(),  # empty form after submission
                    "prediction": prediction_label,
                    "probability": probability,
                    "error": error,
                })
            except FileNotFoundError as e:
                error = str(e)
            except Exception as e:
                logger.exception("prediction failed: %s", e)
                error = f"Prediction failed: {e}"
        else:
            error = "Invalid form submission."
    else:
        form = CycloneForm()

    return render(request, "home.html", {
        "form": form,
        "prediction": prediction_label,
        "probability": probability,
        "error": error,
    })


# Legacy simple JSON endpoint kept for compatibility
@csrf_exempt
@require_http_methods(["POST"])
def api_predict(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
        if not all(k in payload for k in FEATURE_ORDER):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        try:
            features = [float(payload[k]) for k in FEATURE_ORDER]
        except Exception:
            return JsonResponse({"error": "Invalid payload types"}, status=400)

        start = time.perf_counter()
        y, proba = run_prediction(features)
        latency_ms = (time.perf_counter() - start) * 1000.0
        logger.info("prediction latency_ms=%.2f", latency_ms)

        return JsonResponse({
            "prediction": int(y),
            "label": "Cyclone" if y == 1 else "No Cyclone",
            "probability": proba,
            "latency_ms": round(latency_ms, 2),
        })
    except FileNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=500)
    except Exception as e:
        logger.exception("prediction failed: %s", e)
        return JsonResponse({"error": f"Prediction failed: {e}"}, status=500)


# DRF-based API
class PredictionInputSerializer(serializers.Serializer):
    sea_surface_temp = serializers.FloatField()
    pressure = serializers.FloatField()
    humidity = serializers.FloatField()
    wind_shear = serializers.FloatField()
    vorticity = serializers.FloatField()
    latitude = serializers.FloatField()
    ocean_depth = serializers.FloatField()
    proximity = serializers.FloatField()
    disturbance = serializers.IntegerField(min_value=0, max_value=1)


class PredictAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PredictionInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        features = [float(data[k]) for k in FEATURE_ORDER]

        try:
            start = time.perf_counter()
            y, proba = run_prediction(features)
            latency_ms = (time.perf_counter() - start) * 1000.0
            logger.info("prediction latency_ms=%.2f", latency_ms)
            return Response({
                "prediction": int(y),
                "label": "Cyclone" if y == 1 else "No Cyclone",
                "probability": proba,
                "latency_ms": round(latency_ms, 2),
            })
        except FileNotFoundError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.exception("prediction failed: %s", e)
            return Response({"error": f"Prediction failed: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ModelMetadataAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        meta = {
            "feature_order": FEATURE_ORDER,
        }
        try:
            model = load_model()
            # Best-effort extraction of metadata from model attributes if present
            for key in ("version", "trained_at", "feature_order", "classes_"):
                if hasattr(model, key):
                    meta[key] = getattr(model, key)
        except Exception as e:
            meta["warning"] = f"Could not load model metadata: {e}"
        return Response(meta)


class HealthAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        db_ok = True
        model_ok = True
        try:
            CyclonePrediction.objects.exists()
        except Exception:
            db_ok = False
        try:
            load_model()
        except Exception:
            model_ok = False
        return Response({
            "ok": db_ok and model_ok,
            "database": db_ok,
            "model_loaded": model_ok,
        })
