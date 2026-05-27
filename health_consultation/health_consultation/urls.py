"""
URL configuration for health_consultation project.
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView

urlpatterns = [
    path('admin/', RedirectView.as_view(pattern_name='accounts:admin_login', permanent=False)),
    path('admin/<path:extra>/', RedirectView.as_view(pattern_name='accounts:admin_login', permanent=False)),
    path('', TemplateView.as_view(template_name='landing.html'), name='home'),
    path('terms/', TemplateView.as_view(template_name='terms.html'), name='terms'),
    path('privacy/', TemplateView.as_view(template_name='privacy.html'), name='privacy'),
    path('accounts/', include('accounts.urls')),
    path('appointments/', include('appointments.urls')),
    path('chat/', include('chat.urls')),
    path('consultations/', include('consultations.urls')),
    path('notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
