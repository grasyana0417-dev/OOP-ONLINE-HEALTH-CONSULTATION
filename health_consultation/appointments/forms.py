from django import forms
from django.utils import timezone
from datetime import time
from .models import Appointment, ConsultationRecord
from accounts.models import User

TIME_SLOT_CHOICES = [
    ('08:00', '08:00 AM'),
    ('09:00', '09:00 AM'),
    ('10:00', '10:00 AM'),
    ('11:00', '11:00 AM'),
    ('12:00', '12:00 PM'),
    ('13:00', '01:00 PM'),
    ('14:00', '02:00 PM'),
    ('15:00', '03:00 PM'),
    ('16:00', '04:00 PM'),
]


class AppointmentForm(forms.ModelForm):
    """Form for creating new appointments."""
    
    CONSULTATION_TYPE_CHOICES = [
        ('', 'Select Consultation Type'),
        ('prenatal', 'Prenatal Care'),
        ('child_health', 'Child Health'),
        ('general', 'General Health Concern'),
        ('family_planning', 'Family Planning'),
        ('follow_up', 'Follow-up Checkup'),
        ('immunization', 'Immunization'),
        ('nutrition', 'Nutrition Counseling'),
        ('dental', 'Dental Checkup'),
        ('mental_health', 'Mental Health'),
        ('other', 'Other'),
    ]
    
    CONSULTATION_METHOD_CHOICES = [
        ('video_call', 'Online Video Call'),
        ('voice_call', 'Online Voice Call'),
        ('chat', 'Chat Consultation'),
        ('in_person', 'In-Person Visit'),
    ]
    
    consultation_type = forms.ChoiceField(
        choices=CONSULTATION_TYPE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': 'required'
        })
    )
    
    consultation_method = forms.ChoiceField(
        choices=CONSULTATION_METHOD_CHOICES,
        initial='video_call',
        widget=forms.HiddenInput()
    )

    custom_consultation_type = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Type your consultation type',
            'maxlength': '100'
        })
    )
    
    scheduled_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': 'required',
            'min': timezone.now().strftime('%Y-%m-%d')
        })
    )
    
    scheduled_time = forms.TimeField(
        input_formats=['%H:%M'],
        widget=forms.Select(
            choices=TIME_SLOT_CHOICES,
            attrs={
                'class': 'form-control',
                'required': 'required'
            }
        )
    )
    
    reason_for_visit = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Please describe your symptoms or reason for consultation...',
            'required': 'required'
        })
    )
    
    symptoms = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'List any symptoms you are experiencing (optional)'
        })
    )
    
    class Meta:
        model = Appointment
        fields = ['health_worker', 'consultation_type', 'custom_consultation_type', 'consultation_method', 'scheduled_date',
                  'scheduled_time', 'reason_for_visit', 'symptoms']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Keep visual layout consistent: enforce shared control styling.
        for field_name in ['health_worker', 'consultation_type', 'consultation_method', 'scheduled_date', 'scheduled_time']:
            css = self.fields[field_name].widget.attrs.get('class', '')
            if 'form-control' not in css:
                self.fields[field_name].widget.attrs['class'] = (css + ' form-control').strip()

        self.fields['consultation_method'].initial = 'video_call'
        self.initial.setdefault('consultation_method', 'video_call')
        self.fields['health_worker'].label = 'Health Worker/Midwife'
        self.fields['health_worker'].queryset = User.objects.filter(
            role='health_worker',
            is_available=True,
            is_active=True
        ).order_by('first_name', 'last_name')
    
    def clean_scheduled_date(self):
        """Validate that the scheduled date is not in the past."""
        scheduled_date = self.cleaned_data.get('scheduled_date')
        if scheduled_date and scheduled_date < timezone.now().date():
            raise forms.ValidationError("Cannot schedule appointments in the past.")
        return scheduled_date
    
    def clean(self):
        """Validate the appointment time."""
        cleaned_data = super().clean()
        scheduled_date = cleaned_data.get('scheduled_date')
        scheduled_time = cleaned_data.get('scheduled_time')
        consultation_type = cleaned_data.get('consultation_type')
        custom_type = (cleaned_data.get('custom_consultation_type') or '').strip()

        if consultation_type == 'other' and not custom_type:
            self.add_error('custom_consultation_type', "Please type the consultation type for 'Other'.")
        if consultation_type != 'other':
            cleaned_data['custom_consultation_type'] = ''
        # Lock consultation method for this workflow.
        cleaned_data['consultation_method'] = 'video_call'
        
        if scheduled_date and scheduled_time:
            # Check if the appointment time is in the future
            appointment_datetime = timezone.make_aware(
                timezone.datetime.combine(scheduled_date, scheduled_time)
            )
            if appointment_datetime < timezone.now():
                raise forms.ValidationError("Cannot schedule appointments in the past.")
            
            # Check business hours (8 AM to 5 PM)
            if scheduled_time < time(8, 0) or scheduled_time > time(16, 0):
                raise forms.ValidationError("Appointments must start between 8:00 AM and 4:00 PM (1-hour slots).")

        return cleaned_data


class RescheduleForm(forms.Form):
    """Form for rescheduling appointments."""
    
    new_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': 'required',
            'min': timezone.now().strftime('%Y-%m-%d')
        })
    )
    
    new_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time',
            'required': 'required'
        })
    )
    
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for rescheduling (optional)'
        })
    )
    
    def clean_new_date(self):
        """Validate that the new date is not in the past."""
        new_date = self.cleaned_data.get('new_date')
        if new_date and new_date < timezone.now().date():
            raise forms.ValidationError("Cannot reschedule to a past date.")
        return new_date
    
    def clean_new_time(self):
        """Validate business hours."""
        new_time = self.cleaned_data.get('new_time')
        if new_time:
            if new_time.hour < 8 or new_time.hour >= 17:
                raise forms.ValidationError("Appointments can only be scheduled between 8:00 AM and 5:00 PM.")
        return new_time


class CancellationForm(forms.Form):
    """Form for cancelling appointments."""
    
    reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Reason for cancellation (optional)'
        })
    )


class ConsultationNotesForm(forms.ModelForm):
    """Form for health workers to add consultation notes."""
    
    consultation_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Detailed notes from the consultation'
        })
    )
    
    diagnosis = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Diagnosis or assessment'
        })
    )
    
    recommendations = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Recommendations, prescriptions, or follow-up instructions'
        })
    )
    
    class Meta:
        model = Appointment
        fields = ['consultation_notes', 'diagnosis', 'recommendations']


class ConsultationRecordForm(forms.ModelForm):
    """Form for creating detailed consultation records."""
    
    chief_complaint = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Main reason for consultation'
        })
    )
    
    symptoms_observed = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Symptoms observed during consultation'
        })
    )
    
    diagnosis = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Diagnosis or findings'
        })
    )
    
    treatment_provided = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Treatment provided during consultation'
        })
    )
    
    medications_prescribed = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Medications prescribed'
        })
    )
    
    recommendations = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'General recommendations and advice'
        })
    )
    
    follow_up_required = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    follow_up_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    follow_up_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Notes for follow-up visit'
        })
    )
    
    blood_pressure = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 120/80'
        })
    )
    
    pulse_rate = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=300,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'BPM'
        })
    )
    
    temperature = forms.DecimalField(
        required=False,
        min_value=30,
        max_value=45,
        decimal_places=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '°C'
        })
    )
    
    respiratory_rate = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'breaths/min'
        })
    )
    
    weight_kg = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=500,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'kg'
        })
    )
    
    class Meta:
        model = ConsultationRecord
        fields = [
            'chief_complaint', 'symptoms_observed', 'diagnosis', 'treatment_provided',
            'medications_prescribed', 'recommendations', 'follow_up_required',
            'follow_up_date', 'follow_up_notes', 'blood_pressure', 'pulse_rate',
            'temperature', 'respiratory_rate', 'weight_kg'
        ]


class AppointmentFilterForm(forms.Form):
    """Form for filtering appointments."""
    
    STATUS_CHOICES = [
        ('', 'All Status'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    TYPE_CHOICES = [
        ('', 'All Types'),
        ('prenatal', 'Prenatal Care'),
        ('child_health', 'Child Health'),
        ('general', 'General Health'),
        ('family_planning', 'Family Planning'),
        ('follow_up', 'Follow-up'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    consultation_type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    health_worker = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=True,
        empty_label='Select Health Worker/Midwife',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': 'required'
        })
    )
