from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Notification, NotificationPreference
from .forms import NotificationPreferenceForm


@login_required
def notification_list_view(request):
    """List all notifications for the user."""
    notifications = Notification.objects.filter(recipient=request.user)
    
    # Filter by read status
    filter_type = request.GET.get('filter', 'all')
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
    elif filter_type == 'read':
        notifications = notifications.filter(is_read=True)
    
    notifications = notifications.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Count unread notifications
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    
    context = {
        'page_obj': page_obj,
        'unread_count': unread_count,
        'filter_type': filter_type,
        'total_count': notifications.count(),
    }
    return render(request, 'notifications/list.html', context)


@login_required
def notification_detail_view(request, pk):
    """View a specific notification."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    
    # Mark as read when viewed
    if not notification.is_read:
        notification.mark_as_read()
    
    context = {
        'notification': notification,
    }
    return render(request, 'notifications/detail.html', context)


@login_required
@require_POST
def mark_notification_read_view(request, pk):
    """Mark a specific notification as read."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.mark_as_read()
    
    return JsonResponse({'status': 'success'})


@login_required
@require_POST
def mark_all_read_view(request):
    """Mark all notifications as read."""
    Notification.objects.filter(recipient=request.user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )
    
    messages.success(request, 'All notifications marked as read.')
    return redirect('notifications:list')


@login_required
@require_POST
def delete_notification_view(request, pk):
    """Delete a notification."""
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.delete()
    
    return JsonResponse({'status': 'success'})


@login_required
def preferences_view(request):
    """View and edit notification preferences."""
    preferences, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = NotificationPreferenceForm(request.POST, instance=preferences)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notification preferences updated successfully!')
            return redirect('notifications:preferences')
    else:
        form = NotificationPreferenceForm(instance=preferences)
    
    context = {
        'form': form,
        'preferences': preferences,
    }
    return render(request, 'notifications/preferences.html', context)


@login_required
def get_unread_count_view(request):
    """Get unread notification count (for AJAX polling)."""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})
