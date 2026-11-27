from decimal import Decimal

from django import forms

from .models import WorkEntry


class WorkEntryForm(forms.ModelForm):
    class Meta:
        model = WorkEntry
        fields = ["description", "hours", "status"]
        widgets = {
            "status": forms.RadioSelect,
            "description": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Masalan: mijozlar arizalari ko'rib chiqildi"}
            ),
            "hours": forms.NumberInput(attrs={"step": "0.5", "min": "0.5", "max": "16", "placeholder": "masalan, 2"}),
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
