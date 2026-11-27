import datetime as dt
from decimal import Decimal
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.db.models import Count, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .exports import build_workbook
from .exports_word import build_docx
from .forms import WorkEntryForm
from .models import Department, ReminderAck, ReminderSlot, WorkEntry
from .periods import PERIOD_KEYS, PERIODS, get_range, period_title
from .services import build_summary, display_name, employees_for


class StaffAwareLoginView(LoginView):
    """Rahbar kirganda boshqaruv paneliga, xodim kirganda kunlik hisobotga."""

    redirect_authenticated_user = True

    def get_default_redirect_url(self):
        return reverse("panel") if self.request.user.is_staff else reverse("my_entries")


def _parse_date(value, default):
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError):
        return default


def _date_allowed(user, d):
    """Xodim faqat bugun va oxirgi BACKFILL_DAYS kun ichida yozuv kirita/tahrirlay oladi."""
    today = timezone.localdate()
    if d > today:
        return False
    if user.is_staff:
        return True
    return d >= today - dt.timedelta(days=settings.BACKFILL_DAYS)


@login_required
def my_entries(request):
    today = timezone.localdate()
    day = min(_parse_date(request.GET.get("date"), today), today)
    can_add = _date_allowed(request.user, day)

    if request.method == "POST":
        if not can_add:
            messages.error(request, "Bu sana uchun yozuv kiritish mumkin emas.")
            return redirect(f"{request.path}?date={day.isoformat()}")
        form = WorkEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.user = request.user
            entry.date = day
            entry.save()
            messages.success(request, "Yozuv saqlandi.")
            return redirect(f"{request.path}?date={day.isoformat()}")
    else:
        form = WorkEntryForm()

    entries = WorkEntry.objects.filter(user=request.user, date=day).order_by("created_at")
    day_hours = sum(((e.hours or Decimal("0")) for e in entries), Decimal("0"))

    week_start, week_end, week_label = get_range("week", day)
    week_rows = (
        WorkEntry.objects.filter(user=request.user, date__range=(week_start, week_end))
        .values("date")
        .annotate(n=Count("id"), h=Sum("hours"))
        .order_by("date")
    )
    week_map = {r["date"]: r for r in week_rows}
    week_days = []
    for i in range(7):
        d = week_start + dt.timedelta(days=i)
        r = week_map.get(d)
        week_days.append(
            {
                "date": d,
                "n": r["n"] if r else 0,
                "h": (r["h"] or Decimal("0")) if r else Decimal("0"),
                "future": d > today,
                "current": d == day,
            }
        )

    return render(
        request,
        "reports/my_entries.html",
        {
            "day": day,
            "is_today": day == today,
            "prev_day": day - dt.timedelta(days=1),
            "next_day": day + dt.timedelta(days=1) if day < today else None,
            "entries": entries,
            "day_hours": day_hours,
            "form": form,
            "can_add": can_add,
            "can_edit": can_add,
            "week_label": week_label,
            "week_days": week_days,
            "week_total": sum((d["h"] for d in week_days), Decimal("0")),
            "week_count": sum(d["n"] for d in week_days),
        },
    )


@login_required
def entry_edit(request, pk):
    entry = get_object_or_404(WorkEntry, pk=pk)
    if entry.user_id != request.user.id and not request.user.is_staff:
        return redirect("my_entries")
    if not _date_allowed(request.user, entry.date):
        messages.error(request, "Bu sanadagi yozuvni tahrirlash muddati o'tgan.")
        return redirect(f"/?date={entry.date.isoformat()}")
    form = WorkEntryForm(request.POST or None, instance=entry)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Yozuv yangilandi.")
        return redirect(f"/?date={entry.date.isoformat()}")
    return render(request, "reports/entry_form.html", {"form": form, "entry": entry})


@login_required
@require_POST
def entry_delete(request, pk):
    entry = get_object_or_404(WorkEntry, pk=pk)
    if entry.user_id != request.user.id and not request.user.is_staff:
        return redirect("my_entries")
    if not _date_allowed(request.user, entry.date):
        messages.error(request, "Bu sanadagi yozuvni o'chirish muddati o'tgan.")
    else:
        entry.delete()
        messages.success(request, "Yozuv o'chirildi.")
    return redirect(f"/?date={entry.date.isoformat()}")


def _summary_params(request):
    today = timezone.localdate()
    period = request.GET.get("period", "week")
    if period not in PERIOD_KEYS:
        period = "week"
    ref = _parse_date(request.GET.get("date"), today)
    start, end, label = get_range(period, ref)
    department = request.GET.get("department") or ""
    user_id = request.GET.get("user") or ""
    return period, ref, start, end, label, department, user_id


@login_required
def summary(request):
    today = timezone.localdate()
    period, ref, start, end, label, department, user_id = _summary_params(request)
    users_qs = employees_for(
        request.user,
        department_id=int(department) if department.isdigit() else None,
        user_id=int(user_id) if user_id.isdigit() else None,
    )
    rows, totals = build_summary(users_qs, start, end)

    def nav_url(target_date):
        q = {"period": period, "date": target_date.isoformat()}
        if department:
            q["department"] = department
        if user_id:
            q["user"] = user_id
        return "?" + urlencode(q)

    export_q = {"period": period, "date": ref.isoformat()}
    if department:
        export_q["department"] = department
    if user_id:
        export_q["user"] = user_id

    all_users = []
    if request.user.is_staff:
        all_users = [
            (u.pk, display_name(u))
            for u in employees_for(request.user).order_by("last_name", "first_name", "username")
        ]

    return render(
        request,
        "reports/summary.html",
        {
            "periods": PERIODS,
            "period": period,
            "period_name": period_title(period),
            "label": label,
            "start": start,
            "end": end,
            "ref": ref,
            "prev_url": nav_url(start - dt.timedelta(days=1)),
            "next_url": nav_url(end + dt.timedelta(days=1)) if end < today else None,
            "rows": rows,
            "totals": totals,
            "departments": Department.objects.all() if request.user.is_staff else [],
            "all_users": all_users,
            "sel_department": department,
            "sel_user": user_id,
            "export_qs": urlencode(export_q),
        },
    )


@login_required
def export_excel(request):
    period, ref, start, end, label, department, user_id = _summary_params(request)
    users_qs = employees_for(
        request.user,
        department_id=int(department) if department.isdigit() else None,
        user_id=int(user_id) if user_id.isdigit() else None,
    )
    rows, totals = build_summary(users_qs, start, end)
    content = build_workbook(rows, totals, label, period_title(period))
    resp = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = (
        f'attachment; filename="hisobot_{period}_{start.isoformat()}.xlsx"'
    )
    return resp


@login_required
def export_word(request):
    period, ref, start, end, label, department, user_id = _summary_params(request)
    users_qs = employees_for(
        request.user,
        department_id=int(department) if department.isdigit() else None,
        user_id=int(user_id) if user_id.isdigit() else None,
    )
    rows, totals = build_summary(users_qs, start, end)
    detail = request.GET.get("detail")
    detailed = (detail == "1") if detail in ("0", "1") else period in ("week", "month")
    dep_name = ""
    if department.isdigit():
        dep_name = Department.objects.filter(pk=int(department)).values_list("name", flat=True).first() or ""
    content = build_docx(rows, totals, period, period_title(period), label, start, end, dep_name, detailed)
    resp = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    resp["Content-Disposition"] = f'attachment; filename="hisobot_{period}_{start.isoformat()}.docx"'
    return resp


# ---- Eslatmalar (kuniga 3 marta) -------------------------------------------------

REMINDER_WINDOW = dt.timedelta(hours=3)


@login_required
def reminder_check(request):
    """Brauzer har 30 soniyada so'raydi: hozir ko'rsatish kerak bo'lgan eslatma bormi?"""
    user = request.user
    now = timezone.localtime()
    today = now.date()
    if user.is_superuser or today.weekday() not in settings.WORK_DAYS:
        return JsonResponse({"due": False})

    acked = set(
        ReminderAck.objects.filter(user=user, date=today).values_list("slot_id", flat=True)
    )
    passed = [
        s
        for s in ReminderSlot.objects.filter(active=True)
        if s.time <= now.time() and s.id not in acked
    ]
    if not passed:
        return JsonResponse({"due": False})

    latest = passed[-1]
    # Eskirgan (kuzatilmay qolgan) eslatmalarni jimgina yopamiz
    for s in passed[:-1]:
        ReminderAck.objects.get_or_create(user=user, slot=s, date=today)
    slot_dt = timezone.make_aware(dt.datetime.combine(today, latest.time))
    if now - slot_dt > REMINDER_WINDOW:
        ReminderAck.objects.get_or_create(user=user, slot=latest, date=today)
        return JsonResponse({"due": False})

    todays = WorkEntry.objects.filter(user=user, date=today)
    n = todays.count()
    hours = todays.aggregate(h=Sum("hours"))["h"] or 0
    return JsonResponse(
        {
            "due": True,
            "slot_id": latest.id,
            "time": latest.time.strftime("%H:%M"),
            "message": latest.message,
            "entries_today": n,
            "hours_today": str(hours),
        }
    )


@login_required
@require_POST
def reminder_ack(request):
    slot = get_object_or_404(ReminderSlot, pk=request.POST.get("slot_id"))
    ReminderAck.objects.get_or_create(
        user=request.user, slot=slot, date=timezone.localdate()
    )
    return JsonResponse({"ok": True})
