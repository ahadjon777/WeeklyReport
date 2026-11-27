"""Xodimlarni CSV/Excel fayldan ommaviy qo'shish. Natija: parollar.csv"""
import csv

from django.core.management.base import BaseCommand, CommandError

from reports.importer import ImportError_, import_rows, read_rows


class Command(BaseCommand):
    help = "Xodimlarni fayldan import qiladi va parollar.csv yaratadi"

    def add_arguments(self, parser):
        parser.add_argument("csv_path")
        parser.add_argument("--out", default="parollar.csv")

    def handle(self, *args, csv_path, out, **opts):
        try:
            with open(csv_path, "rb") as f:
                rows = read_rows(csv_path, f.read())
        except OSError as e:
            raise CommandError(f"Faylni ochib bo'lmadi: {e}")
        except ImportError_ as e:
            raise CommandError(str(e))
        results = import_rows(rows)
        with open(out, "w", newline="", encoding="utf-8-sig") as o:
            w = csv.writer(o)
            w.writerow(["Xodim", "Login", "Parol", "Bo'lim"])
            for r in results:
                w.writerow([r["name"], r["username"], r["password"] or "(o'zgartirilmagan)", r["department"]])
        self.stdout.write(self.style.SUCCESS(f"{len(results)} ta xodim qo'shildi. Parollar: {out}"))
