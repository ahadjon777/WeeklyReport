"""Hisobot davrlari: hafta, oy, chorak, yarim yil, yil."""
import calendar
import datetime as dt

PERIODS = [
    ("week", "Haftalik"),
    ("month", "Oylik"),
    ("quarter", "Choraklik"),
    ("half", "Yarim yillik"),
    ("year", "Yillik"),
]
PERIOD_KEYS = [p[0] for p in PERIODS]

MONTHS_UZ = [
    "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
    "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr",
]
WEEKDAYS_UZ = [
    "Dushanba", "Seshanba", "Chorshanba", "Payshanba",
    "Juma", "Shanba", "Yakshanba",
]


def _month_end(year, month):
    return dt.date(year, month, calendar.monthrange(year, month)[1])


def get_range(period, ref):
    """(boshlanish, tugash, nom) qaytaradi."""
    if period == "week":
        start = ref - dt.timedelta(days=ref.weekday())
        end = start + dt.timedelta(days=6)
        label = f"{start:%d.%m.%Y} – {end:%d.%m.%Y}"
    elif period == "month":
        start = ref.replace(day=1)
        end = _month_end(ref.year, ref.month)
        label = f"{MONTHS_UZ[ref.month - 1]} {ref.year}"
    elif period == "quarter":
        q = (ref.month - 1) // 3
        start = dt.date(ref.year, q * 3 + 1, 1)
        end = _month_end(ref.year, q * 3 + 3)
        label = f"{q + 1}-chorak, {ref.year}"
    elif period == "half":
        h = 0 if ref.month <= 6 else 1
        start = dt.date(ref.year, h * 6 + 1, 1)
        end = _month_end(ref.year, h * 6 + 6)
        label = f"{h + 1}-yarim yillik, {ref.year}"
    else:  # year
        start = dt.date(ref.year, 1, 1)
        end = dt.date(ref.year, 12, 31)
        label = f"{ref.year}-yil"
    return start, end, label


def period_title(period):
    return dict(PERIODS).get(period, "Haftalik")
