from decimal import Decimal

from django import forms

from .models import WorkEntry


class WorkEntryForm(forms.ModelForm):
    class Meta:
        model = WorkEntry
        fields = ["description", "hours", "status"]
        widgets = {
            "description": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Nima ish qildingiz?"}
            ),
            "hours": forms.NumberInput(attrs={"step": "0.5", "min": "0.5", "max": "16", "placeholder": "ixtiyoriy"}),
        }

    def clean_hours(self):
        h = self.cleaned_data["hours"]
        if h is None:
            return None
        if h <= Decimal("0") or h > Decimal("16"):
            raise forms.ValidationError("Soat 0 dan katta va 16 dan oshmasligi kerak.")
        return h

    def clean_description(self):
        d = self.cleaned_data["description"].strip()
        if len(d) < 3:
            raise forms.ValidationError("Bajarilgan ishni yozing.")
        return d
