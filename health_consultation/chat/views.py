from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone

from accounts.models import User
from appointments.models import Appointment
from .models import ChatMessage, ChatRoom


@login_required
def chat_list_view(request):
    """List all chat conversations for the user."""
    user = request.user
    
    if user.is_resident:
        # Get all chat rooms where user is resident
        chat_rooms = ChatRoom.objects.filter(resident=user, is_active=True)
        template = 'chat/resident_chat_list.html'
    elif user.is_health_worker:
        # Get all chat rooms where user is health worker
        chat_rooms = ChatRoom.objects.filter(health_worker=user, is_active=True)
        template = 'chat/worker_chat_list.html'
    else:
        return redirect('accounts:dashboard_redirect')
    
    # Get unread counts for each room
    for room in chat_rooms:
        room.unread_count = room.get_unread_count(user)
        room.last_message = room.get_last_message()
    
    # Get available health workers for residents to start new chats
    available_workers = None
    if user.is_resident:
        available_workers = User.objects.filter(
            role='health_worker',
            is_active=True
        )
    
    context = {
        'chat_rooms': chat_rooms,
        'available_workers': available_workers,
    }
    return render(request, template, context)


@login_required
def chat_conversation_view(request, room_id):
    """View a specific chat conversation."""
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    
    # Check if user is part of this chat room
    if request.user not in [room.resident, room.health_worker]:
        return HttpResponseForbidden("You don't have access to this chat.")
    
    # Get chat messages
    messages_list = ChatMessage.objects.filter(
        Q(sender=room.resident, receiver=room.health_worker) |
        Q(sender=room.health_worker, receiver=room.resident)
    ).order_by('created_at')
    
    # Mark unread messages as read
    unread_messages = messages_list.filter(receiver=request.user, is_read=False)
    for msg in unread_messages:
        msg.mark_as_read()
    
    # Paginate messages (show last 50, load more on scroll)
    paginator = Paginator(messages_list, 50)
    page_number = request.GET.get('page', paginator.num_pages)
    page_obj = paginator.get_page(page_number)
    
    # Get the other participant
    other_user = room.health_worker if request.user == room.resident else room.resident
    
    # Check if related to appointment
    appointment = room.appointment
    
    context = {
        'room': room,
        'other_user': other_user,
        'chat_messages': page_obj,
        'appointment': appointment,
        'is_health_worker': request.user.is_health_worker,
    }
    return render(request, 'chat/conversation.html', context)


@login_required
def start_chat_view(request, user_id):
    """Start a new chat with a health worker or resident."""
    other_user = get_object_or_404(User, id=user_id, is_active=True)
    
    # Validate that users can chat (one must be resident, one must be health worker)
    current_user = request.user
    
    if current_user.is_resident and other_user.is_health_worker:
        resident = current_user
        health_worker = other_user
    elif current_user.is_health_worker and other_user.is_resident:
        resident = other_user
        health_worker = current_user
    else:
        messages.error(request, "You can only chat between residents and health workers.")
        return redirect('chat:list')
    
    # Check if chat room already exists
    room, created = ChatRoom.objects.get_or_create(
        resident=resident,
        health_worker=health_worker,
        appointment=None,
        defaults={'room_type': 'general'}
    )
    
    if not room.is_active:
        room.is_active = True
        room.save()
    
    return redirect('chat:conversation', room_id=room.id)


@login_required
def consultation_chat_view(request, appointment_id):
    """Start or join a chat consultation for an appointment."""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check permissions
    if not (request.user == appointment.resident or 
            request.user == appointment.health_worker or 
            request.user.is_admin_user):
        return HttpResponseForbidden("You don't have access to this consultation chat.")
    
    if not appointment.is_online_consultation and appointment.consultation_method != 'chat':
        messages.error(request, "This appointment is not scheduled for chat consultation.")
        return redirect('appointments:detail', pk=appointment_id)
    
    # Get or create chat room for this appointment
    room, created = ChatRoom.objects.get_or_create(
        appointment=appointment,
        defaults={
            'resident': appointment.resident,
            'health_worker': appointment.health_worker,
            'room_type': 'appointment',
            'name': f"Consultation: {appointment.consultation_type} - {appointment.scheduled_date}"
        }
    )
    
    if not room.is_active:
        room.is_active = True
        room.save()
    
    return redirect('chat:conversation', room_id=room.id)


@login_required
@require_POST
def send_message_view(request):
    """Send a new message via AJAX."""
    room_id = request.POST.get('room_id')
    content = request.POST.get('content', '').strip()
    
    if not room_id or not content:
        return JsonResponse({'error': 'Missing room_id or content'}, status=400)
    
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    
    # Check if user is part of this room
    if request.user not in [room.resident, room.health_worker]:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Determine receiver
    receiver = room.health_worker if request.user == room.resident else room.resident
    
    # Create the message
    message = ChatMessage.objects.create(
        sender=request.user,
        receiver=receiver,
        content=content,
        message_type='text',
        appointment=room.appointment
    )
    
    # Update room last message time
    room.update_last_message_time()
    
    # Create notification for receiver
    from notifications.utils import create_notification
    create_notification(
        recipient=receiver,
        notification_type='new_message',
        title='New Message',
        message=f'You have a new message from {request.user.get_full_name()}',
        link=room.get_absolute_url() if hasattr(room, 'get_absolute_url') else None
    )
    
    return JsonResponse({
        'status': 'success',
        'message': {
            'id': message.id,
            'content': message.content,
            'sender_name': message.sender.get_full_name(),
            'time': message.time_display,
            'is_sender_health_worker': message.is_sender_health_worker,
        }
    })


@login_required
@require_POST
def send_file_view(request):
    """Send a file attachment via AJAX."""
    room_id = request.POST.get('room_id')
    
    if not room_id or not request.FILES.get('file'):
        return JsonResponse({'error': 'Missing room_id or file'}, status=400)
    
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    
    if request.user not in [room.resident, room.health_worker]:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    receiver = room.health_worker if request.user == room.resident else room.resident
    uploaded_file = request.FILES['file']
    
    # Determine message type based on file
    file_type = 'file'
    if uploaded_file.content_type.startswith('image/'):
        file_type = 'image'
    
    message = ChatMessage.objects.create(
        sender=request.user,
        receiver=receiver,
        content=f"Sent a file: {uploaded_file.name}",
        message_type=file_type,
        attachment=uploaded_file,
        appointment=room.appointment
    )
    
    room.update_last_message_time()
    
    return JsonResponse({
        'status': 'success',
        'message': {
            'id': message.id,
            'content': message.content,
            'sender_name': message.sender.get_full_name(),
            'time': message.time_display,
            'is_sender_health_worker': message.is_sender_health_worker,
            'file_url': message.attachment.url if message.attachment else None,
        }
    })


@login_required
def get_messages_view(request, room_id):
    """Get messages for a chat room via AJAX (for polling)."""
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    
    if request.user not in [room.resident, room.health_worker]:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Get last message ID from request (for fetching new messages)
    last_message_id = request.GET.get('last_id', 0)
    
    messages_list = ChatMessage.objects.filter(
        Q(sender=room.resident, receiver=room.health_worker) |
        Q(sender=room.health_worker, receiver=room.resident),
        id__gt=last_message_id
    ).order_by('created_at')
    
    # Mark messages as read
    unread_messages = messages_list.filter(receiver=request.user, is_read=False)
    for msg in unread_messages:
        msg.mark_as_read()
    
    messages_data = []
    for msg in messages_list:
        messages_data.append({
            'id': msg.id,
            'content': msg.content,
            'sender_name': msg.sender.get_full_name(),
            'sender_id': msg.sender.id,
            'time': msg.time_display,
            'date': msg.date_display,
            'is_sender_health_worker': msg.is_sender_health_worker,
            'is_mine': msg.sender == request.user,
            'message_type': msg.message_type,
            'file_url': msg.attachment.url if msg.attachment else None,
        })
    
    return JsonResponse({
        'status': 'success',
        'messages': messages_data,
        'unread_count': room.get_unread_count(request.user)
    })


@login_required
@require_POST
def mark_messages_read_view(request, room_id):
    """Mark all messages in a room as read."""
    room = get_object_or_404(ChatRoom, id=room_id, is_active=True)
    
    if request.user not in [room.resident, room.health_worker]:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Mark all unread messages as read
    ChatMessage.objects.filter(
        receiver=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    return JsonResponse({'status': 'success'})


@login_required
def chat_history_view(request, user_id):
    """View chat history with a specific user."""
    other_user = get_object_or_404(User, id=user_id, is_active=True)
    
    # Get all messages between these two users
    messages_list = ChatMessage.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by('created_at')
    
    context = {
        'other_user': other_user,
        'chat_messages': messages_list,
        'message_count': messages_list.count(),
    }
    return render(request, 'chat/history.html', context)
