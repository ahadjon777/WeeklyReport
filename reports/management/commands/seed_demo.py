"""Sinov uchun namunaviy xodimlar va yozuvlar (faqat tekshirish uchun)."""
import datetime as dt
import random
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from reports.models import Department, WorkEntry

User = get_user_model()
TASKS = [
    "Mijozlar arizalarini ko'rib chiqish",
    "Kunlik hisobotni tayyorlash",
    "Server holatini tekshirish",
    "Hujjatlarni rasmiylashtirish",
    "Uchrashuvda ishtirok etish",
    "Texnik nosozlikni bartaraf etish",
]


class Command(BaseCommand):
    def handle(self, *args, **opts):
        dep, _ = Department.objects.get_or_create(name="IT bo'limi")
        today = timezone.localdate()
        for i in range(1, 6):
            u, _ = User.objects.get_or_create(
                username=f"demo{i}", defaults={"first_name": f"Xodim{i}", "last_name": "Demo"}
            )
            u.set_password("demo12345")
            u.save()
            u.profile.department = dep
            u.profile.position = "Mutaxassis"
            u.profile.save()
            for back in range(0, 60):
                d = today - dt.timedelta(days=back)
                if d.weekday() > 4 or random.random() < 0.15:
                    continue
                WorkEntry.objects.create(
                    user=u, date=d, description=random.choice(TASKS),
                    hours=Decimal(random.choice(["2", "3", "4", "1.5"])),
                    status=random.choice(["done", "done", "done", "progress", "blocked"]),
                )
        self.stdout.write("Demo ma'lumotlar yaratildi (login: demo1..demo5, parol: demo12345)")
