from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from .models import Tourist
from .serializers import TouristSerializer

class TouristViewSet(viewsets.ModelViewSet):
    queryset = Tourist.objects.all().order_by('-created_at')
    serializer_class = TouristSerializer

@csrf_exempt
@api_view(['POST'])
def add_tourist(request):
    serializer = TouristSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST', 'GET'])
def panic_button(request):
    # In a real system we'd dispatch alerts, here we return a simple message
    return Response({'message': 'Panic alert sent to nearest authority (demo).'})
