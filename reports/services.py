"""Yig'ma hisobotlarni hisoblash."""
import datetime as dt
from collections import Counter, defaultdict
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

from .models import WorkEntry


def work_days_between(start, end):
    days = set()
    d = start
    while d <= end:
        if d.weekday() in settings.WORK_DAYS:
            days.add(d)
        d += dt.timedelta(days=1)
    return days


def employees_for(request_user, department_id=None, user_id=None):
    User = get_user_model()
    qs = User.objects.filter(is_active=True)
    if not request_user.is_staff:
        return qs.filter(pk=request_user.pk)
    # Rahbar/admin hisoblari faqat o'zida yozuv bo'lsa ro'yxatga kiradi
    qs = qs.filter(Q(is_staff=False) | Q(entries__isnull=False))
    if department_id:
        qs = qs.filter(profile__department_id=department_id)
    if user_id:
        qs = qs.filter(pk=user_id)
    return qs.distinct()


def display_name(user):
    return user.get_full_name() or user.username


def build_summary(users_qs, start, end):
    today = timezone.localdate()
    users = list(
        users_qs.select_related("profile__department").order_by(
            "last_name", "first_name", "username"
        )
    )
    entries = (
        WorkEntry.objects.filter(user__in=users, date__range=(start, end))
        .order_by("date", "created_at")
    )
    by_user = defaultdict(list)
    for e in entries:
        by_user[e.user_id].append(e)

    expected = work_days_between(start, min(end, today)) if start <= today else set()

    rows = []
    total_hours = Decimal("0")
    total_entries = 0
    total_missing = 0
    for u in users:
        es = by_user.get(u.id, [])
        hours = sum(((e.hours or Decimal("0")) for e in es), Decimal("0"))
        reported = {e.date for e in es}
        statuses = Counter(e.status for e in es)
        days = defaultdict(list)
        for e in es:
            days[e.date].append(e)
        profile = getattr(u, "profile", None)
        department = profile.department.name if profile and profile.department else ""
        position = profile.position if profile else ""
        missing = len(expected - reported)
        rows.append(
            {
                "user": u,
                "name": display_name(u),
                "department": department,
                "position": position,
                "count": len(es),
                "hours": hours,
                "days_reported": len(reported),
                "missing_days": missing,
                "done": statuses.get(WorkEntry.STATUS_DONE, 0),
                "progress": statuses.get(WorkEntry.STATUS_PROGRESS, 0),
                "blocked": statuses.get(WorkEntry.STATUS_BLOCKED, 0),
                "days": sorted(days.items()),
            }
        )
        total_hours += hours
        total_entries += len(es)
        total_missing += missing

    totals = {
        "employees": len(rows),
        "entries": total_entries,
        "hours": total_hours,
        "missing_days": total_missing,
        "work_days": len(expected),
    }
    return rows, totals
