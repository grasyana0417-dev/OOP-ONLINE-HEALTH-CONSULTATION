from django.urls import path
from . import views

app_name = 'consultations'

urlpatterns = [
    # Call Room
    path('call/<int:appointment_id>/', views.call_room_view, name='call_room'),
    
    # Call Actions
    path('<int:consultation_id>/join/', views.join_call_view, name='join_call'),
    path('<int:consultation_id>/leave/', views.leave_call_view, name='leave_call'),
    path('<int:consultation_id>/end/', views.end_call_view, name='end_call'),
    path('<int:consultation_id>/log/', views.log_event_view, name='log_event'),
    
    # Feedback
    path('<int:consultation_id>/feedback/', views.feedback_view, name='feedback'),
    
    # History
    path('history/', views.consultation_history_view, name='history'),
]
