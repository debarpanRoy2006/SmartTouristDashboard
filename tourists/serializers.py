from rest_framework import serializers
from .models import Tourist
class TouristSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tourist
        fields = '__all__'
