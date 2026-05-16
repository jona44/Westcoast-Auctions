import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ListingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.listing_id = self.scope['url_route']['kwargs']['listing_id']
        self.listing_group_name = f'listing_{self.listing_id}'

        # Join listing group
        await self.channel_layer.group_add(
            self.listing_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave listing group
        await self.channel_layer.group_discard(
            self.listing_group_name,
            self.channel_name
        )

    # Receive message from room group
    async def bid_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_bid'
        }))
