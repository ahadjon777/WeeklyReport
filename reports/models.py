from django.conf import settings
from django.db import models


class Department(models.Model):
    name = models.CharField("Bo'lim nomi", max_length=120, unique=True)

    class Meta:
        verbose_name = "Bo'lim"
        verbose_name_plural = "Bo'limlar"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    department = models.ForeignKey(
        Department,
        verbose_name="Bo'lim",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    position = models.CharField("Lavozim", max_length=120, blank=True)

    class Meta:
        verbose_name = "Xodim profili"
        verbose_name_plural = "Xodim profillari"

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class WorkEntry(models.Model):
    STATUS_DONE = "done"
    STATUS_PROGRESS = "progress"
    STATUS_BLOCKED = "blocked"
    STATUS_CHOICES = [
        (STATUS_DONE, "Bajarildi"),
        (STATUS_PROGRESS, "Jarayonda"),
        (STATUS_BLOCKED, "To'siq bor"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Xodim",
        on_delete=models.CASCADE,
        related_name="entries",
    )
    date = models.DateField("Sana", db_index=True)
    description = models.TextField("Bajarilgan ish")
    hours = models.DecimalField(
        "Sarflangan soat (ixtiyoriy)", max_digits=4, decimal_places=1, null=True, blank=True
    )
    status = models.CharField(
        "Holati", max_length=10, choices=STATUS_CHOICES, default=STATUS_DONE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ish yozuvi"
        verbose_name_plural = "Ish yozuvlari"
        ordering = ["-date", "-created_at"]
        indexes = [models.Index(fields=["user", "date"])]

    def __str__(self):
        return f"{self.user} · {self.date} · {self.description[:40]}"


class ReminderSlot(models.Model):
    time = models.TimeField("Eslatma vaqti")
    message = models.CharField("Xabar matni", max_length=250)
    active = models.BooleanField("Faol", default=True)

    class Meta:
        verbose_name = "Eslatma vaqti"
        verbose_name_plural = "Eslatma vaqtlari (kuniga 3 marta)"
        ordering = ["time"]

    def __str__(self):
        return self.time.strftime("%H:%M")


class ReminderAck(models.Model):
    """Xodim ma'lum kunda ma'lum eslatmani ko'rib, yopganini bildiradi."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    slot = models.ForeignKey(ReminderSlot, on_delete=models.CASCADE)
    date = models.DateField()

    class Meta:
        unique_together = [("user", "slot", "date")]
