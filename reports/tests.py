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

        now = timezone.make_aware(dt.datetime(2026, 11, 23, 16, 5))  # dushanba 16:05
        with mock.patch("reports.views.timezone.localtime", return_value=now), \
             mock.patch("reports.views.timezone.make_aware", side_effect=timezone.make_aware):
            data = self.client.get(reverse("reminder_check")).json()
            self.assertTrue(data["due"])
            self.assertEqual(data["time"], "16:00")
            self.client.post(reverse("reminder_ack"), {"slot_id": data["slot_id"]})
            self.assertFalse(self.client.get(reverse("reminder_check")).json()["due"])


class PanelTests(TestCase):
    def setUp(self):
        self.boss = User.objects.create_user("boss", password="x12345", is_staff=True, first_name="Boss")
        self.emp = User.objects.create_user("ali", password="x12345", first_name="Ali", last_name="Valiyev")

    def test_employee_blocked_from_panel(self):
        self.client.login(username="ali", password="x12345")
        for name in ("panel", "panel_employees", "panel_departments", "panel_reminders", "panel_import"):
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 302, name)
            self.assertEqual(r.url, reverse("my_entries"))

    def test_pages_render_for_manager(self):
        self.client.login(username="boss", password="x12345")
        for name in ("panel", "panel_employees", "panel_employee_new", "panel_departments", "panel_reminders", "panel_import", "panel_import_sample"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_create_employee_autopassword(self):
        self.client.login(username="boss", password="x12345")
        r = self.client.post(reverse("panel_employee_new"), {
            "last_name": "Karimov", "first_name": "Sardor", "username": "karimov", "is_active": "on"})
        self.assertEqual(r.status_code, 302)
        u = User.objects.get(username="karimov")
        self.assertFalse(u.is_staff)
        self.assertTrue(u.has_usable_password())

    def test_duplicate_username_rejected(self):
        self.client.login(username="boss", password="x12345")
        r = self.client.post(reverse("panel_employee_new"), {
            "last_name": "X", "first_name": "Y", "username": "ali"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Bu login band")

    def test_cannot_deactivate_self(self):
        self.client.login(username="boss", password="x12345")
        self.client.post(reverse("panel_employee_toggle", args=[self.boss.pk]))
        self.boss.refresh_from_db()
        self.assertTrue(self.boss.is_active)

    def test_import_csv_and_xlsx(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.login(username="boss", password="x12345")
        csv_bytes = "full_name;department;position\nAliyev Vali;IT;Dasturchi\nРахимов Сардор;IT;\n".encode("utf-8")
        r = self.client.post(reverse("panel_import"), {"file": SimpleUploadedFile("x.csv", csv_bytes)})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["created_n"], 2)
        self.assertTrue(User.objects.filter(username="raximov.sardor").exists())
        from io import BytesIO
        from openpyxl import Workbook
        wb = Workbook(); ws = wb.active
        ws.append(["FIO", "Bo'lim", "Lavozim", "Rahbar"]); ws.append(["Toshmatov Ali", "HR", "Boshliq", "ha"])
        buf = BytesIO(); wb.save(buf)
        r = self.client.post(reverse("panel_import"), {"file": SimpleUploadedFile("x.xlsx", buf.getvalue())})
        self.assertEqual(r.context["created_n"], 1)
        self.assertTrue(User.objects.get(username="toshmatov.ali").is_staff)

    def test_departments_and_reminders(self):
        self.client.login(username="boss", password="x12345")
        self.client.post(reverse("panel_departments"), {"action": "add", "name": "Buxgalteriya"})
        from .models import Department
        self.assertTrue(Department.objects.filter(name="Buxgalteriya").exists())
        slot = ReminderSlot.objects.first()
        data = {"form-TOTAL_FORMS": "3", "form-INITIAL_FORMS": "3", "form-MIN_NUM_FORMS": "0", "form-MAX_NUM_FORMS": "1000"}
        for i, s in enumerate(ReminderSlot.objects.order_by("time")):
            data.update({f"form-{i}-id": s.pk, f"form-{i}-time": "08:30" if i == 0 else s.time.strftime("%H:%M"),
                         f"form-{i}-message": "Yangi matn" if i == 0 else s.message, f"form-{i}-active": "on"})
        r = self.client.post(reverse("panel_reminders"), data)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(ReminderSlot.objects.order_by("time").first().message, "Yangi matn")

    def test_login_redirects_by_role(self):
        r = self.client.post(reverse("login"), {"username": "boss", "password": "x12345"})
        self.assertEqual(r.url, reverse("panel"))
        self.client.logout()
        r = self.client.post(reverse("login"), {"username": "ali", "password": "x12345"})
        self.assertEqual(r.url, reverse("my_entries"))


class WordExportTests(TestCase):
    def setUp(self):
        self.boss = User.objects.create_user("boss", password="x12345", is_staff=True)
        self.emp = User.objects.create_user("ali", password="x12345", first_name="Ali", last_name="Valiyev")
        WorkEntry.objects.create(user=self.emp, date=timezone.localdate(), description="Server tekshirildi", hours=3)

    def _doc(self, user, **params):
        from io import BytesIO
        from docx import Document
        self.client.login(username=user, password="x12345")
        r = self.client.get(reverse("export_word"), params)
        self.assertEqual(r.status_code, 200)
        doc = Document(BytesIO(r.content))
        text = "\n".join(p.text for p in doc.paragraphs)
        for t in doc.tables:
            for row in t.rows:
                text += "\n" + " | ".join(c.text for c in row.cells)
        return text

    def test_week_detailed(self):
        text = self._doc("boss", period="week")
        self.assertIn("HAFTALIK HISOBOT", text)
        self.assertIn("Ali Valiyev", text)
        self.assertIn("Server tekshirildi", text)

    def test_year_monthly_and_detail_flag(self):
        self.assertNotIn("Server tekshirildi", self._doc("boss", period="year"))
        self.assertIn("Server tekshirildi", self._doc("boss", period="year", detail="1"))

    def test_employee_sees_only_self(self):
        other = User.objects.create_user("vali", password="x12345", last_name="Boshqa")
        WorkEntry.objects.create(user=other, date=timezone.localdate(), description="Yashirin ish", hours=1)
        text = self._doc("ali", period="month")
        self.assertIn("Server tekshirildi", text)
        self.assertNotIn("Yashirin ish", text)


class OptionalHoursTests(TestCase):
    def setUp(self):
        self.emp = User.objects.create_user("ali", password="x12345", first_name="Ali", last_name="Valiyev")
        self.boss = User.objects.create_user("boss", password="x12345", is_staff=True)

    def test_entry_without_hours_saves(self):
        self.client.login(username="ali", password="x12345")
        r = self.client.post("/", {"description": "Soatsiz yozuv", "hours": "", "status": "done"})
        self.assertEqual(r.status_code, 302)
        e = WorkEntry.objects.get()
        self.assertIsNone(e.hours)

    def test_pages_and_exports_work_without_hours(self):
        from io import BytesIO
        from docx import Document
        WorkEntry.objects.create(user=self.emp, date=timezone.localdate(), description="Soatsiz ish", hours=None)
        self.client.login(username="ali", password="x12345")
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get(reverse("summary"), {"period": "month"}).status_code, 200)
        self.assertEqual(self.client.get(reverse("export_excel"), {"period": "month"}).status_code, 200)
        r = self.client.get(reverse("export_word"), {"period": "month"})
        doc = Document(BytesIO(r.content))
        heads = [c.text for t in doc.tables for c in t.rows[0].cells]
        self.assertNotIn("Soat", heads)
        self.assertIn("Soatsiz ish", "\n".join(c.text for t in doc.tables for row in t.rows for c in row.cells))
        self.client.logout()
        self.client.login(username="boss", password="x12345")
        self.assertEqual(self.client.get(reverse("panel")).status_code, 200)
        self.assertEqual(self.client.get(reverse("panel_employees")).status_code, 200)

    def test_mixed_hours_shows_column(self):
        from io import BytesIO
        from docx import Document
        WorkEntry.objects.create(user=self.emp, date=timezone.localdate(), description="A", hours=None)
        WorkEntry.objects.create(user=self.emp, date=timezone.localdate(), description="B", hours=2)
        self.client.login(username="ali", password="x12345")
        doc = Document(BytesIO(self.client.get(reverse("export_word"), {"period": "month"}).content))
        self.assertIn("Soat", [c.text for t in doc.tables for c in t.rows[0].cells])


class AgentApiTests(TestCase):
    def test_schedule_public_and_reported_flag(self):
        u = User.objects.create_user("ali", password="x12345")
        r = self.client.get(reverse("agent_schedule"), {"u": "ali"})
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertEqual([s["time"] for s in d["slots"]], ["11:00", "16:00", "19:00"])
        self.assertTrue(d["user_found"])
        self.assertFalse(d["reported_today"])
        WorkEntry.objects.create(user=u, date=timezone.localdate(), description="Ish", hours=None)
        self.assertTrue(self.client.get(reverse("agent_schedule"), {"u": "ali"}).json()["reported_today"])

    def test_unknown_user_and_inactive_slot(self):
        d = self.client.get(reverse("agent_schedule"), {"u": "yoq"}).json()
        self.assertFalse(d["user_found"])
        ReminderSlot.objects.filter(time=dt.time(11, 0)).update(active=False)
        d = self.client.get(reverse("agent_schedule"), {"u": "yoq"}).json()
        self.assertEqual(len(d["slots"]), 2)

    def test_browser_reminders_can_be_disabled(self):
        from unittest import mock
        User.objects.create_user("ali", password="x12345")
        self.client.login(username="ali", password="x12345")
        now = timezone.make_aware(dt.datetime(2026, 11, 23, 16, 5))
        with mock.patch("reports.views.timezone.localtime", return_value=now), self.settings(BROWSER_REMINDERS=False):
            self.assertFalse(self.client.get(reverse("reminder_check")).json()["due"])
