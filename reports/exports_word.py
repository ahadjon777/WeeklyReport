"""Word (.docx) hisobot shabloni."""
from collections import OrderedDict
from decimal import Decimal
from io import BytesIO

from django.conf import settings
from django.utils import timezone
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from .models import WorkEntry
from .periods import MONTHS_UZ

STATUS = dict(WorkEntry.STATUS_CHOICES)
TITLES = {
    "week": "HAFTALIK HISOBOT",
    "month": "OYLIK HISOBOT",
    "quarter": "CHORAKLIK HISOBOT",
    "half": "YARIM YILLIK HISOBOT",
    "year": "YILLIK HISOBOT",
}
BLUE = RGBColor(0x1F, 0x4E, 0x79)


def _fmt(h):
    return "" if h is None else f"{float(h):g}"


def _shade(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def _repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def _no_split(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:cantSplit")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def _cell(cell, text, bold=False, align=None, size=10, color=None):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(str(text))
    run.bold = bold
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color
    if align == "c":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "r":
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT


def _table(doc, headers, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        _cell(c, h, bold=True, align="c", size=10, color=RGBColor(0xFF, 0xFF, 0xFF))
        _shade(c, "1F4E79")
        c.width = Cm(widths[i])
    _repeat_header(t.rows[0])
    for i, w_ in enumerate(widths):
        t.columns[i].width = Cm(w_)
    tblPr = t._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)
    return t


def _add_row(t, values, widths, aligns=None, bold=False):
    row = t.add_row()
    _no_split(row)
    for i, v in enumerate(values):
        _cell(row.cells[i], v, bold=bold, align=(aligns[i] if aligns else None))
        row.cells[i].width = Cm(widths[i])
    return row


def _heading(doc, text, size=13):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(size)
    r.font.color.rgb = BLUE
    return p


def _page_number_footer(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Sahifa ")
    run.font.size = Pt(9)
    for kind, text in (("begin", None), (None, "PAGE"), ("end", None)):
        r = p.add_run()
        r.font.size = Pt(9)
        if kind:
            fc = OxmlElement("w:fldChar")
            fc.set(qn("w:fldCharType"), kind)
            r._r.append(fc)
        else:
            it = OxmlElement("w:instrText")
            it.set(qn("xml:space"), "preserve")
            it.text = text
            r._r.append(it)


def _monthly(days):
    """[(sana, [yozuvlar])] -> OrderedDict[(yil, oy)] = [yozuvlar soni, soat]"""
    out = OrderedDict()
    for day, entries in days:
        key = (day.year, day.month)
        rec = out.setdefault(key, [0, Decimal("0")])
        rec[0] += len(entries)
        rec[1] += sum((e.hours for e in entries), Decimal("0"))
    return out


def build_docx(rows, totals, period, period_name, label, start, end, department_name="", detailed=True):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin, sec.right_margin = Cm(2), Cm(1.5)
    sec.top_margin, sec.bottom_margin = Cm(1.8), Cm(1.8)
    st = doc.styles["Normal"]
    st.font.name = "Calibri"
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    st.font.size = Pt(11)
    _page_number_footer(sec)

    sh = totals["hours"] > 0  # soat ixtiyoriy: kiritilgan bo'lsagina ustun chiqadi
    org = getattr(settings, "ORG_NAME", "") or ""
    if org:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(org.upper())
        r.bold = True
        r.font.size = Pt(12)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    r = p.add_run(TITLES.get(period, "HISOBOT"))
    r.bold = True
    r.font.size = Pt(18)
    r.font.color.rgb = BLUE

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rng = f"{start:%d.%m.%Y} – {end:%d.%m.%Y}"
    p.add_run(f"Davr: {label}" + ("" if rng in label else f"  ({rng})")).font.size = Pt(12)
    if department_name:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run(f"Bo'lim: {department_name}").font.size = Pt(12)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(f"Tuzilgan sana: {timezone.localdate():%d.%m.%Y}")
    r.font.size = Pt(10)
    r.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    # 1. Umumiy ko'rsatkichlar
    _heading(doc, "1. Umumiy ko'rsatkichlar")
    w = [9, 7.5]
    t = _table(doc, ["Ko'rsatkich", "Qiymat"], w)
    for name, val in [
        ("Xodimlar soni", totals["employees"]),
        ("Ish kunlari soni", totals["work_days"]),
        ("Jami yozuvlar (bajarilgan ishlar)", totals["entries"]),
        *([("Jami sarflangan soat", _fmt(totals["hours"]))] if sh else []),
        ("Hisobot kiritilmagan ish kunlari (jami)", totals["missing_days"]),
    ]:
        _add_row(t, [name, val], w, aligns=[None, "c"])

    # 2. Xodimlar bo'yicha
    _heading(doc, "2. Xodimlar bo'yicha yig'ma jadval")
    if sh:
        w = [0.9, 4.6, 3.2, 1.6, 1.6, 2.3, 2.3]
        heads = ["№", "Xodim", "Bo'lim", "Yozuv", "Soat", "Hisobot kunlari", "Kiritilmagan"]
        al = ["c", None, None, "c", "c", "c", "c"]
    else:
        w = [0.9, 5.4, 3.8, 1.8, 2.8, 2.8]
        heads = ["№", "Xodim", "Bo'lim", "Yozuv", "Hisobot kunlari", "Kiritilmagan"]
        al = ["c", None, None, "c", "c", "c"]
    t = _table(doc, heads, w)
    for i, r_ in enumerate(rows, 1):
        vals = [i, r_["name"], r_["department"] or "—", r_["count"]]
        if sh:
            vals.append(_fmt(r_["hours"]))
        vals += [r_["days_reported"], r_["missing_days"]]
        _add_row(t, vals, w, aligns=al)
    tot = ["", "JAMI", "", totals["entries"]]
    if sh:
        tot.append(_fmt(totals["hours"]))
    tot += ["", totals["missing_days"]]
    _add_row(t, tot, w, aligns=al, bold=True)

    # 3. Batafsil
    _heading(doc, "3. Bajarilgan ishlar" + (" (batafsil)" if detailed else " (oylar kesimida)"))
    if not rows:
        doc.add_paragraph("Tanlangan davr uchun ma'lumot topilmadi.")
    for i, r_ in enumerate(rows, 1):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(f"{i}. {r_['name']}")
        run.bold = True
        extra = ", ".join(x for x in (r_["position"], r_["department"]) if x)
        if extra:
            run2 = p.add_run(f" — {extra}")
            run2.font.size = Pt(10)
        if not r_["days"]:
            q = doc.add_paragraph("Bu davrda yozuv kiritilmagan.")
            q.runs[0].italic = True
            continue
        if detailed:
            if sh:
                w = [2.2, 10.2, 1.6, 2.5]
                heads = ["Sana", "Bajarilgan ish", "Soat", "Holati"]
                al = ["c", None, "c", "c"]
            else:
                w = [2.4, 11.6, 2.5]
                heads = ["Sana", "Bajarilgan ish", "Holati"]
                al = ["c", None, "c"]
            t = _table(doc, heads, w)
            for day, entries in r_["days"]:
                for e in entries:
                    vals = [f"{day:%d.%m.%Y}", e.description]
                    if sh:
                        vals.append(_fmt(e.hours))
                    vals.append(STATUS.get(e.status, e.status))
                    _add_row(t, vals, w, aligns=al)
            if sh:
                _add_row(t, ["", "Jami", _fmt(r_["hours"]), ""], w, aligns=["c", "r", "c", "c"], bold=True)
            else:
                _add_row(t, ["", f"Jami yozuv: {r_['count']}", ""], w, aligns=["c", "r", "c"], bold=True)
        else:
            if sh:
                w = [6, 4, 4]
                heads = ["Oy", "Yozuvlar soni", "Soat"]
            else:
                w = [8, 6]
                heads = ["Oy", "Yozuvlar soni"]
            t = _table(doc, heads, w)
            for (y, m), (n, h) in _monthly(r_["days"]).items():
                vals = [f"{MONTHS_UZ[m - 1]} {y}", n] + ([_fmt(h)] if sh else [])
                _add_row(t, vals, w, aligns=[None, "c", "c"][: len(w)])
            tot = ["Jami", r_["count"]] + ([_fmt(r_["hours"])] if sh else [])
            _add_row(t, tot, w, aligns=[None, "c", "c"][: len(w)], bold=True)
        s = r_
        q = doc.add_paragraph()
        q.paragraph_format.space_before = Pt(2)
        rr = q.add_run(f"Holatlar: bajarildi — {s['done']}, jarayonda — {s['progress']}, to'siq bor — {s['blocked']}")
        rr.font.size = Pt(9)
        rr.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    # Imzolar
    _heading(doc, "Tasdiqlash")
    t = doc.add_table(rows=2, cols=3)
    t.autofit = False
    labels = ["Tayyorladi:", "Tekshirdi:", "Tasdiqladi:"]
    for i, lab in enumerate(labels):
        _cell(t.rows[0].cells[i], lab, bold=True, size=11)
        _cell(t.rows[1].cells[i], "____________________\n(lavozim, F.I.Sh., imzo)\n\n«___» ____________ 20___ y.", size=9)
        t.rows[0].cells[i].width = t.rows[1].cells[i].width = Cm(5.6)

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()
