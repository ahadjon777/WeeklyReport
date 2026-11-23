import datetime as dt
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import ReminderAck, ReminderSlot, WorkEntry
from .periods import get_range

User = get_user_model()


class PeriodTests(TestCase):
    def test_ranges(self):
        ref = dt.date(2026, 11, 23)  # dushanba
        self.assertEqual(get_range("week", ref)[:2], (dt.date(2026, 11, 23), dt.date(2026, 11, 29)))
        self.assertEqual(get_range("month", ref)[:2], (dt.date(2026, 11, 1), dt.date(2026, 11, 30)))
        self.assertEqual(get_range("quarter", ref)[:2], (dt.date(2026, 10, 1), dt.date(2026, 12, 31)))
        self.assertEqual(get_range("half", ref)[:2], (dt.date(2026, 7, 1), dt.date(2026, 12, 31)))
        self.assertEqual(get_range("year", ref)[:2], (dt.date(2026, 1, 1), dt.date(2026, 12, 31)))


class FlowTests(TestCase):
    def setUp(self):
        self.emp = User.objects.create_user("ali", password="x12345", first_name="Ali", last_name="Valiyev")
        self.emp2 = User.objects.create_user("vali", password="x12345")
        self.boss = User.objects.create_user("boss", password="x12345", is_staff=True)

    def test_profile_autocreated(self):
        self.assertTrue(hasattr(self.emp, "profile"))

    def test_add_entry_and_summary_isolation(self):
        self.client.login(username="ali", password="x12345")
        r = self.client.post("/", {"description": "Server tekshirish", "hours": "3.5", "status": "done"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(WorkEntry.objects.filter(user=self.emp).count(), 1)
        WorkEntry.objects.create(user=self.emp2, date=timezone.localdate(), description="Boshqa ish", hours=2)
        r = self.client.get(reverse("summary"), {"period": "year"})
        self.assertContains(r, "Valiyev")
        self.assertNotContains(r, "vali</b>")  # boshqa xodim ko'rinmaydi
        self.assertEqual(r.context["totals"]["hours"], Decimal("3.5"))

    def test_manager_sees_all_and_excel(self):
        for u in (self.emp, self.emp2):
            WorkEntry.objects.create(user=u, date=timezone.localdate(), description="Ish bajarildi", hours=2)
        self.client.login(username="boss", password="x12345")
        r = self.client.get(reverse("summary"), {"period": "month"})
        self.assertEqual(r.context["totals"]["employees"], 2)
        self.assertEqual(r.context["totals"]["hours"], Decimal("4"))
        x = self.client.get(reverse("export_excel"), {"period": "month"})
        self.assertEqual(x.status_code, 200)
        self.assertTrue(x.content.startswith(b"PK"))

    def test_backfill_limit(self):
        self.client.login(username="ali", password="x12345")
        old = timezone.localdate() - dt.timedelta(days=10)
        self.client.post(f"/?date={old.isoformat()}", {"description": "Eski ish", "hours": "1", "status": "done"})
        self.assertEqual(WorkEntry.objects.count(), 0)

    def test_cannot_edit_others_entry(self):
        e = WorkEntry.objects.create(user=self.emp2, date=timezone.localdate(), description="Boshqaniki", hours=1)
        self.client.login(username="ali", password="x12345")
        self.client.post(reverse("entry_delete", args=[e.pk]))
        self.assertTrue(WorkEntry.objects.filter(pk=e.pk).exists())


class ReminderTests(TestCase):
    def setUp(self):
        self.u = User.objects.create_user("ali", password="x12345")
        self.client.login(username="ali", password="x12345")

    def test_three_default_slots(self):
        self.assertEqual(ReminderSlot.objects.filter(active=True).count(), 3)

    def test_due_then_ack(self):
        from unittest import mock

        now = timezone.make_aware(dt.datetime(2026, 11, 23, 13, 5))  # dushanba 13:05
        with mock.patch("reports.views.timezone.localtime", return_value=now), \
             mock.patch("reports.views.timezone.make_aware", side_effect=timezone.make_aware):
            data = self.client.get(reverse("reminder_check")).json()
            self.assertTrue(data["due"])
            self.assertEqual(data["time"], "13:00")
            self.client.post(reverse("reminder_ack"), {"slot_id": data["slot_id"]})
            self.assertFalse(self.client.get(reverse("reminder_check")).json()["due"])
