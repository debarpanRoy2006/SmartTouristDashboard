from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # This matches the 'ws://' connection in your policedashboard.html
    re_path(r'ws/tracking/$', consumers.PoliceAlertConsumer.as_asgi()),
]