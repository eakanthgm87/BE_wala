from django import forms
from .models import UpcomingCrop



class UpcomingCropForm(forms.ModelForm):
    class Meta:
        model = UpcomingCrop
        fields = ["description", "expected_ready_date"]
        widgets = {
            "description": forms.Textarea(attrs={
                "placeholder": "Enter crop details...",
                "rows": 4,
            }),
            "expected_ready_date": forms.DateInput(attrs={
                "type": "date"
            }),
        }