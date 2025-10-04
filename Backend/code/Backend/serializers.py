from rest_framework import serializers
from .models import MedicalCenter

class MedicalCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalCenter
        fields = '__all__'