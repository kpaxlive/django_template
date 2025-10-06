from django.contrib import admin
from .models import Chat, Message


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'participant_1', 'participant_2', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['participant_1__email', 'participant_2__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat', 'sender', 'message_type', 'is_read', 'created_at']
    list_filter = ['message_type', 'is_read', 'created_at']
    search_fields = ['content', 'sender__email']
    readonly_fields = ['created_at', 'updated_at', 'read_at']
    ordering = ['-created_at']
