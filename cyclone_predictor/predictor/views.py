from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from .forms import CycloneForm
from .models import CyclonePrediction
from .services import predict as run_prediction, load_model

import json

# Optionally touch-load the model once on import to surface errors early (non-fatal for UI)
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
            features = [
                data["sea_surface_temp"],
                data["pressure"],
                data["humidity"],
                data["wind_shear"],
                data["vorticity"],
                data["latitude"],
                data["ocean_depth"],
                data["proximity"],
                data["disturbance"],
            ]
            try:
                y, proba = run_prediction(features)
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


# Simple JSON API endpoint for programmatic predictions
@csrf_exempt
@require_http_methods(["POST"])
def api_predict(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
        required = [
            "sea_surface_temp", "pressure", "humidity", "wind_shear", "vorticity",
            "latitude", "ocean_depth", "proximity", "disturbance"
        ]
        if not all(k in payload for k in required):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        try:
            features = [float(payload[k]) for k in required]
        except Exception:
            return JsonResponse({"error": "Invalid payload types"}, status=400)

        y, proba = run_prediction(features)
        return JsonResponse({
            "prediction": int(y),
            "label": "Cyclone" if y == 1 else "No Cyclone",
            "probability": proba,
        })
    except FileNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"Prediction failed: {e}"}, status=500)
