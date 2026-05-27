from django.contrib import admin
from .models import Appointment, AppointmentSlot, ConsultationRecord


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'resident', 'health_worker', 'consultation_type', 'scheduled_date', 
        'scheduled_time', 'status', 'is_online_consultation', 'created_at'
    ]
    list_filter = ['status', 'consultation_type', 'consultation_method', 'scheduled_date']
    search_fields = [
        'resident__email', 'resident__first_name', 'resident__last_name',
        'health_worker__email', 'health_worker__first_name', 'health_worker__last_name'
    ]
    raw_id_fields = ['resident', 'health_worker', 'cancelled_by', 'rescheduled_from']
    date_hierarchy = 'scheduled_date'
    ordering = ['-scheduled_date', '-scheduled_time']
    
    fieldsets = (
        ('Appointment Information', {
            'fields': ('resident', 'health_worker', 'consultation_type', 'consultation_method')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'scheduled_time', 'duration_minutes')
        }),
        ('Status & Notes', {
            'fields': ('status', 'reason_for_visit', 'symptoms', 'consultation_notes', 'diagnosis', 'recommendations')
        }),
        ('Call Information', {
            'fields': ('call_room_id', 'call_started_at', 'call_ended_at'),
            'classes': ('collapse',)
        }),
        ('Cancellation/Rescheduling', {
            'fields': ('cancelled_by', 'cancellation_reason', 'rescheduled_from', 'reschedule_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'approved_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'approved_at', 'completed_at']
    
    actions = ['approve_appointments', 'mark_completed', 'mark_cancelled']
    
    def approve_appointments(self, request, queryset):
        from django.utils import timezone
        queryset.filter(status='pending').update(
            status='approved', 
            approved_at=timezone.now(),
            health_worker=request.user if request.user.is_health_worker else None
        )
    approve_appointments.short_description = "Approve selected appointments"
    
    def mark_completed(self, request, queryset):
        from django.utils import timezone
        queryset.filter(status='approved').update(
            status='completed',
            completed_at=timezone.now()
        )
    mark_completed.short_description = "Mark selected appointments as completed"
    
    def mark_cancelled(self, request, queryset):
        queryset.filter(status__in=['pending', 'approved']).update(status='cancelled')
    mark_cancelled.short_description = "Cancel selected appointments"


@admin.register(AppointmentSlot)
class AppointmentSlotAdmin(admin.ModelAdmin):
    list_display = ['health_worker', 'date', 'start_time', 'end_time', 'is_available']
    list_filter = ['is_available', 'date']
    search_fields = ['health_worker__email', 'health_worker__first_name', 'health_worker__last_name']
    date_hierarchy = 'date'


@admin.register(ConsultationRecord)
class ConsultationRecordAdmin(admin.ModelAdmin):
    list_display = ['resident', 'health_worker', 'consultation_type', 'consultation_date', 'follow_up_required']
    list_filter = ['consultation_type', 'follow_up_required', 'consultation_date']
    search_fields = [
        'resident__email', 'resident__first_name', 'resident__last_name',
        'health_worker__email', 'health_worker__first_name', 'health_worker__last_name',
        'diagnosis', 'chief_complaint'
    ]
    raw_id_fields = ['appointment', 'resident', 'health_worker']
    date_hierarchy = 'consultation_date'
