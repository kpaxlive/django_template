from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError

User = get_user_model()


class Chat(models.Model):
    """
    Chat model representing a conversation between two users.
    Each chat has exactly two participants.
    """
    
    participant_1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chats_as_participant_1',
        help_text='First participant in the chat'
    )
    participant_2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chats_as_participant_2',
        help_text='Second participant in the chat'
    )
    
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    
    # Clear messages timestamps (user cleared all messages before this time)
    cleared_at_for_participant_1 = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Messages before this timestamp are hidden for participant 1'
    )
    cleared_at_for_participant_2 = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Messages before this timestamp are hidden for participant 2'
    )
    
    # Deletion flags (for "delete chat for me" functionality)
    is_deleted_for_participant_1 = models.BooleanField(default=False)
    is_deleted_for_participant_2 = models.BooleanField(default=False)
    
    # Archive flags
    is_archived_for_participant_1 = models.BooleanField(default=False)
    is_archived_for_participant_2 = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Chat'
        verbose_name_plural = 'Chats'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['participant_1', 'participant_2']),
            models.Index(fields=['-updated_at']),
        ]
        # Ensure unique chat between two users
        constraints = [
            models.UniqueConstraint(
                fields=['participant_1', 'participant_2'],
                name='unique_chat_between_users'
            )
        ]
    
    def __str__(self):
        return f'Chat between {self.participant_1} and {self.participant_2}'
    
    def clean(self):
        """Validate that participants are different users."""
        if self.participant_1 == self.participant_2:
            raise ValidationError('Cannot create a chat with yourself.')
    
    def save(self, *args, **kwargs):
        """Override save to ensure participant_1 ID < participant_2 ID for consistency."""
        self.full_clean()
        # Ensure participant_1 always has lower ID than participant_2
        if self.participant_1.id > self.participant_2.id:
            self.participant_1, self.participant_2 = self.participant_2, self.participant_1
        super().save(*args, **kwargs)
    
    def get_other_participant(self, user):
        """Get the other participant in the chat."""
        if user == self.participant_1:
            return self.participant_2
        return self.participant_1
    
    def is_deleted_for(self, user):
        """Check if chat is deleted for a specific user."""
        if user == self.participant_1:
            return self.is_deleted_for_participant_1
        return self.is_deleted_for_participant_2
    
    def is_archived_for(self, user):
        """Check if chat is archived for a specific user."""
        if user == self.participant_1:
            return self.is_archived_for_participant_1
        return self.is_archived_for_participant_2
    
    def get_cleared_at_for(self, user):
        """Get the cleared_at timestamp for a specific user."""
        if user == self.participant_1:
            return self.cleared_at_for_participant_1
        return self.cleared_at_for_participant_2
    
    def clear_messages_for(self, user):
        """Clear all messages for a specific user (sets cleared_at to now)."""
        now = timezone.now()
        if user == self.participant_1:
            self.cleared_at_for_participant_1 = now
        else:
            self.cleared_at_for_participant_2 = now
        self.save(update_fields=[
            'cleared_at_for_participant_1' if user == self.participant_1 
            else 'cleared_at_for_participant_2'
        ])
    
    def get_unread_count(self, user):
        """Get unread message count for a specific user (after cleared_at)."""
        cleared_at = self.get_cleared_at_for(user)
        other_user = self.get_other_participant(user)
        
        queryset = self.messages.filter(
            sender=other_user,
            is_read=False,
            is_deleted_for_receiver=False,
        )
        
        # Only count messages after cleared_at
        if cleared_at:
            queryset = queryset.filter(created_at__gt=cleared_at)
        
        return queryset.count()
    
    def get_last_message_for_user(self, user):
        """Get the last visible message for a specific user."""
        cleared_at = self.get_cleared_at_for(user)
        
        # Filter messages visible to user
        if user == self.participant_1:
            queryset = self.messages.filter(is_deleted_for_receiver=False)
        else:
            queryset = self.messages.filter(is_deleted_for_sender=False)
        
        # Only get messages after cleared_at
        if cleared_at:
            queryset = queryset.filter(created_at__gt=cleared_at)
        
        return queryset.order_by('-created_at').first()
    
    def get_last_message(self):
        """Get the last message in the chat (deprecated, use get_last_message_for_user)."""
        return self.messages.filter(
            models.Q(is_deleted_for_sender=False) | models.Q(is_deleted_for_receiver=False)
        ).order_by('-created_at').first()


class Message(models.Model):
    """
    Message model representing a single message in a chat.
    Supports text, images, and files.
    """
    
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
    ]
    
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text='Chat this message belongs to'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text='User who sent the message'
    )
    
    # Message content
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPE_CHOICES,
        default='text',
        db_index=True
    )
    content = models.TextField(blank=True, help_text='Text content of the message')
    image = models.ImageField(
        upload_to='chat_images/',
        null=True,
        blank=True,
        help_text='Image attachment'
    )
    file = models.FileField(
        upload_to='chat_files/',
        null=True,
        blank=True,
        help_text='File attachment'
    )
    
    # Message metadata
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Read status
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Deletion flags (for "delete for me" / "delete for everyone")
    is_deleted_for_sender = models.BooleanField(default=False)
    is_deleted_for_receiver = models.BooleanField(default=False)
    
    # Edit tracking
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat', 'created_at']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['is_read', 'created_at']),
        ]
    
    def __str__(self):
        if self.message_type == 'text':
            preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
            return f'{self.sender}: {preview}'
        return f'{self.sender}: [{self.message_type}]'
    
    def clean(self):
        """Validate message content based on type."""
        if self.message_type == 'text' and not self.content:
            raise ValidationError('Text messages must have content.')
        if self.message_type == 'image' and not self.image:
            raise ValidationError('Image messages must have an image attachment.')
        if self.message_type == 'file' and not self.file:
            raise ValidationError('File messages must have a file attachment.')
    
    def save(self, *args, **kwargs):
        """Override save to update chat's updated_at."""
        self.full_clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Update chat's updated_at
        if is_new:
            self.chat.save(update_fields=['updated_at'])
    
    def mark_as_read(self):
        """Mark message as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def delete_for_sender(self):
        """Delete message for sender."""
        self.is_deleted_for_sender = True
        self.save(update_fields=['is_deleted_for_sender'])
    
    def delete_for_receiver(self):
        """Delete message for receiver."""
        self.is_deleted_for_receiver = True
        self.save(update_fields=['is_deleted_for_receiver'])
    
    def delete_for_everyone(self):
        """Delete message for both sender and receiver."""
        self.is_deleted_for_sender = True
        self.is_deleted_for_receiver = True
        self.save(update_fields=['is_deleted_for_sender', 'is_deleted_for_receiver'])
    
    def get_receiver(self):
        """Get the receiver of this message."""
        return self.chat.get_other_participant(self.sender)
