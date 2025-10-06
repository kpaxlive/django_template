from rest_framework import status, generics, parsers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django.conf import settings
from functools import wraps

from .models import Chat, Message
from .serializers import (
    ChatListSerializer,
    ChatDetailSerializer,
    MessageSerializer,
    CreateMessageSerializer,
    CreateChatSerializer,
)
from src.accounts.responses import success_response, error_response, ResponseCodes

User = get_user_model()


def chat_feature_required(view_func):
    """Decorator to check if chat feature is enabled."""
    @wraps(view_func)
    def wrapped_view(self, request, *args, **kwargs):
        if not getattr(settings, 'ENABLE_CHAT_SYSTEM', True):
            response_data, http_status = error_response(
                error='Chat system is disabled.',
                code='CHAT_FEATURE_DISABLED',
                http_status=status.HTTP_403_FORBIDDEN
            )
            return Response(response_data, status=http_status)
        return view_func(self, request, *args, **kwargs)
    return wrapped_view


@extend_schema(
    tags=['Chat'],
    responses={
        200: ChatListSerializer(many=True),
        403: OpenApiResponse(description='Chat feature disabled'),
    },
)
class ChatListView(APIView):
    """
    GET: List all chats for the current user.
    Returns chats with other participant info, last message, and unread count.
    """
    
    permission_classes = [IsAuthenticated]
    
    @chat_feature_required
    def get(self, request):
        user = request.user
        
        # Get chats where user is a participant and not deleted
        chats = Chat.objects.filter(
            Q(participant_1=user, is_deleted_for_participant_1=False) |
            Q(participant_2=user, is_deleted_for_participant_2=False)
        ).order_by('-updated_at')
        
        serializer = ChatListSerializer(chats, many=True, context={'request': request})
        
        response_data, http_status = success_response(
            message='Chats retrieved successfully.',
            data=serializer.data,
            code=ResponseCodes.SUCCESS
        )
        return Response(response_data, status=http_status)


@extend_schema(
    tags=['Chat'],
    request=CreateChatSerializer,
    responses={
        201: ChatDetailSerializer,
        400: OpenApiResponse(description='Bad Request'),
        403: OpenApiResponse(description='Chat feature disabled'),
    },
)
class CreateChatView(APIView):
    """
    POST: Create a new chat with another user.
    If chat already exists, returns the existing chat.
    """
    
    permission_classes = [IsAuthenticated]
    
    @chat_feature_required
    def post(self, request):
        serializer = CreateChatSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        chat = serializer.save()
        
        detail_serializer = ChatDetailSerializer(chat, context={'request': request})
        
        response_data, http_status = success_response(
            message='Chat created successfully.',
            data=detail_serializer.data,
            code=ResponseCodes.CREATED,
            http_status=status.HTTP_201_CREATED
        )
        return Response(response_data, status=http_status)


@extend_schema(
    tags=['Chat'],
    responses={
        200: ChatDetailSerializer,
        404: OpenApiResponse(description='Chat not found'),
        403: OpenApiResponse(description='Chat feature disabled or access denied'),
    },
)
class ChatDetailView(APIView):
    """
    GET: Get chat details with messages.
    DELETE: Delete chat (for current user only).
    """
    
    permission_classes = [IsAuthenticated]
    
    @chat_feature_required
    def get(self, request, chat_id):
        user = request.user
        
        try:
            chat = Chat.objects.get(
                Q(id=chat_id) &
                (Q(participant_1=user) | Q(participant_2=user))
            )
        except Chat.DoesNotExist:
            response_data, http_status = error_response(
                error='Chat not found.',
                code=ResponseCodes.NOT_FOUND,
                http_status=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=http_status)
        
        # Check if deleted for user
        if chat.is_deleted_for(user):
            response_data, http_status = error_response(
                error='Chat not found.',
                code=ResponseCodes.NOT_FOUND,
                http_status=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=http_status)
        
        serializer = ChatDetailSerializer(chat, context={'request': request})
        
        response_data, http_status = success_response(
            message='Chat retrieved successfully.',
            data=serializer.data,
            code=ResponseCodes.SUCCESS
        )
        return Response(response_data, status=http_status)
    
    @chat_feature_required
    def delete(self, request, chat_id):
        """Delete chat for current user (not for everyone)."""
        user = request.user
        
        try:
            chat = Chat.objects.get(
                Q(id=chat_id) &
                (Q(participant_1=user) | Q(participant_2=user))
            )
        except Chat.DoesNotExist:
            response_data, http_status = error_response(
                error='Chat not found.',
                code=ResponseCodes.NOT_FOUND,
                http_status=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=http_status)
        
        # Mark as deleted for current user
        if user == chat.participant_1:
            chat.is_deleted_for_participant_1 = True
        else:
            chat.is_deleted_for_participant_2 = True
        chat.save()
        
        response_data, http_status = success_response(
            message='Chat deleted successfully.',
            code=ResponseCodes.DELETED
        )
        return Response(response_data, status=http_status)


@extend_schema(
    tags=['Chat'],
    responses={
        200: OpenApiResponse(description='Chat archived/unarchived'),
        404: OpenApiResponse(description='Chat not found'),
        403: OpenApiResponse(description='Chat feature disabled'),
    },
)
class ArchiveChatView(APIView):
    """
    POST: Archive chat for current user.
    DELETE: Unarchive chat for current user.
    """
    
    permission_classes = [IsAuthenticated]
    
    @chat_feature_required
    def post(self, request, chat_id):
        """Archive chat for current user."""
        user = request.user
        
        try:
            chat = Chat.objects.get(
                Q(id=chat_id) &
                (Q(participant_1=user) | Q(participant_2=user))
            )
        except Chat.DoesNotExist:
            response_data, http_status = error_response(
                error='Chat not found.',
                code=ResponseCodes.NOT_FOUND,
                http_status=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=http_status)
        
        # Mark as archived for current user
        if user == chat.participant_1:
            chat.is_archived_for_participant_1 = True
        else:
            chat.is_archived_for_participant_2 = True
        chat.save()
        
        response_data, http_status = success_response(
            message='Chat archived successfully.',
            code=ResponseCodes.SUCCESS
        )
        return Response(response_data, status=http_status)
    
    @chat_feature_required
    def delete(self, request, chat_id):
        """Unarchive chat for current user."""
        user = request.user
        
        try:
            chat = Chat.objects.get(
                Q(id=chat_id) &
                (Q(participant_1=user) | Q(participant_2=user))
            )
        except Chat.DoesNotExist:
            response_data, http_status = error_response(
                error='Chat not found.',
                code=ResponseCodes.NOT_FOUND,
                http_status=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=http_status)
        
        # Mark as not archived for current user
        if user == chat.participant_1:
            chat.is_archived_for_participant_1 = False
        else:
            chat.is_archived_for_participant_2 = False
        chat.save()
        
        response_data, http_status = success_response(
            message='Chat unarchived successfully.',
            code=ResponseCodes.SUCCESS
        )
        return Response(response_data, status=http_status)


@extend_schema(
    tags=['Chat - Messages'],
    responses={
        200: MessageSerializer(many=True),
        404: OpenApiResponse(description='Chat not found'),
        403: OpenApiResponse(description='Chat feature disabled'),
    },
)
class ChatMessagesView(APIView):
    """
    GET: Get all messages in a chat.
    """
    
    permission_classes = [IsAuthenticated]
    
    @chat_feature_required
    def get(self, request, chat_id):
        user = request.user
        
        try:
            chat = Chat.objects.get(
                Q(id=chat_id) &
                (Q(participant_1=user) | Q(participant_2=user))
            )
        except Chat.DoesNotExist:
            response_data, http_status = error_response(
                error='Chat not found.',
                code=ResponseCodes.NOT_FOUND,
                http_status=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=http_status)
        
        # Get messages visible to current user (respects cleared_at)
        cleared_at = chat.get_cleared_at_for(user)
        
        if user == chat.participant_1:
            messages = chat.messages.filter(is_deleted_for_receiver=False)
        else:
            messages = chat.messages.filter(is_deleted_for_sender=False)
        
        # Only get messages after cleared_at
        if cleared_at:
            messages = messages.filter(created_at__gt=cleared_at)
        
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        
        response_data, http_status = success_response(
            message='Messages retrieved successfully.',
            data=serializer.data,
            code=ResponseCodes.SUCCESS
        )
        return Response(response_data, status=http_status)


@extend_schema(
    tags=['Chat - Messages'],
    request=CreateMessageSerializer,
    responses={
        201: MessageSerializer,
        400: OpenApiResponse(description='Bad Request'),
        404: OpenApiResponse(description='Chat not found'),
        403: OpenApiResponse(description='Chat feature disabled'),
    },
)
class SendMessageView(APIView):
    """
    POST: Send a message in a chat.
    Supports text, image, and file messages.
    """
    
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    @chat_feature_required
    def post(self, request, chat_id):
        user = request.user
        
        try:
            chat = Chat.objects.get(
                Q(id=chat_id) &
                (Q(participant_1=user) | Q(participant_2=user))
            )
        except Chat.DoesNotExist:
            response_data, http_status = error_response(
                error='Chat not found.',
                code=ResponseCodes.NOT_FOUND,
                http_status=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=http_status)
        
        serializer = CreateMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create message
        message = Message.objects.create(
            chat=chat,
            sender=user,
            **serializer.validated_data
        )
        
        response_serializer = MessageSerializer(message, context={'request': request})
        
        response_data, http_status = success_response(
            message='Message sent successfully.',
            data=response_serializer.data,
            code=ResponseCodes.CREATED,
            http_status=status.HTTP_201_CREATED
        )
        return Response(response_data, status=http_status)


@extend_schema(
    tags=['Chat - Messages'],
    responses={
        200: OpenApiResponse(description='Messages marked as read'),
        404: OpenApiResponse(description='Chat not found'),
        403: OpenApiResponse(description='Chat feature disabled'),
    },
)
class MarkMessagesAsReadView(APIView):
    """
    POST: Mark all unread messages in a chat as read.
    """
    
    permission_classes = [IsAuthenticated]
    
    @chat_feature_required
    def post(self, request, chat_id):
        user = request.user
        
        try:
            chat = Chat.objects.get(
                Q(id=chat_id) &
                (Q(participant_1=user) | Q(participant_2=user))
            )
        except Chat.DoesNotExist:
            response_data, http_status = error_response(
                error='Chat not found.',
                code=ResponseCodes.NOT_FOUND,
                http_status=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=http_status)
        
        # Get other participant
        other_user = chat.get_other_participant(user)
        
        # Mark all unread messages from other user as read
        unread_messages = chat.messages.filter(
            sender=other_user,
            is_read=False
        )
        
        count = unread_messages.count()
        
        for message in unread_messages:
            message.mark_as_read()
        
        response_data, http_status = success_response(
            message=f'{count} message(s) marked as read.',
            data={'marked_count': count},
            code=ResponseCodes.SUCCESS
        )
        return Response(response_data, status=http_status)


@extend_schema(
    tags=['Chat - Messages'],
    responses={
        200: OpenApiResponse(description='Message deleted'),
        404: OpenApiResponse(description='Message not found'),
        403: OpenApiResponse(description='Chat feature disabled or not sender'),
    },
)
class DeleteMessageView(APIView):
    """
    DELETE: Delete a message (for sender only or for everyone).
    Query param: for_everyone=true to delete for both users.
    """
    
    permission_classes = [IsAuthenticated]
    
    @chat_feature_required
    def delete(self, request, message_id):
        user = request.user
        for_everyone = request.query_params.get('for_everyone', 'false').lower() == 'true'
        
        try:
            message = Message.objects.get(id=message_id)
        except Message.DoesNotExist:
            response_data, http_status = error_response(
                error='Message not found.',
                code=ResponseCodes.NOT_FOUND,
                http_status=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=http_status)
        
        # Check if user is part of the chat
        chat = message.chat
        if user not in [chat.participant_1, chat.participant_2]:
            response_data, http_status = error_response(
                error='Access denied.',
                code=ResponseCodes.PERMISSION_DENIED,
                http_status=status.HTTP_403_FORBIDDEN
            )
            return Response(response_data, status=http_status)
        
        if for_everyone:
            # Only sender can delete for everyone
            if message.sender != user:
                response_data, http_status = error_response(
                    error='Only sender can delete message for everyone.',
                    code=ResponseCodes.PERMISSION_DENIED,
                    http_status=status.HTTP_403_FORBIDDEN
                )
                return Response(response_data, status=http_status)
            message.delete_for_everyone()
            msg = 'Message deleted for everyone.'
        else:
            # Delete for current user only
            if message.sender == user:
                message.delete_for_sender()
            else:
                message.delete_for_receiver()
            msg = 'Message deleted for you.'
        
        response_data, http_status = success_response(
            message=msg,
            code=ResponseCodes.DELETED
        )
        return Response(response_data, status=http_status)


@extend_schema(
    tags=['Chat - Messages'],
    responses={
        200: OpenApiResponse(description='Messages cleared'),
        404: OpenApiResponse(description='Chat not found'),
        403: OpenApiResponse(description='Chat feature disabled'),
    },
)
class ClearMessagesView(APIView):
    """
    POST: Clear all messages in a chat for current user.
    Sets cleared_at timestamp - messages before this time will be hidden.
    """
    
    permission_classes = [IsAuthenticated]
    
    @chat_feature_required
    def post(self, request, chat_id):
        user = request.user
        
        try:
            chat = Chat.objects.get(
                Q(id=chat_id) &
                (Q(participant_1=user) | Q(participant_2=user))
            )
        except Chat.DoesNotExist:
            response_data, http_status = error_response(
                error='Chat not found.',
                code=ResponseCodes.NOT_FOUND,
                http_status=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=http_status)
        
        # Clear messages for current user
        chat.clear_messages_for(user)
        
        response_data, http_status = success_response(
            message='All messages cleared successfully.',
            code=ResponseCodes.SUCCESS
        )
        return Response(response_data, status=http_status)
