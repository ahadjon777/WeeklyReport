"""Boshqaruv paneli (faqat rahbarlar uchun)."""
import datetime as dt
from collections import defaultdict
from decimal import Decimal
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .importer import ImportError_, import_rows, new_password, read_rows
from .models import Department, ReminderSlot, WorkEntry
from .periods import WEEKDAYS_UZ, get_range
from .services import employees_for
from .staff_forms import EmployeeForm, ReminderFormSet, UploadForm

User = get_user_model()


def staff_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            return redirect("my_entries")
        return view(request, *args, **kwargs)

    return wrapper


def _pct(part, whole):
    return round(part * 100 / whole) if whole else 0


# ---------------------------------------------------------------- Bosh sahifa

@staff_required
def dashboard(request):
    today = timezone.localdate()
    is_workday = today.weekday() in settings.WORK_DAYS
    emps = list(employees_for(request.user).select_related("profile__department"))
    ids = [u.id for u in emps]

    todays = WorkEntry.objects.filter(user_id__in=ids, date=today)
    reported_ids = set(todays.values_list("user_id", flat=True))
    today_entries = todays.count()
    pending = [u for u in emps if u.id not in reported_ids] if is_workday else []
    reported_n = len(reported_ids)
    total_n = len(emps)

    # 14 kunlik faollik
    start14 = today - dt.timedelta(days=13)
    rows = (
        WorkEntry.objects.filter(user_id__in=ids, date__gte=start14)
        .values("date")
        .annotate(n=Count("id"), people=Count("user", distinct=True))
    )
    by_day = {r["date"]: r for r in rows}
    max_n = max([r["n"] for r in by_day.values()] or [1]) or 1
    chart = []
    for i in range(14):
        d = start14 + dt.timedelta(days=i)
        r = by_day.get(d)
        n = r["n"] if r else 0
        chart.append(
            {
                "date": d,
                "label": f"{d.day:02d}",
                "wd": WEEKDAYS_UZ[d.weekday()][:3],
                "count": n,
                "people": r["people"] if r else 0,
                "height": max(4, round(n * 100 / max_n)) if n else 0,
                "weekend": d.weekday() not in settings.WORK_DAYS,
                "today": d == today,
            }
        )

    # Hafta soati va oldingi hafta bilan taqqoslash
    ws, we, _ = get_range("week", today)
    pws = ws - dt.timedelta(days=7)
    week_n = WorkEntry.objects.filter(user_id__in=ids, date__range=(ws, we)).count()
    prev_n = WorkEntry.objects.filter(
        user_id__in=ids, date__range=(pws, ws - dt.timedelta(days=1))
    ).count()
    delta = None
    if prev_n:
        delta = round((week_n - prev_n) * 100 / prev_n)

    # Bo'limlar kesimi
    deps = defaultdict(lambda: {"total": 0, "done": 0})
    for u in emps:
        p = getattr(u, "profile", None)
        name = p.department.name if p and p.department else "Bo'limsiz"
        deps[name]["total"] += 1
        if u.id in reported_ids:
            deps[name]["done"] += 1
    dep_rows = [
        {"name": n, "total": v["total"], "done": v["done"], "pct": _pct(v["done"], v["total"])}
        for n, v in sorted(deps.items())
    ]

    blocked = (
        WorkEntry.objects.filter(
            user_id__in=ids, status=WorkEntry.STATUS_BLOCKED, date__gte=today - dt.timedelta(days=7)
        )
        .select_related("user")
        .order_by("-date")[:6]
    )
    recent = WorkEntry.objects.filter(user_id__in=ids).select_related("user").order_by("-created_at")[:8]

    return render(
        request,
        "panel/dashboard.html",
        {
            "today": today,
            "is_workday": is_workday,
            "total_n": total_n,
            "reported_n": reported_n,
            "pending": pending,
            "pending_n": len(pending),
            "reported_pct": _pct(reported_n, total_n),
            "today_entries": today_entries,
            "week_n": week_n,
            "week_delta": delta,
            "chart": chart,
            "dep_rows": dep_rows,
            "blocked": blocked,
            "recent": recent,
        },
    )


# ---------------------------------------------------------------- Xodimlar

@staff_required
def employees(request):
    today = timezone.localdate()
    q = (request.GET.get("q") or "").strip()
    dep = request.GET.get("department") or ""
    status = request.GET.get("status") or "active"

    qs = User.objects.select_related("profile__department").annotate(
        last_report=Max("entries__date"),
        month_count=Count("entries", filter=Q(entries__date__gte=today.replace(day=1))),
    )
    if status == "active":
        qs = qs.filter(is_active=True)
    elif status == "inactive":
        qs = qs.filter(is_active=False)
    if q:
        qs = qs.filter(
            Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        )
    if dep.isdigit():
        qs = qs.filter(profile__department_id=int(dep))
    elif dep == "none":
        qs = qs.filter(profile__department__isnull=True)
    qs = qs.order_by("last_name", "first_name", "username")

    return render(
        request,
        "panel/employees.html",
        {
            "users": qs,
            "count": qs.count(),
            "q": q,
            "sel_dep": dep,
            "status": status,
            "departments": Department.objects.all(),
            "today": today,
        },
    )


@staff_required
def employee_edit(request, pk=None):
    target = get_object_or_404(User, pk=pk) if pk else None
    initial = {}
    if target:
        p = target.profile
        initial = {
            "last_name": target.last_name,
            "first_name": target.first_name,
            "username": target.username,
            "department": p.department_id,
            "position": p.position,
            "is_staff": target.is_staff,
            "is_active": target.is_active,
        }
    form = EmployeeForm(request.POST or None, initial=initial, user=target)

    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        user = target or User()
        user.username = d["username"]
        user.last_name = d["last_name"].strip()
        user.first_name = d["first_name"].strip()
        user.is_staff = d["is_staff"]
        user.is_active = d["is_active"] if target else True
        if target and target.pk == request.user.pk:  # o'zini bloklab qo'ymasin
            user.is_staff, user.is_active = True, True
        password = d["password"]
        generated = False
        if not target and not password:
            password, generated = new_password(), True
        if password:
            user.set_password(password)
        user.save()
        profile = user.profile
        profile.department = d["department"]
        profile.position = d["position"].strip()
        profile.save()
        if not target:
            messages.success(
                request, f"Xodim qo'shildi. Login: {user.username} · Parol: {password}"
            )
        elif password:
            messages.success(request, f"Saqlandi. Yangi parol: {password}")
        else:
            messages.success(request, "O'zgarishlar saqlandi.")
        return redirect("panel_employees")

    return render(request, "panel/employee_form.html", {"form": form, "target": target})


@staff_required
@require_POST
def employee_reset_password(request, pk):
    user = get_object_or_404(User, pk=pk)
    pw = new_password()
    user.set_password(pw)
    user.save(update_fields=["password"])
    messages.success(request, f"{user.get_full_name() or user.username} uchun yangi parol: {pw}")
    return redirect("panel_employee_edit", pk=pk)


@staff_required
@require_POST
def employee_toggle(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user.pk == request.user.pk:
        messages.error(request, "O'zingizni o'chirib bo'lmaydi.")
    else:
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        messages.success(
            request,
            f"{user.get_full_name() or user.username} " + ("faollashtirildi." if user.is_active else "o'chirildi (hisobotlari saqlanadi)."),
        )
    return redirect("panel_employees")


# ---------------------------------------------------------------- Bo'limlar

@staff_required
def departments(request):
    if request.method == "POST":
        action = request.POST.get("action")
        name = (request.POST.get("name") or "").strip()
        if action == "add":
            if not name:
                messages.error(request, "Bo'lim nomini yozing.")
            elif Department.objects.filter(name__iexact=name).exists():
                messages.error(request, "Bunday bo'lim bor.")
            else:
                Department.objects.create(name=name)
                messages.success(request, f"«{name}» bo'limi qo'shildi.")
        elif action == "rename":
            dep = get_object_or_404(Department, pk=request.POST.get("id"))
            if name and not Department.objects.filter(name__iexact=name).exclude(pk=dep.pk).exists():
                dep.name = name
                dep.save()
                messages.success(request, "Nom o'zgartirildi.")
            else:
                messages.error(request, "Nom bo'sh yoki band.")
        elif action == "delete":
            dep = get_object_or_404(Department, pk=request.POST.get("id"))
            dep.delete()
            messages.success(request, "Bo'lim o'chirildi. Xodimlar bo'limsiz qoldi.")
        return redirect("panel_departments")

    deps = Department.objects.annotate(n=Count("profile", filter=Q(profile__user__is_active=True)))
    return render(request, "panel/departments.html", {"departments": deps})


# ---------------------------------------------------------------- Eslatmalar

@staff_required
def reminders(request):
    qs = ReminderSlot.objects.order_by("time")
    if request.method == "POST":
        fs = ReminderFormSet(request.POST, queryset=qs)
        if fs.is_valid():
            fs.save()
            messages.success(request, "Eslatmalar saqlandi.")
            return redirect("panel_reminders")
    else:
        fs = ReminderFormSet(queryset=qs)
    return render(request, "panel/reminders.html", {"formset": fs})


# ---------------------------------------------------------------- Import

SAMPLE_CSV = (
    "full_name,department,position,is_manager,username,password\r\n"
    "Aliyev Vali,IT bo'limi,Dasturchi,,,\r\n"
    "Karimova Dilnoza,Buxgalteriya,Buxgalter,,,\r\n"
    "Rahimov Sardor,IT bo'limi,Bo'lim boshlig'i,ha,,\r\n"
)


@staff_required
def import_page(request):
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        f = form.cleaned_data["file"]
        try:
            results = import_rows(read_rows(f.name, f.read()))
        except ImportError_ as e:
            form.add_error("file", str(e))
        except Exception:
            form.add_error("file", "Faylni o'qishda xato. Shablonga mosligini tekshiring.")
        else:
            return render(
                request,
                "panel/import_result.html",
                {
                    "results": results,
                    "created_n": sum(1 for r in results if r["created"]),
                    "updated_n": sum(1 for r in results if not r["created"]),
                },
            )
    return render(request, "panel/import.html", {"form": form})


@staff_required
def import_sample(request):
    resp = HttpResponse("﻿" + SAMPLE_CSV, content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="xodimlar_shablon.csv"'
    return resp
