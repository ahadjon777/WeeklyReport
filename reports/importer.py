"""Xodimlarni CSV / Excel fayldan ommaviy qo'shish (panel va buyruq uchun umumiy)."""
import csv
import random
import re
from io import BytesIO, StringIO

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Department

User = get_user_model()

ALIASES = {
    "full_name": {"full_name", "fio", "f.i.o", "f.i.sh", "xodim", "ism", "ismi", "ism familiya", "familiya ism"},
    "department": {"department", "bolim", "bo'lim", "bo‘lim", "bo`lim"},
    "position": {"position", "lavozim"},
    "is_manager": {"is_manager", "rahbar", "manager", "admin"},
    "username": {"username", "login"},
    "password": {"password", "parol"},
}

CYR = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh",
    "ъ": "", "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya", "ў": "o", "қ": "q", "ғ": "g", "ҳ": "h",
}


class ImportError_(Exception):
    pass


def _canon(header):
    h = (header or "").strip().lower()
    for key, names in ALIASES.items():
        if h in names:
            return key
    return None


def _normalize(rows_iter):
    out = []
    for raw in rows_iter:
        row = {}
        for k, v in raw.items():
            key = _canon(k)
            if key:
                row[key] = "" if v is None else str(v).strip()
        if row.get("full_name"):
            out.append(row)
    return out


def read_rows(filename, data):
    """Fayl baytlaridan xodimlar ro'yxatini (dict) o'qiydi."""
    name = (filename or "").lower()
    if name.endswith(".xlsx"):
        from openpyxl import load_workbook

        ws = load_workbook(BytesIO(data), read_only=True, data_only=True).active
        it = ws.iter_rows(values_only=True)
        try:
            headers = next(it)
        except StopIteration:
            return []
        dicts = (dict(zip(headers, r)) for r in it)
        rows = _normalize(dicts)
    else:
        for enc in ("utf-8-sig", "cp1251"):
            try:
                text = data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ImportError_("Fayl kodirovkasini o'qib bo'lmadi. UTF-8 formatida saqlang.")
        first = text.splitlines()[0] if text.strip() else ""
        delim = ";" if first.count(";") > first.count(",") else ","
        rows = _normalize(csv.DictReader(StringIO(text), delimiter=delim))
    if not rows:
        raise ImportError_(
            "Fayldan xodim topilmadi. Birinchi qatorda sarlavha (full_name) bo'lishi kerak."
        )
    return rows


def _translit(s):
    return "".join(CYR.get(ch, ch) for ch in s.lower())


def make_username(full_name, taken):
    base = _translit(full_name).replace("'", "").replace("‘", "").replace("’", "").replace("`", "")
    base = re.sub(r"[^a-z0-9]+", ".", base).strip(".") or "xodim"
    name, i = base, 1
    while name in taken or User.objects.filter(username=name).exists():
        i += 1
        name = f"{base}{i}"
    taken.add(name)
    return name


def new_password():
    return str(random.randint(100000, 999999))


@transaction.atomic
def import_rows(rows):
    """Xodimlarni yaratadi/yangilaydi. Natija ro'yxatini qaytaradi."""
    taken, results = set(), []
    for row in rows:
        full = row["full_name"]
        username = row.get("username") or make_username(full, taken)
        parts = full.split()
        user, created = User.objects.get_or_create(username=username)
        user.last_name = parts[0]
        user.first_name = " ".join(parts[1:])
        if row.get("is_manager", "").lower() in ("1", "ha", "yes", "true", "x"):
            user.is_staff = True
        password = row.get("password") or ""
        if created and not password:
            password = new_password()
        if password:
            user.set_password(password)
        else:
            password = ""
        user.save()
        profile = user.profile
        if row.get("department"):
            profile.department, _ = Department.objects.get_or_create(name=row["department"])
        if row.get("position"):
            profile.position = row["position"]
        profile.save()
        results.append(
            {
                "name": full,
                "username": username,
                "password": password,
                "department": row.get("department", ""),
                "created": created,
                "manager": user.is_staff,
            }
        )
    return results
