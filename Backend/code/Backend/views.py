from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import MedicalCenterSerializer
from .models import MedicalCenter
from .proposed_hospitals_algorithm import insert_proposed_hospitals_into_object
from .proposed_hospitals_database import insert_hospitals_into_object

class get_medical_centers(APIView):
    def get(self, request):
        centers = MedicalCenter.objects.all()
        centers = centers.filter(is_suggested=False)
        serialized = MedicalCenterSerializer(centers, many=True)
        return Response(serialized.data)
    
class get_proposed_medical_centers(APIView):
    def get(self, request):
        insert_proposed_hospitals_into_object()
        centers = MedicalCenter.objects.all()
        centers = centers.filter(is_suggested=True)
        serialized = MedicalCenterSerializer(centers, many=True)
        return Response(serialized.data)
    