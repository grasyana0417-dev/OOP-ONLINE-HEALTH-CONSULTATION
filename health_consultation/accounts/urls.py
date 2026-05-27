from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('login/resident/', views.resident_login_view, name='resident_login'),
    path('login/health-worker/', views.worker_login_view, name='worker_login'),
    path('login/admin/', views.admin_login_view, name='admin_login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboards
    path('dashboard/', views.dashboard_redirect_view, name='dashboard_redirect'),
    path('resident/dashboard/', views.resident_dashboard_view, name='resident_dashboard'),
    path('health-worker/dashboard/', views.worker_dashboard_view, name='worker_dashboard'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    
    # Health Worker
    path('toggle-availability/', views.toggle_availability_view, name='toggle_availability'),
    
    # Admin
    path('admin/users/create/', views.admin_user_create_view, name='user_create'),
    path('admin/users/', views.user_list_view, name='user_list'),
    path('admin/users/<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('admin/users/<int:user_id>/activate/', views.user_activate_view, name='user_activate'),
]
