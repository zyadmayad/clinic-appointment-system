from django import forms

from consultations.models import Consultation

FIELD_CLASS = "w-full bg-surface text-on-surface border border-outline-variant rounded-lg px-md py-sm focus:border-secondary-container focus:ring-1 focus:ring-secondary-container transition-colors outline-none resize-y"


class ConsultationForm(forms.ModelForm):
    diagnosis = forms.CharField(
        required=True,
        error_messages={"required": "Diagnosis is required."},
        widget=forms.Textarea(attrs={"rows": 3, "class": FIELD_CLASS}),
    )

    class Meta:
        model = Consultation
        fields = ["diagnosis", "notes", "prescriptions", "tests"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 4, "class": FIELD_CLASS}),
            "prescriptions": forms.Textarea(attrs={"rows": 4, "class": FIELD_CLASS}),
            "tests": forms.Textarea(attrs={"rows": 3, "class": FIELD_CLASS}),
        }