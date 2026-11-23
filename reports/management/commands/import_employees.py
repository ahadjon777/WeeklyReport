"""Xodimlarni CSV fayldan ommaviy qo'shish.

CSV ustunlari (birinchi qator sarlavha):
  full_name, department, position, is_manager, username, password
Faqat full_name majburiy. Login va parol bo'sh bo'lsa, avtomatik yaratiladi.
Natija: parollar.csv (xodimlarga tarqatish uchun).
"""
import csv
import random
import re

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from reports.models import Department

User = get_user_model()


def make_username(full_name, taken):
    base = re.sub(r"[^a-z0-9]+", ".", full_name.lower().replace("'", "").replace("‘", "").replace("’", "")).strip(".")
    if not base:
        base = "xodim"
    name, i = base, 1
    while name in taken or User.objects.filter(username=name).exists():
        i += 1
        name = f"{base}{i}"
    taken.add(name)
    return name


class Command(BaseCommand):
    help = "Xodimlarni CSV fayldan import qiladi va parollar.csv yaratadi"

    def add_arguments(self, parser):
        parser.add_argument("csv_path")
        parser.add_argument("--out", default="parollar.csv")

    def handle(self, *args, csv_path, out, **opts):
        try:
            f = open(csv_path, newline="", encoding="utf-8-sig")
        except OSError as e:
            raise CommandError(f"Faylni ochib bo'lmadi: {e}")
        taken, results = set(), []
        with f:
            for row in csv.DictReader(f):
                full = (row.get("full_name") or "").strip()
                if not full:
                    continue
                username = (row.get("username") or "").strip() or make_username(full, taken)
                password = (row.get("password") or "").strip() or str(random.randint(100000, 999999))
                parts = full.split()
                user, created = User.objects.get_or_create(username=username)
                user.first_name = " ".join(parts[1:])
                user.last_name = parts[0]
                user.is_staff = (row.get("is_manager") or "").strip().lower() in ("1", "ha", "yes", "true")
                if created or row.get("password"):
                    user.set_password(password)
                else:
                    password = "(o'zgartirilmagan)"
                user.save()
                dep_name = (row.get("department") or "").strip()
                profile = user.profile
                if dep_name:
                    profile.department, _ = Department.objects.get_or_create(name=dep_name)
                profile.position = (row.get("position") or "").strip()
                profile.save()
                results.append([full, username, password, dep_name])
        with open(out, "w", newline="", encoding="utf-8-sig") as o:
            w = csv.writer(o)
            w.writerow(["Xodim", "Login", "Parol", "Bo'lim"])
            w.writerows(results)
        self.stdout.write(self.style.SUCCESS(f"{len(results)} ta xodim qo'shildi. Parollar: {out}"))
