from django import forms
from django.contrib.auth import get_user_model
from django.forms import modelformset_factory

from .models import Department, ReminderSlot

User = get_user_model()


class EmployeeForm(forms.Form):
    last_name = forms.CharField(label="Familiya", max_length=150)
    first_name = forms.CharField(label="Ism", max_length=150)
    username = forms.CharField(label="Login", max_length=150)
    department = forms.ModelChoiceField(
        label="Bo'lim", queryset=Department.objects.all(), required=False, empty_label="— tanlanmagan —"
    )
    position = forms.CharField(label="Lavozim", max_length=120, required=False)
    password = forms.CharField(
        label="Parol", required=False, max_length=128,
        help_text="Bo'sh qoldirsangiz: yangi xodimga avtomatik parol beriladi, mavjud xodimniki o'zgarmaydi.",
    )
    is_staff = forms.BooleanField(
        label="Rahbar", required=False,
        help_text="Boshqaruv paneliga kiradi, barcha xodimlar hisobotini ko'radi.",
    )
    is_active = forms.BooleanField(label="Faol", required=False, initial=True)

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        for name in ("last_name", "first_name", "username", "position", "password"):
            self.fields[name].widget.attrs.update({"autocomplete": "off"})

    def clean_username(self):
        u = self.cleaned_data["username"].strip()
        if " " in u:
            raise forms.ValidationError("Loginda bo'sh joy bo'lmasligi kerak.")
        qs = User.objects.filter(username__iexact=u)
        if self.user:
            qs = qs.exclude(pk=self.user.pk)
        if qs.exists():
            raise forms.ValidationError("Bu login band.")
        return u

    def clean_password(self):
        p = self.cleaned_data["password"].strip()
        if p and len(p) < 4:
            raise forms.ValidationError("Parol kamida 4 belgi bo'lsin.")
        return p


class UploadForm(forms.Form):
    file = forms.FileField(label="Fayl (.csv yoki .xlsx)")

    def clean_file(self):
        f = self.cleaned_data["file"]
        if not f.name.lower().endswith((".csv", ".xlsx")):
            raise forms.ValidationError("Faqat .csv yoki .xlsx fayl yuklang.")
        if f.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Fayl 2 MB dan oshmasligi kerak.")
        return f


ReminderFormSet = modelformset_factory(
    ReminderSlot,
    fields=["time", "message", "active"],
    extra=0,
    widgets={
        "time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        "message": forms.TextInput(attrs={"maxlength": 250}),
    },
)
