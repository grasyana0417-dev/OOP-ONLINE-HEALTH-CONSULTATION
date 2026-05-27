from datetime import timedelta, time

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import HealthWorkerProfile, ResidentProfile, User
from appointments.models import Appointment, ConsultationRecord
from chat.models import ChatMessage, ChatRoom
from notifications.models import Notification


class Command(BaseCommand):
    help = "Create demo users and sample health consultation data."

    def handle(self, *args, **options):
        admin = self._user(
            email="admin@guimbala.test",
            password="Admin12345!",
            first_name="Barangay",
            last_name="Admin",
            role="admin",
            is_staff=True,
            is_superuser=True,
        )

        worker = self._user(
            email="worker@guimbala.test",
            password="Worker12345!",
            first_name="Maria",
            last_name="Santos",
            role="health_worker",
            phone_number="0917 000 1000",
            address="Barangay Guimbala Health Center, Silay City",
            is_available=True,
        )
        HealthWorkerProfile.objects.update_or_create(
            user=worker,
            defaults={
                "employee_id": "BHW-001",
                "license_number": "MW-2026-001",
                "specialization": "general",
                "years_of_experience": 6,
                "bio": "Barangay Health Worker/Midwife supporting online consultations for Guimbala residents.",
                "schedule_start": time(8, 0),
                "schedule_end": time(17, 0),
                "days_available": "Mon,Tue,Wed,Thu,Fri",
                "is_on_duty": True,
            },
        )

        resident = self._user(
            email="resident@guimbala.test",
            password="Resident12345!",
            first_name="Juan",
            last_name="Dela Cruz",
            role="resident",
            phone_number="0917 000 2000",
            address="Purok 2, Barangay Guimbala, Silay City",
        )
        ResidentProfile.objects.update_or_create(
            user=resident,
            defaults={
                "age": 32,
                "gender": "male",
                "civil_status": "married",
                "medical_history": "No major medical history recorded.",
                "allergies": "None reported.",
            },
        )

        tomorrow = timezone.localdate() + timedelta(days=1)
        appointment, _ = Appointment.objects.update_or_create(
            resident=resident,
            health_worker=worker,
            scheduled_date=tomorrow,
            scheduled_time=time(9, 30),
            defaults={
                "consultation_type": "general",
                "consultation_method": "video_call",
                "status": "approved",
                "reason_for_visit": "Mild fever and headache for two days.",
                "symptoms": "Fever, headache, body weakness.",
                "approved_at": timezone.now(),
            },
        )

        completed_date = timezone.localdate() - timedelta(days=7)
        completed, _ = Appointment.objects.update_or_create(
            resident=resident,
            health_worker=worker,
            scheduled_date=completed_date,
            scheduled_time=time(10, 0),
            defaults={
                "consultation_type": "follow_up",
                "consultation_method": "chat",
                "status": "completed",
                "reason_for_visit": "Follow-up checkup after cough.",
                "consultation_notes": "Resident reported improvement after rest and hydration.",
                "diagnosis": "Resolving upper respiratory symptoms.",
                "recommendations": "Continue fluids, rest, and return if fever persists.",
                "completed_at": timezone.now() - timedelta(days=6),
            },
        )

        ConsultationRecord.objects.update_or_create(
            appointment=completed,
            defaults={
                "resident": resident,
                "health_worker": worker,
                "consultation_type": completed.consultation_type,
                "consultation_method": completed.consultation_method,
                "consultation_date": completed.scheduled_date,
                "chief_complaint": completed.reason_for_visit,
                "symptoms_observed": "Improving cough, no fever.",
                "diagnosis": completed.diagnosis,
                "treatment_provided": "Health counseling and monitoring advice.",
                "recommendations": completed.recommendations,
            },
        )

        room, _ = ChatRoom.objects.get_or_create(
            resident=resident,
            health_worker=worker,
            appointment=appointment,
            defaults={
                "room_type": "appointment",
                "name": "General Health Consultation",
                "last_message_at": timezone.now(),
            },
        )
        ChatMessage.objects.get_or_create(
            sender=worker,
            receiver=resident,
            appointment=appointment,
            content="Good day. Your appointment is approved. Please join the online call at the scheduled time.",
        )

        Notification.objects.get_or_create(
            recipient=resident,
            notification_type="appointment_approved",
            title="Appointment Approved",
            message="Your demo appointment has been approved for online consultation.",
            link=appointment.get_absolute_url(),
        )

        self.stdout.write(self.style.SUCCESS("Demo data created."))
        self.stdout.write("Admin: admin@guimbala.test / Admin12345!")
        self.stdout.write("Health Worker/Midwife: worker@guimbala.test / Worker12345!")
        self.stdout.write("Resident: resident@guimbala.test / Resident12345!")

    def _user(self, email, password, **defaults):
        user, created = User.objects.get_or_create(email=email, defaults=defaults)
        for key, value in defaults.items():
            setattr(user, key, value)
        if created or not user.has_usable_password():
            user.set_password(password)
        user.save()
        return user
