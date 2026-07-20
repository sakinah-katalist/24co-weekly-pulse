"""
24co Weekly Pulse — PDF Report
Sections: at-a-glance KPIs, revenue by period, pipeline cards,
          CRM stage chart, monthly revenue chart, overdue payments.
"""

import io
import calendar as _cal
from datetime import datetime, timedelta, timezone
from config import ORG_FULL_NAMES
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable, KeepTogether, PageBreak,
)

W, H   = landscape(A4)
MARGIN = 18 * mm
REPORT_TITLE = "24co Weekly Pulse"
COMPANY      = "Katalist Venture"

C = {
    "teal":         colors.HexColor("#1A7F7A"),
    "teal_light":   colors.HexColor("#E6F4F3"),
    "yellow":       colors.HexColor("#F5C800"),
    "yellow_light": colors.HexColor("#FFFDE7"),
    "red":          colors.HexColor("#C0392B"),
    "red_light":    colors.HexColor("#FDECEA"),
    "green":        colors.HexColor("#27AE60"),
    "green_light":  colors.HexColor("#E8F8EE"),
    "dark":         colors.HexColor("#1C1C1C"),
    "mid":          colors.HexColor("#555555"),
    "muted":        colors.HexColor("#888888"),
    "light":        colors.HexColor("#F8F9FA"),
    "border":       colors.HexColor("#DDDDDD"),
    "white":        colors.white,
    "header_bg":    colors.HexColor("#0D3349"),
}
C["gold"] = C["yellow"]


def _expand_org(name: str) -> str:
    if not name:
        return name
    if name in ORG_FULL_NAMES:
        return ORG_FULL_NAMES[name]
    for key in sorted(ORG_FULL_NAMES, key=len, reverse=True):
        if name.startswith(key):
            sep = name[len(key):]
            if sep and sep[0] in (" ", "-", "|", "("):
                suffix = sep.strip(" -|()")
                return f"{ORG_FULL_NAMES[key]} — {suffix}" if suffix else ORG_FULL_NAMES[key]
    return name


def _is_paid_only(s):
    t = (s or "").lower()
    if "before adam" in t:
        return False
    return "paid" in t


def _is_revenue(s):
    t = (s or "").lower()
    if "before adam" in t:
        return False
    return "paid" in t or "closed" in t


def _is_stale_pipeline(d, report_date, weeks=5):
    stg = (d.get("stage") or "").lower()
    if not any(k in stg for k in ("almost", "proposal", "quotation")):
        return False
    cd = (d.get("added_date") or d.get("close_date") or "")[:10]
    if not cd:
        return False
    try:
        deal_dt = datetime.strptime(cd, "%Y-%m-%d")
        rd = report_date if hasattr(report_date, "strftime") else datetime.strptime(str(report_date)[:10], "%Y-%m-%d")
        year_start = datetime(rd.year, 1, 1)
        year_end   = datetime(rd.year, 12, 31)
        if not (year_start <= deal_dt <= year_end):
            return False
        return deal_dt <= rd - timedelta(days=weeks * 7)
    except ValueError:
        return False


def _awaiting_payment(deals):
    return [d for d in deals
            if "closed" in (d.get("stage") or "").lower()
            and "before adam" not in (d.get("stage") or "").lower()]


def _weeks_overdue(d, report_date):
    ref = d.get("train_date") or d.get("added_date") or ""
    if not ref:
        return None
    try:
        return (report_date - datetime.strptime(ref[:10], "%Y-%m-%d")).days / 7
    except Exception:
        return None


def _rev_date(d):
    return (d.get("payment_received_date") or d.get("close_date") or "")[:10]


def _revenue_last_7_days(deals, report_date) -> float:
    if not hasattr(report_date, "strftime"):
        return 0.0
    cutoff = (report_date - timedelta(days=7)).strftime("%Y-%m-%d")
    today  = report_date.strftime("%Y-%m-%d")
    return sum(d.get("deal_value", 0) or 0 for d in deals
               if _is_revenue(d.get("stage", ""))
               and cutoff <= (d.get("payment_received_date") or d.get("close_date") or "") <= today)


def _session_type(s: dict) -> str:
    return "Public" if (s.get("signup") or "").strip() else "In-house"


def _pending_collection(deals, report_date) -> list:
    cutoff = report_date.strftime("%Y-%m-%d") if hasattr(report_date, "strftime") else str(report_date)
    return [d for d in deals
            if d.get("train_date") and d["train_date"] <= cutoff
            and not _is_revenue(d.get("stage", ""))]


def _hex(c) -> str:
    raw = c.hexval()
    raw = raw[2:] if raw.startswith(("0x", "0X")) else raw.lstrip("#")
    return raw.upper().zfill(6)


def _img_from_bytes(data: bytes, w_mm: float, max_h_mm: float = 130) -> Image:
    # Preserve aspect ratio explicitly — reportlab keeps the PNG's natural
    # pixel height when only width is given, which distorts the image and
    # can overflow the page (creating blank/orphan pages).
    from reportlab.lib.utils import ImageReader
    iw, ih = ImageReader(io.BytesIO(data)).getSize()
    w = w_mm * mm
    h = w * ih / iw
    max_h = max_h_mm * mm
    if h > max_h:
        w = w * max_h / h
        h = max_h
    img = Image(io.BytesIO(data), width=w, height=h)
    img.hAlign = "CENTER"
    return img


def _styles():
    base = getSampleStyleSheet()

    def _s(name, size, font, color, align=TA_LEFT, leading_mult=1.5):
        return ParagraphStyle(name, parent=base["Normal"],
                              fontSize=size, leading=size * leading_mult,
                              fontName=font, textColor=color, alignment=align)

    return {
        "SectionHead":  _s("SectionHead",  12, "Helvetica-Bold",    C["dark"]),
        "SectionSub":   _s("SectionSub",    8, "Helvetica-Oblique", C["muted"]),
        "Narrative":    _s("Narrative",    9.5,"Helvetica",         C["dark"],    leading_mult=1.6),
        "NarrativeBold":_s("NarrativeBold",9.5,"Helvetica-Bold",   C["dark"],    leading_mult=1.6),
        "KPIVal":       _s("KPIVal",       15, "Helvetica-Bold",    C["dark"],    TA_CENTER),
        "KPILbl":       _s("KPILbl",        8, "Helvetica-Bold",    C["muted"],   TA_CENTER),
        "KPISub":       _s("KPISub",        7, "Helvetica",         C["muted"],   TA_CENTER),
        "CardOrg":      _s("CardOrg",      10, "Helvetica-Bold",    C["dark"]),
        "TableHead":    _s("TableHead",     8, "Helvetica-Bold",    C["white"],   TA_LEFT),
        "TableCell":    _s("TableCell",     8, "Helvetica",         C["dark"]),
        "TableCellR":   _s("TableCellR",    8, "Helvetica",         C["dark"],    TA_RIGHT),
        "SmallMuted":   _s("SmallMuted",    7, "Helvetica",         C["muted"]),
        "WarnHead":     _s("WarnHead",      9, "Helvetica-Bold",    C["red"]),
        "Highlight":    _s("Highlight",     9, "Helvetica-Bold",    C["teal"]),
    }


def _hr(c=None):
    return HRFlowable(width="100%", thickness=0.8,
                      color=c or C["border"], spaceAfter=3)


def _sp(n=4):
    return Spacer(1, n * mm)


def _callout(text, bg, border, styles, key="Narrative"):
    cell = Table([[Paragraph(text, styles[key])]], colWidths=[W - 2*MARGIN])
    cell.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("TOPPADDING",    (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
        ("BOX",           (0,0),(-1,-1), 0.5, border),
    ]))
    return cell


# ── KPI card grid ─────────────────────────────────────────────────────────────
def _kpi_card(val_str, label, sub, bg, val_color):
    """Single KPI card as a 1-cell Table."""
    inner = Table([
        [Paragraph(val_str, ParagraphStyle("_kv", fontName="Helvetica-Bold",
                   fontSize=13, leading=16, textColor=val_color, alignment=TA_CENTER))],
        [Paragraph(label,   ParagraphStyle("_kl", fontName="Helvetica-Bold",
                   fontSize=7.5, leading=11, textColor=C["muted"], alignment=TA_CENTER))],
        [Paragraph(sub,     ParagraphStyle("_ks", fontName="Helvetica",
                   fontSize=7, leading=10, textColor=C["muted"], alignment=TA_CENTER))],
    ], colWidths=[None])
    inner.setStyle(TableStyle([
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
    ]))
    card = Table([[inner]], colWidths=[None])
    card.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("RIGHTPADDING",  (0,0),(-1,-1), 8),
        ("BOX",           (0,0),(-1,-1), 0.5, C["border"]),
    ]))
    return card


def _kpi_grid(cards, n_cols, full_w_mm):
    """Lay out a list of card items in n_cols columns."""
    col_w = (full_w_mm / n_cols) * mm
    rows = []
    for i in range(0, len(cards), n_cols):
        row = cards[i:i+n_cols]
        while len(row) < n_cols:
            row.append(Spacer(1, 1))
        rows.append(row)
    t = Table(rows, colWidths=[col_w] * n_cols)
    t.setStyle(TableStyle([
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",   (0,0),(-1,-1), 3),
        ("RIGHTPADDING",  (0,0),(-1,-1), 3),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
    ]))
    return t


# ── Awaiting payment table ────────────────────────────────────────────────────
def _pending_table(deals, report_date, styles):
    hdr = [Paragraph(h, styles["TableHead"]) for h in
           ["Organisation", "Collection Status", "Amount Owed", "Training Date", "Contact"]]
    cw = [(W - 2*MARGIN) * f for f in [0.32, 0.26, 0.15, 0.14, 0.13]]
    red_hex = _hex(C["red"])

    rows = []
    for d in sorted(deals, key=lambda x: -(x.get("deal_value") or 0)):
        w = _weeks_overdue(d, report_date)
        if w is not None and w > 5:
            status = f'<font color="#{red_hex}"><b>🔴 {int(w)}w overdue — re-nudge</b></font>'
        elif w is not None:
            status = f"🟡 {int(w)}w since training" if w > 0 else "🟡 Training upcoming"
        else:
            status = "⚪ No training date"

        rows.append([
            Paragraph(_expand_org(d.get("org_name", "")), styles["TableCell"]),
            Paragraph(status,                              styles["TableCell"]),
            Paragraph(f"RM {d['deal_value']:,.0f}" if d.get("deal_value") else "—",
                      styles["TableCellR"]),
            Paragraph(d.get("train_date") or "—",         styles["TableCell"]),
            Paragraph(d.get("contact", "") or "—",        styles["TableCell"]),
        ])

    total_amt = sum(d.get("deal_value", 0) or 0 for d in deals)
    rows.append([
        Paragraph(f"<b>TOTAL ({len(deals)} deals)</b>", styles["TableCell"]),
        Paragraph("", styles["TableCell"]),
        Paragraph(f"<b>RM {total_amt:,.0f}</b>",        styles["TableCellR"]),
        Paragraph("", styles["TableCell"]),
        Paragraph("", styles["TableCell"]),
    ])

    t = Table([hdr] + rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  C["header_bg"]),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1), 8),
        ("ROWBACKGROUNDS",(0,1),(-1,-2), [C["white"], C["light"]]),
        ("BACKGROUND",    (0,-1),(-1,-1), C["yellow_light"]),
        ("FONTNAME",      (0,-1),(-1,-1), "Helvetica-Bold"),
        ("GRID",          (0,0),(-1,-1), 0.35, C["border"]),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 5),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ]))
    return t


# ── Main builder ──────────────────────────────────────────────────────────────
def build_pdf(leads, sessions, crm_deals, revenue_history,
              report_date, period_label, chart_bytes, output_path):

    styles = _styles()
    full_w = (W - 2*MARGIN) / mm

    from pathlib import Path as _Path
    _Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Top margin must clear the 20mm header strip drawn by on_page,
    # otherwise the first flowable on each page hides behind it.
    doc = SimpleDocTemplate(
        output_path, pagesize=landscape(A4),
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=28 * mm, bottomMargin=MARGIN,
    )

    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(C["header_bg"])
        canvas.rect(0, H - 20*mm, W, 20*mm, fill=1, stroke=0)
        canvas.setFillColor(C["white"])
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(MARGIN, H - 12*mm, REPORT_TITLE)
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(W - MARGIN, H - 11*mm,
                               f"{COMPANY}  ·  {report_date.strftime('%d %b %Y')}")
        canvas.drawRightString(W - MARGIN, H - 16*mm, f"Period: {period_label}")
        canvas.setFillColor(C["muted"])
        canvas.setFont("Helvetica", 6.5)
        canvas.drawCentredString(W / 2, 9*mm,
            f"Generated {datetime.now(timezone(timedelta(hours=8))).strftime('%d %b %Y %H:%M MYT')}"
            f"  ·  Page {doc.page}  ·  Confidential — Katalist Venture")
        canvas.restoreState()

    story = []
    add   = story.append

    # ── Pre-compute values ────────────────────────────────────────────────────
    rd_str   = report_date.strftime("%Y-%m-%d")
    d7_str   = (report_date - timedelta(days=7)).strftime("%Y-%m-%d")
    d14_str  = (report_date - timedelta(days=14)).strftime("%Y-%m-%d")
    year     = report_date.year
    month    = report_date.month

    paid_deals     = [d for d in crm_deals if _is_paid_only(d.get("stage", ""))]
    pipeline_deals = [d for d in crm_deals
                      if not _is_revenue(d.get("stage", ""))
                      and any(k in (d.get("stage") or "").lower()
                              for k in ("almost", "proposal", "quotation", "progress"))]
    # YTD = invoiced amount of Paid deals created (added) in the report year
    paid_total     = sum(d.get("deal_value", 0) or 0 for d in paid_deals
                         if (d.get("added_date") or "").startswith(str(year)))
    pipe_total     = sum(d.get("deal_value", 0) or 0 for d in pipeline_deals)

    # Revenue by period (paid only)
    def _period_rev(deals, from_str, to_str):
        return [(d, d.get("deal_value", 0) or 0) for d in deals
                if _rev_date(d) and from_str <= _rev_date(d) <= to_str]

    rev_7d_deals  = _period_rev(paid_deals, d7_str,  rd_str)
    rev_14d_deals = _period_rev(paid_deals, d14_str, rd_str)

    curr_m_start  = f"{year}-{month:02d}-01"
    rev_cm_deals  = _period_rev(paid_deals, curr_m_start, rd_str)

    def _qrange(q):
        starts = {1: f"{year}-01-01", 2: f"{year}-04-01",
                  3: f"{year}-07-01", 4: f"{year}-10-01"}
        ends   = {1: f"{year}-03-31", 2: f"{year}-06-30",
                  3: f"{year}-09-30", 4: f"{year}-12-31"}
        return starts[q], ends[q]

    q_deals = {}
    for q in (1, 2, 3, 4):
        qs, qe = _qrange(q)
        q_deals[q] = _period_rev(paid_deals, qs, qe)

    total_7d  = sum(v for _, v in rev_7d_deals)
    total_14d = sum(v for _, v in rev_14d_deals)
    total_cm  = sum(v for _, v in rev_cm_deals)

    # Awaiting payment (all Closed deals)
    pending      = _awaiting_payment(crm_deals)
    pending_total = sum(d.get("deal_value", 0) or 0 for d in pending)
    stale_pending = [d for d in pending if (_weeks_overdue(d, report_date) or 0) > 5]
    stale_pending_total = sum(d.get("deal_value", 0) or 0 for d in stale_pending)

    # Likely lost
    stale_pipe = [d for d in crm_deals
                  if not _is_revenue(d.get("stage", ""))
                  and _is_stale_pipeline(d, report_date)]
    stale_pipe_total = sum(d.get("deal_value", 0) or 0 for d in stale_pipe)

    # ── 1. THIS WEEK AT A GLANCE ──────────────────────────────────────────────
    add(KeepTogether([
        _hr(C["teal"]),
        Paragraph("This Week at a Glance", styles["SectionHead"]),
        Paragraph(period_label, styles["SectionSub"]),
        _sp(3),
    ]))

    glance_cards = [
        _kpi_card(f"RM {total_7d:,.0f}",   "REVENUE THIS WEEK",     "Past 7 days (Paid)",    C["teal_light"],   C["teal"]),
        _kpi_card(f"RM {paid_total:,.0f}",  "YTD REVENUE",           f"Paid deals added in {year}", C["green_light"],  C["green"]),
        _kpi_card(f"RM {pipe_total:,.0f}",  "ACTIVE PIPELINE",       f"{len(pipeline_deals)} deals · lifetime active pipeline",   C["yellow_light"], C["yellow"]),
        _kpi_card(f"RM {pending_total:,.0f}", "AWAITING PAYMENT (LIFETIME)", f"{len(pending)} Closed deals",   C["red_light"],    C["red"]),
        _kpi_card(f"RM {stale_pending_total:,.0f}", "OVERDUE >5 WKS", f"{len(stale_pending)} deals — re-nudge", C["red_light"], C["red"]),
        _kpi_card(f"RM {stale_pipe_total:,.0f}", "LIKELY LOST",      f"{len(stale_pipe)} stale deals · lifetime deals", C["yellow_light"], C["dark"]),
    ]
    add(_kpi_grid(glance_cards, 3, full_w))
    add(_sp(6))

    # ── 2. REVENUE BREAKDOWN BY PERIOD ───────────────────────────────────────
    add(KeepTogether([
        _hr(C["yellow"]),
        Paragraph("Revenue Breakdown by Period", styles["SectionHead"]),
        Paragraph(f"Paid deals only · {year}", styles["SectionSub"]),
        _sp(3),
    ]))

    rev_hdr = [Paragraph(h, styles["TableHead"])
               for h in ["Period", "Deals", "Revenue (Paid)"]]
    rev_cw  = [(W - 2*MARGIN) * f for f in [0.50, 0.15, 0.35]]

    q_names = {1: "Q1 (Jan – Mar)", 2: "Q2 (Apr – Jun)",
                3: "Q3 (Jul – Sep)", 4: "Q4 (Oct – Dec)"}
    curr_m_name = f"{_cal.month_name[month]} {year}"

    rev_rows = [
        [Paragraph("Past 7 days",      styles["TableCell"]),
         Paragraph(str(len(rev_7d_deals)),  styles["TableCell"]),
         Paragraph(f"RM {total_7d:,.0f}",  styles["TableCellR"])],
        [Paragraph("Past 14 days",     styles["TableCell"]),
         Paragraph(str(len(rev_14d_deals)), styles["TableCell"]),
         Paragraph(f"RM {total_14d:,.0f}", styles["TableCellR"])],
        [Paragraph(f"{curr_m_name} (so far)", styles["TableCell"]),
         Paragraph(str(len(rev_cm_deals)), styles["TableCell"]),
         Paragraph(f"RM {total_cm:,.0f}", styles["TableCellR"])],
    ]
    for q in (1, 2, 3, 4):
        qd = q_deals[q]
        qt = sum(v for _, v in qd)
        rev_rows.append([
            Paragraph(f"{q_names[q]} {year}", styles["TableCell"]),
            Paragraph(str(len(qd)),           styles["TableCell"]),
            Paragraph(f"RM {qt:,.0f}",        styles["TableCellR"]),
        ])

    rev_tbl = Table([rev_hdr] + rev_rows, colWidths=rev_cw, repeatRows=1)
    rev_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  C["header_bg"]),
        ("FONTSIZE",      (0,0),(-1,-1), 8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C["white"], C["light"]]),
        ("GRID",          (0,0),(-1,-1), 0.35, C["border"]),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 6),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        # Highlight current quarter row
        ("BACKGROUND",    (0, 3 + month // 4 + 1), (-1, 3 + month // 4 + 1), C["yellow_light"]),
    ]))
    add(rev_tbl)

    # ── 4 & 5. CHARTS ─────────────────────────────────────────────────────────
    # NOTE: never add a Spacer as the last flowable before a PageBreak —
    # if the page is already full it spills onto its own blank page.
    pipeline_chart = chart_bytes.get("pipeline_bar")
    if pipeline_chart:
        add(PageBreak())
        add(_hr(C["teal"]))
        add(Paragraph("Sales CRM — Value by Stage  (Lifetime, All Deals)", styles["SectionHead"]))
        add(_sp(2))
        add(_img_from_bytes(pipeline_chart, full_w))

    monthly_chart = chart_bytes.get("monthly_revenue")
    if monthly_chart:
        add(PageBreak())
        add(_hr(C["teal"]))
        add(Paragraph(f"Monthly Revenue — {year}  (Paid Deals Only)", styles["SectionHead"]))
        add(_sp(2))
        add(_img_from_bytes(monthly_chart, full_w))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return output_path
