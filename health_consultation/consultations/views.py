from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.db.models import Q
import uuid

from appointments.models import Appointment
from .models import OnlineConsultation, CallLog, ConsultationFeedback
from .forms import ConsultationFeedbackForm


@login_required
def call_room_view(request, appointment_id):
    """View for the online call room."""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Check permissions
    if not (request.user == appointment.resident or 
            request.user == appointment.health_worker):
        return HttpResponseForbidden("You don't have access to this consultation.")
    
    # Check if appointment is approved
    if appointment.status != 'approved':
        messages.error(request, 'This appointment is not yet approved.')
        return redirect('appointments:detail', pk=appointment_id)
    
    # Check if it's an online consultation
    if not appointment.is_online_consultation:
        messages.error(request, 'This is not an online consultation.')
        return redirect('appointments:detail', pk=appointment_id)
    
    # Get or create online consultation record
    consultation, created = OnlineConsultation.objects.get_or_create(
        appointment=appointment,
        defaults={
            'consultation_type': 'video' if appointment.consultation_method == 'video_call' else 'voice',
            'room_id': str(uuid.uuid4()),
            'resident': appointment.resident,
            'health_worker': appointment.health_worker,
        }
    )
    
    # Log user joining
    is_initiator = request.user == appointment.health_worker
    
    context = {
        'appointment': appointment,
        'consultation': consultation,
        'is_initiator': is_initiator,
        'room_id': consultation.room_id,
        'consultation_type': consultation.consultation_type,
    }
    
    return render(request, 'consultations/call_room.html', context)


@login_required
@require_POST
def join_call_view(request, consultation_id):
    """Mark user as joined the call."""
    consultation = get_object_or_404(OnlineConsultation, id=consultation_id)
    
    if not (request.user == consultation.resident or 
            request.user == consultation.health_worker):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Log the join event
    CallLog.objects.create(
        consultation=consultation,
        user=request.user,
        event_type='joined',
        event_data={'user_role': request.user.role}
    )
    
    # Update consultation
    consultation.participant_joined(request.user)
    
    return JsonResponse({
        'status': 'success',
        'participant_joined': True,
        'call_status': consultation.status
    })


@login_required
@require_POST
def leave_call_view(request, consultation_id):
    """Mark user as left the call."""
    consultation = get_object_or_404(OnlineConsultation, id=consultation_id)
    
    if not (request.user == consultation.resident or 
            request.user == consultation.health_worker):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Log the leave event
    CallLog.objects.create(
        consultation=consultation,
        user=request.user,
        event_type='left',
        event_data={'user_role': request.user.role}
    )
    
    # Update consultation
    consultation.participant_left(request.user)
    
    return JsonResponse({
        'status': 'success',
        'call_ended': consultation.status == 'completed'
    })


@login_required
@require_POST
def end_call_view(request, consultation_id):
    """End the call (health worker only)."""
    consultation = get_object_or_404(OnlineConsultation, id=consultation_id)
    
    if request.user != consultation.health_worker:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    # Log the end event
    CallLog.objects.create(
        consultation=consultation,
        user=request.user,
        event_type='ended',
        event_data={'ended_by': 'health_worker'}
    )
    
    # End the consultation
    consultation.end_call()
    
    # Complete the appointment
    consultation.appointment.complete()
    
    return JsonResponse({'status': 'success'})


@login_required
def log_event_view(request, consultation_id):
    """Log a call event."""
    consultation = get_object_or_404(OnlineConsultation, id=consultation_id)
    
    if not (request.user == consultation.resident or 
            request.user == consultation.health_worker):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        event_type = request.POST.get('event_type')
        event_data = request.POST.get('event_data', '{}')
        
        import json
        try:
            event_data_dict = json.loads(event_data)
        except:
            event_data_dict = {}
        
        CallLog.objects.create(
            consultation=consultation,
            user=request.user,
            event_type=event_type,
            event_data=event_data_dict
        )
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'error': 'Invalid method'}, status=400)


@login_required
def feedback_view(request, consultation_id):
    """Submit feedback for a consultation (resident only)."""
    consultation = get_object_or_404(OnlineConsultation, id=consultation_id)
    
    if request.user != consultation.resident:
        return HttpResponseForbidden("Only the resident can submit feedback.")
    
    # Check if feedback already exists
    existing_feedback = ConsultationFeedback.objects.filter(consultation=consultation).first()
    
    if request.method == 'POST':
        form = ConsultationFeedbackForm(request.POST, instance=existing_feedback)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.consultation = consultation
            feedback.resident = request.user
            feedback.save()
            messages.success(request, 'Thank you for your feedback!')
            return redirect('accounts:resident_dashboard')
    else:
        form = ConsultationFeedbackForm(instance=existing_feedback)
    
    context = {
        'form': form,
        'consultation': consultation,
    }
    return render(request, 'consultations/feedback.html', context)


@login_required
def consultation_history_view(request):
    """View consultation history."""
    if request.user.is_resident:
        consultations = OnlineConsultation.objects.filter(
            resident=request.user,
            status='completed'
        )
    elif request.user.is_health_worker:
        consultations = OnlineConsultation.objects.filter(
            health_worker=request.user,
            status='completed'
        )
    else:
        return redirect('accounts:dashboard_redirect')
    
    consultations = consultations.order_by('-initiated_at')
    
    context = {
        'consultations': consultations,
    }
    return render(request, 'consultations/history.html', context)
