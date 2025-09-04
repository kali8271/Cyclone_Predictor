from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('api/predict/', views.api_predict, name="api_predict"),
]