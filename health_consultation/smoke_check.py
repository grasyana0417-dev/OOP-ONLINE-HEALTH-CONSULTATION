import os
from datetime import timedelta
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "health_consultation.settings")
import django
django.setup()

from django.test import Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from appointments.models import Appointment
from chat.models import ChatRoom

results = []

def check(name, ok, detail=""):
    results.append((name, ok, detail))

c = Client()

for label, urlname in [("home","home"),("login","accounts:login"),("register","accounts:register")]:
    r = c.get(reverse(urlname))
    check(f"public:{label}", r.status_code == 200, f"status={r.status_code}")

resident = User.objects.get(email="resident@guimbala.test")
worker = User.objects.get(email="worker@guimbala.test")
admin = User.objects.get(email="admin@guimbala.test")

pending = Appointment.objects.create(
    resident=resident,
    consultation_type="general",
    consultation_method="video_call",
    scheduled_date=timezone.localdate() + timedelta(days=2),
    scheduled_time="09:00",
    reason_for_visit="Smoke test appointment"
)

approved = Appointment.objects.filter(resident=resident, status="approved").order_by("-id").first()
room = ChatRoom.objects.filter(resident=resident, health_worker=worker).order_by("-id").first()

c.force_login(resident)
for label, url in [
    ("resident_dashboard", reverse("accounts:resident_dashboard")),
    ("appointments_list", reverse("appointments:list")),
    ("appointments_create", reverse("appointments:create")),
    ("notifications", reverse("notifications:list")),
    ("chat_list", reverse("chat:list")),
    ("consult_history", reverse("consultations:history")),
]:
    r = c.get(url)
    check(f"resident:{label}", r.status_code == 200, f"status={r.status_code}")

r = c.get(reverse("appointments:detail", kwargs={"pk": pending.pk}))
check("resident:appointment_detail", r.status_code == 200, f"status={r.status_code}")

if room:
    r = c.get(reverse("chat:conversation", kwargs={"room_id": room.pk}))
    check("resident:chat_conversation", r.status_code == 200, f"status={r.status_code}")
    r = c.post(reverse("chat:send_message"), {"room_id": room.pk, "content": "smoke test msg"})
    check("resident:chat_send_message", r.status_code == 200, f"status={r.status_code}")

c.logout()

c.force_login(worker)
for label, url in [
    ("worker_dashboard", reverse("accounts:worker_dashboard")),
    ("appointments_list", reverse("appointments:list")),
    ("notifications", reverse("notifications:list")),
    ("chat_list", reverse("chat:list")),
    ("consult_history", reverse("consultations:history")),
]:
    r = c.get(url)
    check(f"worker:{label}", r.status_code == 200, f"status={r.status_code}")

r = c.get(reverse("appointments:approve", kwargs={"pk": pending.pk}))
check("worker:approve_page", r.status_code == 200, f"status={r.status_code}")
r = c.post(reverse("appointments:approve", kwargs={"pk": pending.pk}))
check("worker:approve_post", r.status_code in (200, 302), f"status={r.status_code}")
pending.refresh_from_db()
check("worker:approve_effect", pending.status == "approved", f"status={pending.status}")

r = c.post(reverse("accounts:toggle_availability"))
check("worker:toggle_availability", r.status_code in (200,302), f"status={r.status_code}")

if approved is None:
    approved = pending

r = c.post(reverse("appointments:start_call", kwargs={"pk": approved.pk}))
check("worker:start_call", r.status_code == 200, f"status={r.status_code}")
r = c.post(reverse("appointments:end_call", kwargs={"pk": approved.pk}))
check("worker:end_call", r.status_code == 200, f"status={r.status_code}")

c.logout()

c.force_login(admin)
for label, url in [
    ("admin_dashboard", reverse("accounts:admin_dashboard")),
    ("appointments_list", reverse("appointments:list")),
    ("user_list", reverse("accounts:user_list")),
    ("notifications", reverse("notifications:list")),
]:
    r = c.get(url)
    check(f"admin:{label}", r.status_code == 200, f"status={r.status_code}")

failed = [x for x in results if not x[1]]
for name, ok, detail in results:
    print(("PASS" if ok else "FAIL"), name, detail)
print("TOTAL", len(results), "FAILED", len(failed))
if failed:
    raise SystemExit(1)
