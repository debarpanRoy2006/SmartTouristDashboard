from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # This matches the 'ws://' connection in your policedashboard.html
    re_path(r'ws/tracking/$', consumers.PoliceAlertConsumer.as_asgi()),
]

#this file defines the WebSocket routing for the 'tourists' app. The re_path function is used to specify the URL pattern for WebSocket connections, which in this case is 'ws/tracking/'. When a client connects to this URL, the PoliceAlertConsumer will handle the connection and any messages sent by the client.




