import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Chat, Message

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat messaging.
    
    URL: ws://localhost:8000/ws/chat/{chat_id}/
    
    Features:
    - Real-time message sending/receiving
    - Typing indicators
    - Read receipts
    - Online status
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'chat_{self.chat_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        # Check if user is part of the chat
        is_participant = await self.check_chat_participant()
        if not is_participant:
            await self.close(code=4003)
            return
        
        # Join chat room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send welcome message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connected to chat {self.chat_id}'
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave chat room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket.
        
        Expected format:
        {
            "type": "chat_message" | "typing" | "read_receipt",
            "message": "text content",
            "message_type": "text" | "image" | "file"
        }
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing_indicator(data)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(data)
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def handle_chat_message(self, data):
        """Handle incoming chat message."""
        message_content = data.get('message', '')
        message_type = data.get('message_type', 'text')
        
        # Save message to database
        message = await self.save_message(message_content, message_type)
        
        if message:
            # Broadcast message to chat room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'sender_id': self.user.id,
                        'sender_name': self.user.get_full_name(),
                        'content': message.content,
                        'message_type': message.message_type,
                        'created_at': message.created_at.isoformat(),
                        'is_read': message.is_read,
                    }
                }
            )
    
    async def handle_typing_indicator(self, data):
        """Handle typing indicator."""
        is_typing = data.get('is_typing', False)
        
        # Broadcast typing indicator to other participants
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'user_name': self.user.get_full_name(),
                'is_typing': is_typing,
            }
        )
    
    async def handle_read_receipt(self, data):
        """Handle read receipt for messages."""
        message_id = data.get('message_id')
        
        if message_id:
            await self.mark_message_as_read(message_id)
            
            # Broadcast read receipt
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'message_id': message_id,
                    'user_id': self.user.id,
                }
            )
    
    # Receive message from room group
    async def chat_message(self, event):
        """Send message to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket."""
        # Don't send typing indicator to the user who is typing
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing'],
            }))
    
    async def read_receipt(self, event):
        """Send read receipt to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
        }))
    
    # Database operations
    @database_sync_to_async
    def check_chat_participant(self):
        """Check if user is participant in the chat."""
        try:
            chat = Chat.objects.get(id=self.chat_id)
            return self.user in [chat.participant_1, chat.participant_2]
        except Chat.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content, message_type):
        """Save message to database."""
        try:
            chat = Chat.objects.get(id=self.chat_id)
            message = Message.objects.create(
                chat=chat,
                sender=self.user,
                content=content,
                message_type=message_type
            )
            return message
        except Exception as e:
            print(f"Error saving message: {e}")
            return None
    
    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        """Mark message as read."""
        try:
            message = Message.objects.get(id=message_id)
            if message.sender != self.user:  # Only receiver can mark as read
                message.mark_as_read()
        except Message.DoesNotExist:
            pass

