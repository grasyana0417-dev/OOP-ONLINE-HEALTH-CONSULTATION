from django import forms
from .models import NotificationPreference


class NotificationPreferenceForm(forms.ModelForm):
    """Form for notification preferences."""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'email_appointment_reminders',
            'email_appointment_updates',
            'email_new_messages',
            'email_system_notifications',
            'in_app_appointment_reminders',
            'in_app_appointment_updates',
            'in_app_new_messages',
            'in_app_system_notifications',
        ]
        widgets = {
            'email_appointment_reminders': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_appointment_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_new_messages': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'email_system_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_appointment_reminders': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_appointment_updates': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_new_messages': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'in_app_system_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
