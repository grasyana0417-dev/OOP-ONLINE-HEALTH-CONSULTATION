from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list_view, name='list'),
    path('<int:pk>/', views.notification_detail_view, name='detail'),
    path('<int:pk>/mark-read/', views.mark_notification_read_view, name='mark_read'),
    path('<int:pk>/delete/', views.delete_notification_view, name='delete'),
    path('mark-all-read/', views.mark_all_read_view, name='mark_all_read'),
    path('preferences/', views.preferences_view, name='preferences'),
    path('unread-count/', views.get_unread_count_view, name='unread_count'),
]
