from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework.exceptions import AuthenticationFailed
from api.authenticate import CustomTokenAuthentication
from .models import Room, Message
from asgiref.sync import sync_to_async
from mongoengine import DoesNotExist
import json

class Reqeust:
    def __init__(self, headers):
        self.headers = headers

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Extract the room name from the URL
        room_id = self.scope['url_route']['kwargs'].get('room_id', None)
        # Extract the token from the URL
        token = self.scope['query_string'].decode().split('token=')[1] if 'token=' in self.scope['query_string'].decode() else None
        
        if not token:
            await self.close()
            return

        self.user = self.authenticate_user(token)
        if not self.user:
            await self.close()
            return

        try:
            self.room = Room.objects.get(id=room_id)
        except DoesNotExist:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            f'{self.room.id}',
            self.channel_name
        )
        await self.accept()
        print("WebSocket connected")

    async def receive(self, text_data=None, bytes_data=None):
        # Handle incoming data
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')

        # Save message to the room
        if self.room:
            await sync_to_async(self.save_message)(message, self.room)
        
        # Send the message to the room group
        await self.channel_layer.group_send(
            f"{self.room.id}",
            {
                'type': 'chat_message',
                'message': message
            }
        )

    async def chat_message(self, event):
        # Send the message to WebSocket
        message = event['message']
        await self.send(text_data=json.dumps({
            'message': message
        }))
    
    async def disconnect(self, close_code):
        # Leave room group
        if self.room:
            await self.channel_layer.group_discard(
                f"{self.room.id}",
                self.channel_name
            )
        print("WebSocket disconnected with code:", close_code)

    def save_message(self, message, room):
        # Save a new message to the room
        msg = Message(sender=self.user, message=message)
        room.add_message(msg)

    def authenticate_user(self, token):
        # Authenticate user with token
        request = Reqeust(headers={
            'token': token
        })
        authentication_class = CustomTokenAuthentication()
        (user, _) = authentication_class.authenticate(request)
        return user