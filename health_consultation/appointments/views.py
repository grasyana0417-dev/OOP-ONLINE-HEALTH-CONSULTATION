from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
import uuid
from datetime import timedelta

from accounts.models import User
from notifications.utils import create_notification
from .models import Appointment, ConsultationRecord
from .forms import (
    AppointmentForm, RescheduleForm, CancellationForm, 
    ConsultationNotesForm, ConsultationRecordForm, AppointmentFilterForm
)

BOOKED_STATUSES = ['pending', 'approved']


def get_available_workers_for_slot(scheduled_date, scheduled_time):
    """Return active/on-duty workers available for a specific date/time slot."""
    booked_worker_ids = Appointment.objects.filter(
        scheduled_date=scheduled_date,
        scheduled_time=scheduled_time,
        status__in=BOOKED_STATUSES,
        health_worker__isnull=False
    ).values_list('health_worker_id', flat=True)

    return User.objects.filter(
        role='health_worker',
        is_available=True,
        is_active=True
    ).exclude(id__in=booked_worker_ids).order_by('first_name', 'last_name')


def is_worker_available_for_slot(worker_id, scheduled_date, scheduled_time):
    return not Appointment.objects.filter(
        health_worker_id=worker_id,
        scheduled_date=scheduled_date,
        scheduled_time=scheduled_time,
        status__in=BOOKED_STATUSES
    ).exists()


@login_required
def appointment_list_view(request):
    """List appointments based on user role."""
    user = request.user
    
    if user.is_resident:
        appointments = Appointment.objects.filter(resident=user)
        template = 'appointments/resident_list.html'
    elif user.is_health_worker:
        # Health workers should only see appointments assigned to them.
        appointments = Appointment.objects.filter(health_worker=user)
        template = 'appointments/worker_list.html'
    elif user.is_admin_user:
        appointments = Appointment.objects.all()
        template = 'appointments/admin_list.html'
    else:
        return redirect('accounts:dashboard_redirect')
    
    # Filter handling
    filter_form = AppointmentFilterForm(request.GET)
    if filter_form.is_valid():
        status = filter_form.cleaned_data.get('status')
        consultation_type = filter_form.cleaned_data.get('consultation_type')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')
        
        if status:
            appointments = appointments.filter(status=status)
        if consultation_type:
            appointments = appointments.filter(consultation_type=consultation_type)
        if date_from:
            appointments = appointments.filter(scheduled_date__gte=date_from)
        if date_to:
            appointments = appointments.filter(scheduled_date__lte=date_to)
    
    appointments = appointments.order_by('-scheduled_date', '-scheduled_time')
    
    # Pagination
    paginator = Paginator(appointments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_count': appointments.count(),
    }
    return render(request, template, context)


@login_required
def appointment_create_view(request):
    """Create a new appointment (Resident only)."""
    if not request.user.is_resident:
        return redirect('accounts:dashboard_redirect')
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.resident = request.user

            # Fixed duration for every consultation slot.
            appointment.duration_minutes = 60

            if not is_worker_available_for_slot(
                appointment.health_worker_id,
                appointment.scheduled_date,
                appointment.scheduled_time
            ):
                messages.error(request, 'Selected health worker is not available for that date/time. Please choose another slot.')
                context = {
                    'form': form,
                    'available_workers': get_available_workers_for_slot(
                        appointment.scheduled_date,
                        appointment.scheduled_time
                    ),
                }
                return render(request, 'appointments/create.html', context)

            appointment.save()
            
            messages.success(request, 'Appointment request submitted successfully! You will be notified once it is approved.')
            return redirect('appointments:list')
    else:
        form = AppointmentForm()
    
    # Initial available health workers list (for default selected time if present).
    available_workers = User.objects.filter(
        role='health_worker',
        is_available=True,
        is_active=True
    ).order_by('first_name', 'last_name')
    
    context = {
        'form': form,
        'available_workers': available_workers,
    }
    return render(request, 'appointments/create.html', context)


@login_required
def available_workers_view(request):
    """Return workers available for a selected date/time slot."""
    if not request.user.is_resident:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    date_str = request.GET.get('date')
    time_str = request.GET.get('time')
    if not date_str or not time_str:
        return JsonResponse({'workers': []})

    try:
        slot_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        slot_time = timezone.datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        return JsonResponse({'workers': []})

    workers = get_available_workers_for_slot(slot_date, slot_time)
    worker_id = request.GET.get('worker_id')
    selected_available = None
    if worker_id and worker_id.isdigit():
        selected_available = is_worker_available_for_slot(int(worker_id), slot_date, slot_time)

    data = [{'id': w.id, 'name': w.get_full_name(), 'email': w.email} for w in workers]
    return JsonResponse({'workers': data, 'selected_available': selected_available})


@login_required
def appointment_detail_view(request, pk):
    """View appointment details."""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check if user has permission to view this appointment
    if not (request.user == appointment.resident or 
            request.user == appointment.health_worker or 
            request.user.is_admin_user):
        return HttpResponseForbidden("You don't have permission to view this appointment.")
    
    context = {
        'appointment': appointment,
        'can_edit': appointment.status in ['pending', 'approved'],
        'can_cancel': appointment.can_be_cancelled,
        'can_reschedule': appointment.can_be_rescheduled,
    }
    return render(request, 'appointments/detail.html', context)


@login_required
def appointment_approve_view(request, pk):
    """Approve an appointment (Assigned Health Worker only)."""
    if not request.user.is_health_worker:
        return redirect('accounts:dashboard_redirect')
    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        status='pending',
        health_worker=request.user
    )

    if request.method == 'POST':
        appointment.approve(request.user)
        
        # Create notification for resident
        create_notification(
            recipient=appointment.resident,
            notification_type='appointment_approved',
            title='Appointment Approved',
            message=f'Your {appointment.get_consultation_type_display()} appointment on {appointment.scheduled_date} has been approved.',
            link=appointment.get_absolute_url()
        )
        
        messages.success(request, 'Appointment approved successfully!')
        return redirect('appointments:detail', pk=pk)
    
    return render(request, 'appointments/approve_confirm.html', {'appointment': appointment})


@login_required
def appointment_reschedule_view(request, pk):
    """Reschedule an appointment."""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check permissions
    if not (request.user == appointment.resident or 
            request.user == appointment.health_worker):
        return HttpResponseForbidden("You don't have permission to reschedule this appointment.")
    
    if not appointment.can_be_rescheduled:
        messages.error(request, 'This appointment cannot be rescheduled.')
        return redirect('appointments:detail', pk=pk)
    
    if request.method == 'POST':
        form = RescheduleForm(request.POST)
        if form.is_valid():
            new_date = form.cleaned_data['new_date']
            new_time = form.cleaned_data['new_time']
            reason = form.cleaned_data['reason']
            
            appointment.reschedule(new_date, new_time, reason)
            
            # Create notification for the other party
            recipient = appointment.health_worker if request.user == appointment.resident else appointment.resident
            create_notification(
                recipient=recipient,
                notification_type='appointment_rescheduled',
                title='Appointment Rescheduled',
                message=f'Your appointment has been rescheduled to {new_date} at {new_time}.',
                link=appointment.get_absolute_url()
            )
            
            messages.success(request, 'Appointment rescheduled successfully!')
            return redirect('appointments:detail', pk=pk)
    else:
        form = RescheduleForm()
    
    context = {
        'form': form,
        'appointment': appointment,
    }
    return render(request, 'appointments/reschedule.html', context)


@login_required
def appointment_cancel_view(request, pk):
    """Cancel an appointment."""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check permissions
    if not (request.user == appointment.resident or 
            request.user == appointment.health_worker):
        return HttpResponseForbidden("You don't have permission to cancel this appointment.")
    
    if not appointment.can_be_cancelled:
        messages.error(request, 'This appointment cannot be cancelled.')
        return redirect('appointments:detail', pk=pk)
    
    if request.method == 'POST':
        form = CancellationForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            appointment.cancel(request.user, reason)
            
            # Create notification for the other party
            recipient = appointment.health_worker if request.user == appointment.resident else appointment.resident
            create_notification(
                recipient=recipient,
                notification_type='appointment_cancelled',
                title='Appointment Cancelled',
                message=f'An appointment has been cancelled.',
                link=None
            )
            
            messages.success(request, 'Appointment cancelled successfully.')
            return redirect('appointments:list')
    else:
        form = CancellationForm()
    
    context = {
        'form': form,
        'appointment': appointment,
    }
    return render(request, 'appointments/cancel.html', context)


@login_required
def appointment_complete_view(request, pk):
    """Mark appointment as completed and add notes (Health Worker only)."""
    if not request.user.is_health_worker:
        return redirect('accounts:dashboard_redirect')
    
    appointment = get_object_or_404(Appointment, pk=pk, health_worker=request.user)
    
    if request.method == 'POST':
        form = ConsultationNotesForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            appointment.complete()
            
            # Create consultation record
            ConsultationRecord.objects.create(
                appointment=appointment,
                resident=appointment.resident,
                health_worker=appointment.health_worker,
                consultation_type=appointment.consultation_type,
                consultation_method=appointment.consultation_method,
                consultation_date=appointment.scheduled_date,
                chief_complaint=appointment.reason_for_visit,
                diagnosis=appointment.diagnosis,
                recommendations=appointment.recommendations
            )
            
            # Create notification for resident
            create_notification(
                recipient=appointment.resident,
                notification_type='appointment_completed',
                title='Consultation Completed',
                message=f'Your consultation has been completed. View your consultation records for details.',
                link=None
            )
            
            messages.success(request, 'Consultation completed and records saved!')
            return redirect('appointments:detail', pk=pk)
    else:
        form = ConsultationNotesForm(instance=appointment)
    
    context = {
        'form': form,
        'appointment': appointment,
    }
    return render(request, 'appointments/complete.html', context)


@login_required
def join_consultation_view(request, pk):
    """Join an online consultation."""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Check permissions
    if not (request.user == appointment.resident or 
            request.user == appointment.health_worker):
        return HttpResponseForbidden("You don't have permission to join this consultation.")
    
    if appointment.status != 'approved':
        messages.error(request, 'This consultation is not yet approved or has been completed/cancelled.')
        return redirect('appointments:detail', pk=pk)
    
    if not appointment.is_online_consultation:
        messages.error(request, 'This is not an online consultation.')
        return redirect('appointments:detail', pk=pk)
    
    # Generate call room ID if not exists
    if not appointment.call_room_id:
        appointment.call_room_id = str(uuid.uuid4())
        appointment.save()
    
    # Determine if user is initiator (health worker) or joiner (resident)
    is_initiator = request.user == appointment.health_worker
    
    context = {
        'appointment': appointment,
        'is_initiator': is_initiator,
        'call_started': bool(appointment.call_started_at),
        'call_room_id': appointment.call_room_id,
        'consultation_method': appointment.consultation_method,
        'jitsi_domain': getattr(settings, 'JITSI_DOMAIN', 'meet.jit.si'),
        'jitsi_app_id': getattr(settings, 'JITSI_APP_ID', ''),
        'jitsi_jwt': getattr(settings, 'JITSI_JWT', ''),
    }
    
    if appointment.consultation_method in ['video_call', 'voice_call']:
        return render(request, 'appointments/call_room.html', context)
    else:
        return redirect('chat:consultation_chat', appointment_id=pk)


@login_required
def start_call_view(request, pk):
    """Start the call and record start time."""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if request.user != appointment.health_worker:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        appointment.call_started_at = timezone.now()
        appointment.save()
        return JsonResponse({'status': 'success', 'started_at': appointment.call_started_at.isoformat()})
    
    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required
def end_call_view(request, pk):
    """End the call and record end time."""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    if not (request.user == appointment.resident or 
            request.user == appointment.health_worker):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        appointment.call_ended_at = timezone.now()
        appointment.save()
        return JsonResponse({'status': 'success', 'ended_at': appointment.call_ended_at.isoformat()})
    
    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required
def call_status_view(request, pk):
    """Return whether call has started for polling clients."""
    appointment = get_object_or_404(Appointment, pk=pk)

    if not (request.user == appointment.resident or
            request.user == appointment.health_worker or
            request.user.is_admin_user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    return JsonResponse({'started': bool(appointment.call_started_at)})


@login_required
def consultation_records_view(request):
    """View consultation records history."""
    if request.user.is_resident:
        records = ConsultationRecord.objects.filter(resident=request.user)
    elif request.user.is_health_worker:
        records = ConsultationRecord.objects.filter(health_worker=request.user)
    elif request.user.is_admin_user:
        records = ConsultationRecord.objects.all()
    else:
        return redirect('accounts:dashboard_redirect')
    
    records = records.order_by('-consultation_date')
    
    context = {
        'records': records,
    }
    return render(request, 'appointments/consultation_records.html', context)


@login_required
def consultation_record_detail_view(request, pk):
    """View a specific consultation record."""
    record = get_object_or_404(ConsultationRecord, pk=pk)
    
    if not (request.user == record.resident or 
            request.user == record.health_worker or 
            request.user.is_admin_user):
        return HttpResponseForbidden("You don't have permission to view this record.")
    
    context = {
        'record': record,
    }
    return render(request, 'appointments/record_detail.html', context)
