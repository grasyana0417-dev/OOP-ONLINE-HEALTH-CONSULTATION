from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Chat List
    path('', views.chat_list_view, name='list'),
    
    # Chat Conversation
    path('room/<int:room_id>/', views.chat_conversation_view, name='conversation'),
    path('room/<int:room_id>/messages/', views.get_messages_view, name='get_messages'),
    path('room/<int:room_id>/read/', views.mark_messages_read_view, name='mark_read'),
    
    # Start Chat
    path('start/<int:user_id>/', views.start_chat_view, name='start_chat'),
    
    # Consultation Chat
    path('consultation/<int:appointment_id>/', views.consultation_chat_view, name='consultation_chat'),
    
    # Send Messages
    path('send/', views.send_message_view, name='send_message'),
    path('send-file/', views.send_file_view, name='send_file'),
    
    # Chat History
    path('history/<int:user_id>/', views.chat_history_view, name='history'),
]
