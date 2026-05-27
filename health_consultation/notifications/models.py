from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone


class Notification(models.Model):
    """Model for user notifications."""
    
    NOTIFICATION_TYPE_CHOICES = [
        ('appointment_request', 'Appointment Request'),
        ('appointment_approved', 'Appointment Approved'),
        ('appointment_rescheduled', 'Appointment Rescheduled'),
        ('appointment_cancelled', 'Appointment Cancelled'),
        ('appointment_completed', 'Appointment Completed'),
        ('appointment_reminder', 'Appointment Reminder'),
        ('new_message', 'New Message'),
        ('consultation_started', 'Consultation Started'),
        ('consultation_ended', 'Consultation Ended'),
        ('system', 'System Notification'),
        ('general', 'General'),
    ]
    
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPE_CHOICES
    )
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Optional link to related object
    link = models.URLField(blank=True, null=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.title} - {self.recipient.get_full_name()}"
    
    def mark_as_read(self):
        """Mark the notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
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
    
    @property
    def icon_class(self):
        """Get appropriate icon class based on notification type."""
        icon_map = {
            'appointment_request': 'calendar',
            'appointment_approved': 'check-circle',
            'appointment_rescheduled': 'clock',
            'appointment_cancelled': 'x-circle',
            'appointment_completed': 'check',
            'appointment_reminder': 'bell',
            'new_message': 'message-circle',
            'consultation_started': 'video',
            'consultation_ended': 'phone-off',
            'system': 'info',
            'general': 'bell',
        }
        return icon_map.get(self.notification_type, 'bell')
    
    @property
    def color_class(self):
        """Get appropriate color class based on notification type."""
        color_map = {
            'appointment_request': 'blue',
            'appointment_approved': 'green',
            'appointment_rescheduled': 'orange',
            'appointment_cancelled': 'red',
            'appointment_completed': 'green',
            'appointment_reminder': 'yellow',
            'new_message': 'purple',
            'consultation_started': 'teal',
            'consultation_ended': 'gray',
            'system': 'blue',
            'general': 'gray',
        }
        return color_map.get(self.notification_type, 'gray')


class NotificationPreference(models.Model):
    """User preferences for notifications."""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Email notifications
    email_appointment_reminders = models.BooleanField(default=True)
    email_appointment_updates = models.BooleanField(default=True)
    email_new_messages = models.BooleanField(default=True)
    email_system_notifications = models.BooleanField(default=True)
    
    # In-app notifications
    in_app_appointment_reminders = models.BooleanField(default=True)
    in_app_appointment_updates = models.BooleanField(default=True)
    in_app_new_messages = models.BooleanField(default=True)
    in_app_system_notifications = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.get_full_name()}"
