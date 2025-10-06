from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Chat, Message

User = get_user_model()


class ChatUserSerializer(serializers.ModelSerializer):
    """Serializer for user info in chat context."""
    
    profile_picture_url = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'profile_picture_url', 'bio']
        read_only_fields = fields
    
    def get_profile_picture_url(self, obj):
        """Return full URL for profile picture."""
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return obj.profile_picture.url
        return None
    
    def get_full_name(self, obj):
        """Return user's full name."""
        return obj.get_full_name()


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""
    
    sender_info = ChatUserSerializer(source='sender', read_only=True)
    image_url = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'chat', 'sender', 'sender_info', 'message_type',
            'content', 'image', 'image_url', 'file', 'file_url',
            'created_at', 'updated_at', 'is_read', 'read_at',
            'is_edited', 'edited_at', 'is_mine'
        ]
        read_only_fields = [
            'id', 'sender', 'sender_info', 'created_at', 'updated_at',
            'is_read', 'read_at', 'is_edited', 'edited_at', 'image_url', 'file_url', 'is_mine'
        ]
    
    def get_image_url(self, obj):
        """Return full URL for image."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_file_url(self, obj):
        """Return full URL for file."""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_is_mine(self, obj):
        """Check if message belongs to current user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.sender == request.user
        return False


class CreateMessageSerializer(serializers.ModelSerializer):
    """Serializer for creating a message."""
    
    class Meta:
        model = Message
        fields = ['message_type', 'content', 'image', 'file']
    
    def validate(self, attrs):
        """Validate message content based on type."""
        message_type = attrs.get('message_type', 'text')
        
        if message_type == 'text' and not attrs.get('content'):
            raise serializers.ValidationError({'content': 'Text messages must have content.'})
        if message_type == 'image' and not attrs.get('image'):
            raise serializers.ValidationError({'image': 'Image messages must have an image.'})
        if message_type == 'file' and not attrs.get('file'):
            raise serializers.ValidationError({'file': 'File messages must have a file.'})
        
        return attrs


class LastMessageSerializer(serializers.ModelSerializer):
    """Serializer for last message in chat list."""
    
    class Meta:
        model = Message
        fields = ['id', 'message_type', 'content', 'created_at', 'is_read']
        read_only_fields = fields


class ChatListSerializer(serializers.ModelSerializer):
    """Serializer for chat list with other participant info and last message."""
    
    other_participant = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Chat
        fields = [
            'id', 'other_participant', 'last_message', 'unread_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_other_participant(self, obj):
        """Get the other participant in the chat."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            other_user = obj.get_other_participant(request.user)
            return ChatUserSerializer(other_user, context=self.context).data
        return None
    
    def get_last_message(self, obj):
        """Get the last visible message for current user (respects cleared_at)."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            last_msg = obj.get_last_message_for_user(request.user)
            if last_msg:
                return LastMessageSerializer(last_msg).data
        return None
    
    def get_unread_count(self, obj):
        """Get unread message count for current user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_unread_count(request.user)
        return 0


class ChatDetailSerializer(serializers.ModelSerializer):
    """Serializer for chat detail with full info."""
    
    other_participant = serializers.SerializerMethodField()
    messages = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Chat
        fields = [
            'id', 'other_participant', 'messages', 'unread_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields
    
    def get_other_participant(self, obj):
        """Get the other participant in the chat."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            other_user = obj.get_other_participant(request.user)
            return ChatUserSerializer(other_user, context=self.context).data
        return None
    
    def get_messages(self, obj):
        """Get messages visible to current user (respects cleared_at and deletion flags)."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            user = request.user
            cleared_at = obj.get_cleared_at_for(user)
            
            # Filter messages based on deletion flags
            if user == obj.participant_1:
                messages = obj.messages.filter(is_deleted_for_receiver=False)
            else:
                messages = obj.messages.filter(is_deleted_for_sender=False)
            
            # Only get messages after cleared_at
            if cleared_at:
                messages = messages.filter(created_at__gt=cleared_at)
            
            return MessageSerializer(messages, many=True, context=self.context).data
        return []
    
    def get_unread_count(self, obj):
        """Get unread message count for current user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_unread_count(request.user)
        return 0


class CreateChatSerializer(serializers.Serializer):
    """Serializer for creating a new chat."""
    
    participant_email = serializers.EmailField(required=True)
    
    def validate_participant_email(self, value):
        """Validate participant email exists."""
        try:
            user = User.objects.get(email=value, is_anonymous=False)
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist.')
        
        # Check if user is trying to chat with themselves
        request = self.context.get('request')
        if request and request.user == user:
            raise serializers.ValidationError('Cannot create a chat with yourself.')
        
        return value
    
    def create(self, validated_data):
        """Create or get existing chat."""
        request = self.context['request']
        user = request.user
        
        participant_email = validated_data['participant_email']
        other_user = User.objects.get(email=participant_email, is_anonymous=False)
        
        # Ensure user1.id < user2.id for consistency
        if user.id < other_user.id:
            participant_1, participant_2 = user, other_user
        else:
            participant_1, participant_2 = other_user, user
        
        # Get or create chat
        chat, created = Chat.objects.get_or_create(
            participant_1=participant_1,
            participant_2=participant_2
        )
        
        return chat

