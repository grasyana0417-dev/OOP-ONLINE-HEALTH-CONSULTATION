from django.db import models
from django.conf import settings
from django.utils import timezone


class OnlineConsultation(models.Model):
    """Model for tracking online consultations (video/voice calls)."""
    
    CONSULTATION_TYPE_CHOICES = [
        ('video', 'Video Call'),
        ('voice', 'Voice Call'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        related_name='online_consultation'
    )
    
    consultation_type = models.CharField(
        max_length=10,
        choices=CONSULTATION_TYPE_CHOICES
    )
    
    room_id = models.CharField(max_length=100, unique=True)
    
    resident = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resident_consultations',
        limit_choices_to={'role': 'resident'}
    )
    
    health_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='worker_consultations',
        limit_choices_to={'role': 'health_worker'}
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Call timestamps
    initiated_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Call duration in seconds
    duration_seconds = models.PositiveIntegerField(default=0)
    
    # Technical details
    resident_joined = models.BooleanField(default=False)
    health_worker_joined = models.BooleanField(default=False)
    resident_left_at = models.DateTimeField(null=True, blank=True)
    health_worker_left_at = models.DateTimeField(null=True, blank=True)
    
    # Quality metrics
    call_quality_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="1-5 rating of call quality"
    )
    technical_issues = models.TextField(
        blank=True,
        null=True,
        help_text="Any technical issues encountered during the call"
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about the consultation"
    )
    
    class Meta:
        ordering = ['-initiated_at']
        verbose_name = 'Online Consultation'
        verbose_name_plural = 'Online Consultations'
    
    def __str__(self):
        return f"{self.consultation_type} - {self.resident.get_full_name()} & {self.health_worker.get_full_name()}"
    
    @property
    def duration_display(self):
        """Format duration for display."""
        if self.duration_seconds < 60:
            return f"{self.duration_seconds}s"
        elif self.duration_seconds < 3600:
            minutes = self.duration_seconds // 60
            seconds = self.duration_seconds % 60
            return f"{minutes}m {seconds}s"
        else:
            hours = self.duration_seconds // 3600
            minutes = (self.duration_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def start_call(self):
        """Start the consultation call."""
        self.status = 'ongoing'
        self.started_at = timezone.now()
        self.save()
    
    def end_call(self):
        """End the consultation call."""
        if self.started_at:
            self.ended_at = timezone.now()
            duration = (self.ended_at - self.started_at).total_seconds()
            self.duration_seconds = int(duration)
        self.status = 'completed'
        self.save()
    
    def participant_joined(self, user):
        """Mark a participant as joined."""
        if user == self.resident:
            self.resident_joined = True
        elif user == self.health_worker:
            self.health_worker_joined = True
        
        # Start call if both have joined
        if self.resident_joined and self.health_worker_joined and self.status == 'pending':
            self.start_call()
        else:
            self.save()
    
    def participant_left(self, user):
        """Mark a participant as left."""
        now = timezone.now()
        if user == self.resident:
            self.resident_left_at = now
        elif user == self.health_worker:
            self.health_worker_left_at = now
        
        # End call if both have left
        if self.resident_left_at and self.health_worker_left_at:
            self.end_call()
        else:
            self.save()


class CallLog(models.Model):
    """Detailed log of call events for debugging and auditing."""
    
    EVENT_TYPE_CHOICES = [
        ('initiated', 'Call Initiated'),
        ('joined', 'Participant Joined'),
        ('left', 'Participant Left'),
        ('ended', 'Call Ended'),
        ('connection_lost', 'Connection Lost'),
        ('reconnected', 'Reconnected'),
        ('error', 'Error'),
    ]
    
    consultation = models.ForeignKey(
        OnlineConsultation,
        on_delete=models.CASCADE,
        related_name='call_logs'
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    event_data = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.event_type} - {self.consultation} at {self.timestamp}"


class ConsultationFeedback(models.Model):
    """Feedback from residents about consultations."""
    
    consultation = models.OneToOneField(
        OnlineConsultation,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    
    resident = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consultation_feedback',
        limit_choices_to={'role': 'resident'}
    )
    
    # Ratings (1-5)
    overall_satisfaction = models.PositiveSmallIntegerField(
        help_text="Overall satisfaction with the consultation (1-5)"
    )
    doctor_competence = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Health worker's competence (1-5)"
    )
    communication_clarity = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Clarity of communication (1-5)"
    )
    technical_quality = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Technical quality of the call (1-5)"
    )
    
    # Feedback text
    would_recommend = models.BooleanField(
        null=True,
        help_text="Would you recommend this service to others?"
    )
    positive_feedback = models.TextField(
        blank=True,
        null=True,
        help_text="What went well?"
    )
    improvement_suggestions = models.TextField(
        blank=True,
        null=True,
        help_text="What could be improved?"
    )
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Consultation Feedback'
        verbose_name_plural = 'Consultation Feedback'
    
    def __str__(self):
        return f"Feedback for {self.consultation} - {self.overall_satisfaction}/5"
