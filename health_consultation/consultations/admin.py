from django.contrib import admin
from .models import OnlineConsultation, CallLog, ConsultationFeedback


@admin.register(OnlineConsultation)
class OnlineConsultationAdmin(admin.ModelAdmin):
    list_display = [
        'appointment', 'consultation_type', 'status', 'resident_joined', 
        'health_worker_joined', 'duration_display', 'initiated_at'
    ]
    list_filter = ['consultation_type', 'status', 'initiated_at']
    search_fields = [
        'appointment__resident__email', 'appointment__health_worker__email', 'room_id'
    ]
    raw_id_fields = ['appointment', 'resident', 'health_worker']
    date_hierarchy = 'initiated_at'
    ordering = ['-initiated_at']
    
    readonly_fields = ['duration_seconds', 'initiated_at']


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ['consultation', 'event_type', 'user', 'timestamp']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['consultation__room_id', 'user__email']
    raw_id_fields = ['consultation', 'user']
    date_hierarchy = 'timestamp'


@admin.register(ConsultationFeedback)
class ConsultationFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'consultation', 'resident', 'overall_satisfaction', 
        'would_recommend', 'submitted_at'
    ]
    list_filter = ['overall_satisfaction', 'would_recommend', 'submitted_at']
    search_fields = ['consultation__room_id', 'resident__email']
    raw_id_fields = ['consultation', 'resident']
    date_hierarchy = 'submitted_at'
