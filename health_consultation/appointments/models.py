from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone


class Appointment(models.Model):
    """Model for health consultation appointments."""
    
    CONSULTATION_TYPE_CHOICES = [
        ('prenatal', 'Prenatal Care'),
        ('child_health', 'Child Health'),
        ('general', 'General Health Concern'),
        ('family_planning', 'Family Planning'),
        ('follow_up', 'Follow-up Checkup'),
        ('immunization', 'Immunization'),
        ('nutrition', 'Nutrition Counseling'),
        ('dental', 'Dental Checkup'),
        ('mental_health', 'Mental Health'),
        ('other', 'Other'),
    ]
    
    CONSULTATION_METHOD_CHOICES = [
        ('video_call', 'Online Video Call'),
        ('voice_call', 'Online Voice Call'),
        ('chat', 'Chat Consultation'),
        ('in_person', 'In-Person Visit'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rescheduled', 'Rescheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    # Relationships
    resident = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resident_appointments',
        limit_choices_to={'role': 'resident'}
    )
    health_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='worker_appointments',
        limit_choices_to={'role': 'health_worker'},
        null=True,
        blank=True
    )
    
    # Appointment Details
    consultation_type = models.CharField(
        max_length=20,
        choices=CONSULTATION_TYPE_CHOICES
    )
    custom_consultation_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Custom consultation type when 'Other' is selected"
    )
    consultation_method = models.CharField(
        max_length=20,
        choices=CONSULTATION_METHOD_CHOICES,
        default='video_call'
    )
    
    # Scheduling
    scheduled_date = models.DateField()
    scheduled_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    
    # Status and Notes
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    reason_for_visit = models.TextField(
        help_text="Brief description of symptoms or reason for consultation"
    )
    symptoms = models.TextField(
        blank=True,
        null=True,
        help_text="List of symptoms (if applicable)"
    )
    
    # Health Worker Notes (filled after consultation)
    consultation_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes from the health worker after consultation"
    )
    diagnosis = models.TextField(
        blank=True,
        null=True
    )
    recommendations = models.TextField(
        blank=True,
        null=True,
        help_text="Recommendations, prescriptions, or follow-up instructions"
    )
    
    # Rescheduling Information
    rescheduled_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rescheduled_to'
    )
    reschedule_reason = models.TextField(
        blank=True,
        null=True
    )
    
    # Cancellation Information
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_appointments'
    )
    cancellation_reason = models.TextField(
        blank=True,
        null=True
    )
    
    # Call Information (for online consultations)
    call_room_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True
    )
    call_started_at = models.DateTimeField(
        null=True,
        blank=True
    )
    call_ended_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-scheduled_date', '-scheduled_time']
        verbose_name = 'Appointment'
        verbose_name_plural = 'Appointments'
    
    def __str__(self):
        return f"{self.consultation_type} - {self.resident.get_full_name()} on {self.scheduled_date}"
    
    def get_absolute_url(self):
        return reverse('appointments:detail', kwargs={'pk': self.pk})
    
    @property
    def is_upcoming(self):
        """Check if appointment is in the future and not cancelled/completed."""
        if self.status in ['cancelled', 'completed', 'no_show']:
            return False
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(self.scheduled_date, self.scheduled_time)
        )
        return appointment_datetime > timezone.now()
    
    @property
    def is_today(self):
        """Check if appointment is scheduled for today."""
        return self.scheduled_date == timezone.now().date()
    
    @property
    def end_time(self):
        """Calculate the end time of the appointment."""
        from datetime import datetime, timedelta
        start_datetime = datetime.combine(self.scheduled_date, self.scheduled_time)
        end_datetime = start_datetime + timedelta(minutes=self.duration_minutes)
        return end_datetime.time()
    
    @property
    def can_be_cancelled(self):
        """Check if appointment can be cancelled."""
        return self.status in ['pending', 'approved']
    
    @property
    def can_be_rescheduled(self):
        """Check if appointment can be rescheduled."""
        return self.status in ['pending', 'approved']
    
    @property
    def is_online_consultation(self):
        """Check if this is an online consultation."""
        return self.consultation_method in ['video_call', 'voice_call', 'chat']
    
    def approve(self, health_worker):
        """Approve the appointment."""
        self.status = 'approved'
        self.health_worker = health_worker
        self.approved_at = timezone.now()
        self.save()
    
    def complete(self):
        """Mark appointment as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        
        # Increment health worker consultation count
        if self.health_worker:
            try:
                self.health_worker.health_worker_profile.increment_consultation_count()
            except:
                pass
    
    def cancel(self, user, reason=None):
        """Cancel the appointment."""
        self.status = 'cancelled'
        self.cancelled_by = user
        self.cancellation_reason = reason
        self.save()
    
    def reschedule(self, new_date, new_time, reason=None):
        """Reschedule the appointment."""
        old_appointment = Appointment.objects.create(
            resident=self.resident,
            health_worker=self.health_worker,
            consultation_type=self.consultation_type,
            consultation_method=self.consultation_method,
            scheduled_date=self.scheduled_date,
            scheduled_time=self.scheduled_time,
            duration_minutes=self.duration_minutes,
            reason_for_visit=self.reason_for_visit,
            symptoms=self.symptoms,
            status='rescheduled',
            rescheduled_from=self,
            reschedule_reason=reason
        )
        
        # Update current appointment with new schedule
        self.scheduled_date = new_date
        self.scheduled_time = new_time
        self.status = 'rescheduled'
        self.reschedule_reason = reason
        self.save()


class AppointmentSlot(models.Model):
    """Available appointment slots for health workers."""
    
    health_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='available_slots',
        limit_choices_to={'role': 'health_worker'}
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['health_worker', 'date', 'start_time']
    
    def __str__(self):
        return f"{self.health_worker.get_full_name()} - {self.date} {self.start_time}"


class ConsultationRecord(models.Model):
    """Record of completed consultations for history tracking."""
    
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='consultation_record'
    )
    resident = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consultation_history',
        limit_choices_to={'role': 'resident'}
    )
    health_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='provided_consultations',
        limit_choices_to={'role': 'health_worker'}
    )
    
    # Consultation Details
    consultation_type = models.CharField(max_length=20)
    consultation_method = models.CharField(max_length=20)
    consultation_date = models.DateField()
    
    # Medical Information
    chief_complaint = models.TextField()
    symptoms_observed = models.TextField(blank=True, null=True)
    diagnosis = models.TextField(blank=True, null=True)
    treatment_provided = models.TextField(blank=True, null=True)
    medications_prescribed = models.TextField(blank=True, null=True)
    recommendations = models.TextField(blank=True, null=True)
    
    # Follow-up
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(blank=True, null=True)
    follow_up_notes = models.TextField(blank=True, null=True)
    
    # Vital Signs (if recorded)
    blood_pressure = models.CharField(max_length=20, blank=True, null=True)
    pulse_rate = models.PositiveIntegerField(blank=True, null=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    respiratory_rate = models.PositiveIntegerField(blank=True, null=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    # Attachments
    attachments = models.FileField(
        upload_to='consultation_attachments/%Y/%m/',
        blank=True,
        null=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-consultation_date']
        verbose_name = 'Consultation Record'
        verbose_name_plural = 'Consultation Records'
    
    def __str__(self):
        return f"Consultation: {self.resident.get_full_name()} - {self.consultation_date}"
