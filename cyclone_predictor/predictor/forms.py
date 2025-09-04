from django import forms
from .models import CyclonePrediction

class CycloneForm(forms.ModelForm):
    class Meta:
        model = CyclonePrediction
        fields = [
            "sea_surface_temp",
            "pressure",
            "humidity",
            "wind_shear",
            "vorticity",
            "latitude",
            "ocean_depth",
            "proximity",
            "disturbance"
        ]
        widgets = {
            "sea_surface_temp": forms.NumberInput(attrs={"step": "0.1", "min": "-2", "max": "40", "placeholder": "Sea surface temperature (°C)"}),
            "pressure": forms.NumberInput(attrs={"step": "0.1", "min": "800", "max": "1100", "placeholder": "Pressure (hPa)"}),
            "humidity": forms.NumberInput(attrs={"step": "0.1", "min": "0", "max": "100", "placeholder": "Humidity (%)"}),
            "wind_shear": forms.NumberInput(attrs={"step": "0.1", "min": "0", "max": "100", "placeholder": "Wind shear"}),
            "vorticity": forms.NumberInput(attrs={"step": "0.0001", "placeholder": "Vorticity (s^-1)"}),
            "latitude": forms.NumberInput(attrs={"step": "0.0001", "min": "-90", "max": "90", "placeholder": "Latitude (°)"}),
            "ocean_depth": forms.NumberInput(attrs={"step": "1", "min": "0", "placeholder": "Ocean depth (m)"}),
            "proximity": forms.NumberInput(attrs={"step": "0.1", "min": "0", "placeholder": "Proximity to land"}),
            "disturbance": forms.NumberInput(attrs={"step": "1", "min": "0", "max": "1", "placeholder": "Disturbance (0 or 1)"}),
        }
        help_texts = {
            "sea_surface_temp": "Sea surface temperature in °C",
            "pressure": "Sea-level pressure in hPa",
            "humidity": "Relative humidity %",
            "wind_shear": "Vertical wind shear (m/s or knots)",
            "vorticity": "Relative vorticity (s^-1)",
            "latitude": "Latitude (degrees)",
            "ocean_depth": "Ocean depth (m)",
            "proximity": "Proximity to land or other metric",
            "disturbance": "Binary indicator: 1 if disturbance present, else 0",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide labels and ensure placeholders exist for all fields
        placeholders = {
            "sea_surface_temp": "Sea surface temperature (°C)",
            "pressure": "Pressure (hPa)",
            "humidity": "Humidity (%)",
            "wind_shear": "Wind shear",
            "vorticity": "Vorticity (s^-1)",
            "latitude": "Latitude (°)",
            "ocean_depth": "Ocean depth (m)",
            "proximity": "Proximity to land",
            "disturbance": "Disturbance (0 or 1)",
        }
        for name, field in self.fields.items():
            field.label = ""
            ph = placeholders.get(name, name.replace('_', ' ').title())
            field.widget.attrs["placeholder"] = ph
