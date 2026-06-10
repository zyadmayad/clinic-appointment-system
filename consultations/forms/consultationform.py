from django import forms

from consultations.models import Consultation

FIELD_CLASS = "w-full px-3 py-2 border border-[#dde5eb] rounded-[10px] text-[#1b2f44] focus:outline-none focus:border-[#31b2a3]"


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