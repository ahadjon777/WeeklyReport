"""Excel (.xlsx) eksport."""
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .models import WorkEntry

STATUS_LABELS = dict(WorkEntry.STATUS_CHOICES)
HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
HEADER_FONT = Font(bold=True, color="FFFFFF")


def _header(ws, row, titles):
    for col, title in enumerate(titles, start=1):
        c = ws.cell(row=row, column=col, value=title)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _widths(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def build_workbook(rows, totals, title, period_name):
    wb = Workbook()

    ws = wb.active
    ws.title = "Xulosa"
    ws["A1"] = f"{period_name} hisobot — {title}"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = (
        f"Xodimlar: {totals['employees']}   |   Yozuvlar: {totals['entries']}   |   "
        f"Jami soat: {totals['hours']}   |   Ish kunlari: {totals['work_days']}"
    )
    _header(
        ws,
        4,
        [
            "Xodim", "Bo'lim", "Lavozim", "Yozuvlar", "Jami soat",
            "Hisobot kiritilgan kunlar", "Kiritilmagan ish kunlari",
            "Bajarildi", "Jarayonda", "To'siq bor",
        ],
    )
    r = 5
    for row in rows:
        ws.append(
            [
                row["name"], row["department"], row["position"], row["count"],
                float(row["hours"]), row["days_reported"], row["missing_days"],
                row["done"], row["progress"], row["blocked"],
            ]
        )
        r += 1
    last = r - 1
    ws.cell(row=r, column=1, value="JAMI").font = Font(bold=True)
    for col in (4, 5, 6, 7, 8, 9, 10):
        letter = get_column_letter(col)
        c = ws.cell(row=r, column=col, value=f"=SUM({letter}5:{letter}{last})" if last >= 5 else 0)
        c.font = Font(bold=True)
    ws.freeze_panes = "A5"
    _widths(ws, [28, 22, 22, 11, 11, 16, 16, 11, 11, 11])
    ws.row_dimensions[4].height = 32

    wd = wb.create_sheet("Batafsil")
    _header(wd, 1, ["Sana", "Xodim", "Bo'lim", "Bajarilgan ish", "Soat", "Holati"])
    for row in rows:
        for day, entries in row["days"]:
            for e in entries:
                wd.append(
                    [
                        day, row["name"], row["department"], e.description,
                        float(e.hours) if e.hours is not None else None, STATUS_LABELS.get(e.status, e.status),
                    ]
                )
    for cells in wd.iter_rows(min_row=2, max_col=1):
        cells[0].number_format = "DD.MM.YYYY"
    for cells in wd.iter_rows(min_row=2, min_col=4, max_col=4):
        cells[0].alignment = Alignment(wrap_text=True, vertical="top")
    wd.freeze_panes = "A2"
    wd.auto_filter.ref = f"A1:F{max(wd.max_row, 2)}"
    _widths(wd, [12, 28, 22, 70, 8, 14])

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
