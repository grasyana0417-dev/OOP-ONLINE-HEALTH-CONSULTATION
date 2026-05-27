from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Appointment, ConsultationRecord


@receiver(pre_save, sender=Appointment)
def track_appointment_changes(sender, instance, **kwargs):
    """Track changes to appointment status before saving."""
    if instance.pk:
        try:
            old_instance = Appointment.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Appointment.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Appointment)
def handle_appointment_status_change(sender, instance, created, **kwargs):
    """Handle actions after appointment status changes."""
    if created:
        # New appointment created
        from notifications.utils import create_notification
        
        # Notify admin/health workers about new appointment
        from accounts.models import User
        health_workers = User.objects.filter(role='health_worker', is_active=True)
        
        for worker in health_workers:
            create_notification(
                recipient=worker,
                notification_type='appointment_request',
                title='New Appointment Request',
                message=f'New appointment request from {instance.resident.get_full_name()}.',
                link=instance.get_absolute_url()
            )
