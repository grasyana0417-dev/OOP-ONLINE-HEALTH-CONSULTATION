from .models import Notification


def notifications_count(request):
    """Context processor to add unread notification count to all templates."""
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return {
            'unread_notifications_count': unread_count,
            'has_unread_notifications': unread_count > 0,
        }
    return {
        'unread_notifications_count': 0,
        'has_unread_notifications': False,
    }
