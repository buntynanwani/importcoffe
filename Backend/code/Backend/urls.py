from .views import  get_proposed_medical_centers
from .views import  get_medical_centers
from django.urls import path

urlpatterns = [
    path('get_proposed_medical_centers', get_proposed_medical_centers.as_view(), name = "get_proposed_medical_centers"),
    path('get_medical_centers', get_medical_centers.as_view(), name = "get_medical_centers"),
]
