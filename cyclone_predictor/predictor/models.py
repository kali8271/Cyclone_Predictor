from django.db import models

class CyclonePrediction(models.Model):
    sea_surface_temp = models.FloatField()
    pressure = models.FloatField()
    humidity = models.FloatField()
    wind_shear = models.FloatField()
    vorticity = models.FloatField()
    latitude = models.FloatField()
    ocean_depth = models.FloatField()
    proximity = models.FloatField()
    disturbance = models.IntegerField()
    prediction = models.IntegerField()   # 0 = No Cyclone, 1 = Cyclone
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cyclone Prediction ({self.created_at.date()}) → {self.prediction}"
