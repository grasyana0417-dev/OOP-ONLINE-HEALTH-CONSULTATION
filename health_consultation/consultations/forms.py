from django import forms
from .models import ConsultationFeedback


class ConsultationFeedbackForm(forms.ModelForm):
    """Form for submitting consultation feedback."""
    
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    overall_satisfaction = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Overall Satisfaction'
    )
    
    doctor_competence = forms.ChoiceField(
        choices=RATING_CHOICES,
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Health Worker's Competence"
    )
    
    communication_clarity = forms.ChoiceField(
        choices=RATING_CHOICES,
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Clarity of Communication'
    )
    
    technical_quality = forms.ChoiceField(
        choices=RATING_CHOICES,
        required=False,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Technical Quality of the Call'
    )
    
    would_recommend = forms.NullBooleanField(
        widget=forms.Select(choices=[
            ('', 'Select an option'),
            (True, 'Yes'),
            (False, 'No'),
        ], attrs={'class': 'form-control'}),
        label='Would you recommend this service to others?'
    )
    
    positive_feedback = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'What went well during your consultation?'
        }),
        label='What went well?'
    )
    
    improvement_suggestions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'What could be improved?'
        }),
        label='Suggestions for Improvement'
    )
    
    class Meta:
        model = ConsultationFeedback
        fields = [
            'overall_satisfaction', 'doctor_competence', 'communication_clarity',
            'technical_quality', 'would_recommend', 'positive_feedback',
            'improvement_suggestions'
        ]
