from django.urls import path
from .views import (
    ChatListView,
    CreateChatView,
    ChatDetailView,
    ChatMessagesView,
    SendMessageView,
    MarkMessagesAsReadView,
    DeleteMessageView,
    ClearMessagesView,
    ArchiveChatView,
)

app_name = 'chat'

urlpatterns = [
    # Chat management
    path('', ChatListView.as_view(), name='chat_list'),
    path('create/', CreateChatView.as_view(), name='create_chat'),
    path('<int:chat_id>/', ChatDetailView.as_view(), name='chat_detail'),
    path('<int:chat_id>/archive/', ArchiveChatView.as_view(), name='archive_chat'),
    path('<int:chat_id>/messages/', ChatMessagesView.as_view(), name='chat_messages'),
    
    # Message management
    path('<int:chat_id>/messages/send/', SendMessageView.as_view(), name='send_message'),
    path('<int:chat_id>/messages/read/', MarkMessagesAsReadView.as_view(), name='mark_messages_read'),
    path('<int:chat_id>/messages/clear/', ClearMessagesView.as_view(), name='clear_messages'),
    path('messages/<int:message_id>/delete/', DeleteMessageView.as_view(), name='delete_message'),
]

