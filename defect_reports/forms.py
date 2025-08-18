from django import forms
from .models import DefectReport

class DefectReportForm(forms.ModelForm):
    """Form for operators to submit defect reports"""
    
    class Meta:
        model = DefectReport
        fields = ['title', 'batch', 'description', 'image', 'production_phase', 'severity']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief description of defect'}),
            'batch': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Provide details about the defect, when it was observed, etc.'}),
            'production_phase': forms.TextInput(attrs={'class': 'form-control'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

class DefectReviewForm(forms.ModelForm):
    """Form for QA staff to review defect reports"""
    
    class Meta:
        model = DefectReport
        fields = ['status', 'review_notes', 'corrective_action']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'review_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add notes from your review'}),
            'corrective_action': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe any corrective actions needed'}),
        }
