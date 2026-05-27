from django.utils import timezone
from .models import Notification


def create_notification(recipient, notification_type, title, message, link=None):
    """
    Utility function to create a notification.
    
    Args:
        recipient: User to receive the notification
        notification_type: Type of notification (from NOTIFICATION_TYPE_CHOICES)
        title: Notification title
        message: Notification message
        link: Optional URL link
    
    Returns:
        Notification object
    """
    notification = Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        link=link
    )
    
    return notification


def send_bulk_notification(recipients, notification_type, title, message, link=None):
    """
    Send the same notification to multiple recipients.
    
    Args:
        recipients: QuerySet or list of users
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        link: Optional URL link
    
    Returns:
        List of created Notification objects
    """
    notifications = []
    for recipient in recipients:
        notification = create_notification(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link
        )
        notifications.append(notification)
    
    return notifications


def mark_all_as_read(user):
    """Mark all notifications as read for a specific user."""
    Notification.objects.filter(
        recipient=user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())


def delete_old_notifications(days=30):
    """Delete notifications older than specified days."""
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    Notification.objects.filter(created_at__lt=cutoff_date).delete()
