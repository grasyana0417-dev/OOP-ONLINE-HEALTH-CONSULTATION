from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, ResidentProfile, HealthWorkerProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create appropriate profile when a user is created."""
    if created:
        if instance.role == 'resident':
            ResidentProfile.objects.get_or_create(user=instance)
        elif instance.role == 'health_worker':
            HealthWorkerProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved."""
    if hasattr(instance, 'resident_profile'):
        instance.resident_profile.save()
    if hasattr(instance, 'health_worker_profile'):
        instance.health_worker_profile.save()
