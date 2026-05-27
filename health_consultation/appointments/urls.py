from django.urls import path
from . import views

app_name = 'appointments'

urlpatterns = [
    # Appointment CRUD
    path('', views.appointment_list_view, name='list'),
    path('create/', views.appointment_create_view, name='create'),
    path('available-workers/', views.available_workers_view, name='available_workers'),
    path('<int:pk>/', views.appointment_detail_view, name='detail'),
    
    # Appointment Actions
    path('<int:pk>/approve/', views.appointment_approve_view, name='approve'),
    path('<int:pk>/reschedule/', views.appointment_reschedule_view, name='reschedule'),
    path('<int:pk>/cancel/', views.appointment_cancel_view, name='cancel'),
    path('<int:pk>/complete/', views.appointment_complete_view, name='complete'),
    
    # Online Consultation
    path('<int:pk>/join/', views.join_consultation_view, name='join_consultation'),
    path('<int:pk>/start-call/', views.start_call_view, name='start_call'),
    path('<int:pk>/end-call/', views.end_call_view, name='end_call'),
    path('<int:pk>/call-status/', views.call_status_view, name='call_status'),
    
    # Consultation Records
    path('records/', views.consultation_records_view, name='consultation_records'),
    path('records/<int:pk>/', views.consultation_record_detail_view, name='record_detail'),
]
