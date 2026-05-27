from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse


class ChatMessage(models.Model):
    """Model for storing chat messages between residents and health workers."""
    
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('system', 'System'),
    ]
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    
    # Message content
    content = models.TextField()
    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPE_CHOICES,
        default='text'
    )
    attachment = models.FileField(
        upload_to='chat_attachments/%Y/%m/',
        blank=True,
        null=True
    )
    
    # Status tracking
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Related appointment (if chat is part of a consultation)
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chat_messages'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
    
    def __str__(self):
        return f"Message from {self.sender.get_full_name()} to {self.receiver.get_full_name()}"
    
    def mark_as_read(self):
        """Mark the message as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    @property
    def is_sender_health_worker(self):
        """Check if the sender is a health worker."""
        return self.sender.role == 'health_worker'
    
    @property
    def time_display(self):
        """Format time for display."""
        return self.created_at.strftime('%I:%M %p')
    
    @property
    def date_display(self):
        """Format date for display."""
        today = timezone.now().date()
        if self.created_at.date() == today:
            return 'Today'
        elif self.created_at.date() == today - timezone.timedelta(days=1):
            return 'Yesterday'
        else:
            return self.created_at.strftime('%B %d, %Y')


class ChatRoom(models.Model):
    """Model for chat rooms between residents and health workers."""
    
    ROOM_TYPE_CHOICES = [
        ('general', 'General Consultation'),
        ('appointment', 'Appointment Related'),
        ('follow_up', 'Follow-up'),
        ('emergency', 'Emergency'),
    ]
    
    name = models.CharField(max_length=100, blank=True, null=True)
    resident = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resident_chat_rooms',
        limit_choices_to={'role': 'resident'}
    )
    health_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='worker_chat_rooms',
        limit_choices_to={'role': 'health_worker'}
    )
    room_type = models.CharField(
        max_length=20,
        choices=ROOM_TYPE_CHOICES,
        default='general'
    )
    
    # Related appointment
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chat_room'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['resident', 'health_worker', 'appointment']
        ordering = ['-last_message_at', '-created_at']
        verbose_name = 'Chat Room'
        verbose_name_plural = 'Chat Rooms'
    
    def __str__(self):
        if self.name:
            return self.name
        return f"Chat: {self.resident.get_full_name()} & {self.health_worker.get_full_name()}"

    def get_absolute_url(self):
        return reverse('chat:conversation', kwargs={'room_id': self.pk})
    
    def get_last_message(self):
        """Get the last message in the chat room."""
        return ChatMessage.objects.filter(
            models.Q(sender=self.resident, receiver=self.health_worker) |
            models.Q(sender=self.health_worker, receiver=self.resident)
        ).order_by('-created_at').first()
    
    def get_unread_count(self, user):
        """Get unread message count for a specific user."""
        return ChatMessage.objects.filter(
            receiver=user,
            sender=self.health_worker if user == self.resident else self.resident,
            is_read=False
        ).count()
    
    def update_last_message_time(self):
        """Update the last message timestamp."""
        self.last_message_at = timezone.now()
        self.save(update_fields=['last_message_at'])
    
    def close_room(self):
        """Close the chat room."""
        self.is_active = False
        self.save(update_fields=['is_active'])


class ChatAttachment(models.Model):
    """Model for chat attachments."""
    
    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file = models.FileField(upload_to='chat_attachments/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    file_type = models.CharField(max_length=50)
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Chat Attachment'
        verbose_name_plural = 'Chat Attachments'
    
    def __str__(self):
        return f"Attachment: {self.file_name}"
    
    @property
    def file_size_display(self):
        """Format file size for display."""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
