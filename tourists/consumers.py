import json
from channels.generic.websocket import AsyncWebsocketConsumer

class PoliceAlertConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Join the police group to receive emergency broadcasts
        await self.channel_layer.group_add("police_alerts", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("police_alerts", self.channel_name)

    # This method is called when a 'RED' status is triggered in services.py
    async def emergency_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'EMERGENCY',
            'traveler_name': event['name'],
            'lat': str(event['lat']),
            'lon': str(event['lon']),
            'id': event['id']
        }))