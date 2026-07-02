"""
24co Weekly Pulse — PDF Report
Plain-language, narrative-first layout.
No jargon. No complex charts. Readable by anyone.
"""

import io
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from config import ORG_FULL_NAMES
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable, KeepTogether, PageBreak,
)

W, H   = A4
MARGIN = 18 * mm
REPORT_TITLE = "24co Weekly Pulse"
COMPANY      = "Katalist Venture"

# ── Colours ──────────────────────────────────────────────────────────────────
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
C["gold"] = C["yellow"];  C["gold_light"] = C["yellow_light"]

COLOR_MAP = {"gold": C["yellow"], "yellow": C["yellow"],
             "red": C["red"],     "teal":   C["teal"]}
LIGHT_MAP = {"gold": C["yellow_light"], "yellow": C["yellow_light"],
             "red": C["red_light"],     "teal":   C["teal_light"]}

# Plain-English translations for lead statuses
STATUS_PLAIN = {
    "[training] hot lead": "Very interested — follow up within 48 hours",
    "[canva] hot lead":    "Very interested in Canva — follow up soon",
    "new":                 "Just came in — not yet contacted",
    "contacted":           "We've reached out, waiting for their reply",
    "hot lead":            "Very interested — respond quickly",
    "warm":                "Showing interest — nurture this lead",
    "cold":                "Low activity — may need re-engagement",
    "lost":                "Did not proceed — closed",
    "won":                 "Successfully converted to a booking",
}

CRM_STAGES = ("paid", "closed", "proposal", "quotation", "almost")


def _expand_org(name: str) -> str:
    """
    Expand an org name to its full form.
    1. Exact match in ORG_FULL_NAMES.
    2. Prefix match (longest key first) for series entries like 'MSU - Siri 11 - Ali'.
    3. Return as-is if no match found.
    """
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


def _stage_ok(s):
    t = (s or "").lower()
    return any(k in t for k in CRM_STAGES)


def _is_revenue(s):
    t = (s or "").lower()
    return "paid" in t or "closed" in t


def _plain_status(status: str) -> str:
    return STATUS_PLAIN.get((status or "").lower(), status or "—")


def _session_type(s: dict) -> str:
    return "Public" if (s.get("signup") or "").strip() else "In-house"


def _pending_collection(deals, report_date) -> list:
    cutoff = report_date.strftime("%Y-%m-%d") if hasattr(report_date, "strftime") else str(report_date)
    return [d for d in deals
            if d.get("train_date") and d["train_date"] <= cutoff
            and not _is_revenue(d.get("stage", ""))]


def _revenue_last_7_days(deals, report_date) -> float:
    if not hasattr(report_date, "strftime"):
        return 0.0
    cutoff = (report_date - timedelta(days=7)).strftime("%Y-%m-%d")
    today  = report_date.strftime("%Y-%m-%d")
    return sum(d.get("deal_value", 0) or 0 for d in deals
               if _is_revenue(d.get("stage", ""))
               and cutoff <= (d.get("payment_received_date") or d.get("close_date") or "") <= today)


def _hex(c) -> str:
    raw = c.hexval()
    raw = raw[2:] if raw.startswith(("0x", "0X")) else raw.lstrip("#")
    return raw.upper().zfill(6)


def _img_from_bytes(data: bytes, w_mm: float) -> Image:
    img = Image(io.BytesIO(data), width=w_mm * mm)
    img.hAlign = "CENTER"
    return img


# ── Styles ────────────────────────────────────────────────────────────────────
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
        "CardOrg":      _s("CardOrg",      10, "Helvetica-Bold",    C["dark"]),
        "CardDesc":     _s("CardDesc",      7.5,"Helvetica-Oblique",C["mid"]),
        "CardLabel":    _s("CardLabel",     7, "Helvetica-Bold",    C["muted"]),
        "CardValue":    _s("CardValue",     8.5,"Helvetica",        C["dark"]),
        "TableHead":    _s("TableHead",     8, "Helvetica-Bold",    C["white"],   TA_LEFT),
        "TableCell":    _s("TableCell",     8, "Helvetica",         C["dark"]),
        "SmallMuted":   _s("SmallMuted",    7, "Helvetica",         C["muted"]),
        "Highlight":    _s("Highlight",     9, "Helvetica-Bold",    C["teal"]),
        "WarnHead":     _s("WarnHead",      9, "Helvetica-Bold",    C["red"]),
    }


# ── Helper: coloured highlight box ───────────────────────────────────────────
def _callout(text: str, bg: object, border: object, styles, key="Narrative") -> Table:
    """Single-cell coloured box with text inside."""
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


# ── Lead card — plain English labels ─────────────────────────────────────────
def _lead_card(lead: dict, styles) -> Table:
    color_key = lead.get("color", "teal")
    accent    = COLOR_MAP.get(color_key, C["teal"])
    bg        = LIGHT_MAP.get(color_key, C["teal_light"])
    tier_hex  = _hex(C["yellow"])
    red_hex   = _hex(C["red"])

    hot_tag  = f' <font color="#{red_hex}"><b>[ HOT — respond quickly ]</b></font>' \
               if lead.get("is_hot") and not lead.get("tier1") else ""
    tier_tag = f' <font color="#{tier_hex}"><b>[ Tier 1 — {lead["tier1"]} ]</b></font>' \
               if lead.get("tier1") else ""

    short   = lead['org_name']
    full    = _expand_org(short)
    # Only show the short-form in grey if it's genuinely shorter (an abbreviation)
    name_str = (f"<b>{full}</b>  <font size='8' color='#888888'>({short})</font>"
                if full != short and len(short) < len(full)
                else f"<b>{full}</b>")
    header = Paragraph(f"{name_str}{tier_tag}{hot_tag}", styles["CardOrg"])

    rows = []
    if lead.get("description"):
        rows.append([Paragraph("About this org", styles["CardLabel"]),
                     Paragraph(lead["description"], styles["CardDesc"])])

    def row(lbl, val):
        if not val: return None
        return [Paragraph(lbl, styles["CardLabel"]),
                Paragraph(str(val), styles["CardValue"])]

    # Plain English labels
    status_plain = _plain_status(lead.get("status",""))
    for r in [
        row("Organisation type",  lead.get("org_type")),
        row("Contact person",     lead.get("contact_name")),
        row("Email",              lead.get("contact_email")),
        row("Phone",              lead.get("contact_phone")),
        row("How they found us",  lead.get("lead_source")),
        row("Current status",     status_plain),
        row("Enquiry received",   lead.get("date")),
        row("What they need",     lead.get("enquiry")),
        row("Training topic",     lead.get("area")),
        row("Internal notes",     lead.get("notes")),
    ]:
        if r: rows.append(r)

    cw2 = W - 2*MARGIN - 34*mm
    detail = Table(rows, colWidths=[26*mm, cw2])
    detail.setStyle(TableStyle([
        ("VALIGN",        (0,0),(-1,-1),"TOP"),
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
    ]))

    body = Table([[header],[detail]], colWidths=[W-2*MARGIN-6*mm])
    body.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), bg),
        ("TOPPADDING", (0,0),(-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING", (0,0),(-1,-1), 9),
        ("RIGHTPADDING",(0,0),(-1,-1), 9),
    ]))

    bar = Table([[""]], colWidths=[4*mm])
    bar.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),accent)]))

    card = Table([[bar, body]], colWidths=[4*mm, W-2*MARGIN-4*mm])
    card.setStyle(TableStyle([
        ("VALIGN",        (0,0),(-1,-1),"TOP"),
        ("TOPPADDING",    (0,0),(-1,-1), 0),
        ("BOTTOMPADDING", (0,0),(-1,-1), 0),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
        ("BOX",           (0,0),(-1,-1), 0.5, C["border"]),
    ]))
    return card


# ── Session card — plain English labels ──────────────────────────────────────
def _session_card(s: dict, styles) -> Table:
    color_key = s.get("color", "teal")
    accent    = COLOR_MAP.get(color_key, C["teal"])
    bg        = LIGHT_MAP.get(color_key, C["teal_light"])
    tier_hex  = _hex(C["yellow"])
    stype     = _session_type(s)

    tier_tag  = f' <font color="#{tier_hex}"><b>[ Tier 1 — {s["tier1"]} ]</b></font>' \
                if s.get("tier1") else ""
    type_tag  = " [ Public class ]" if stype == "Public" else " [ In-house ]"

    short_s  = s['org_name']
    full_s   = _expand_org(short_s)
    name_str_s = (f"<b>{full_s}</b>  <font size='8' color='#888888'>({short_s})</font>"
                  if full_s != short_s and len(short_s) < len(full_s)
                  else f"<b>{full_s}</b>")
    header = Paragraph(f"{name_str_s}{tier_tag} <i>{type_tag}</i>",
                       styles["CardOrg"])

    rows = []
    if s.get("description"):
        rows.append([Paragraph("About this org", styles["CardLabel"]),
                     Paragraph(s["description"], styles["CardDesc"])])

    def row(lbl, val):
        if not val: return None
        return [Paragraph(lbl, styles["CardLabel"]),
                Paragraph(str(val), styles["CardValue"])]

    for r in [
        row("Programme",     s.get("class_name")),
        row("Date held",     s.get("date")),
        row("Session type",  f"{stype} — {'Anyone can join' if stype == 'Public' else 'Booked exclusively for this organisation'}"),
    ]:
        if r: rows.append(r)

    if not rows:
        rows.append([Paragraph("Date", styles["CardLabel"]),
                     Paragraph(s.get("date",""), styles["CardValue"])])

    cw2 = W - 2*MARGIN - 34*mm
    detail = Table(rows, colWidths=[26*mm, cw2])
    detail.setStyle(TableStyle([
        ("VALIGN",        (0,0),(-1,-1),"TOP"),
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
    ]))

    body = Table([[header],[detail]], colWidths=[W-2*MARGIN-6*mm])
    body.setStyle(TableStyle([
        ("BACKGROUND", (0,0),(-1,-1), bg),
        ("TOPPADDING", (0,0),(-1,-1), 6),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
        ("LEFTPADDING", (0,0),(-1,-1), 9),
        ("RIGHTPADDING",(0,0),(-1,-1), 9),
    ]))

    bar = Table([[""]], colWidths=[4*mm])
    bar.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),accent)]))

    card = Table([[bar, body]], colWidths=[4*mm, W-2*MARGIN-4*mm])
    card.setStyle(TableStyle([
        ("VALIGN",        (0,0),(-1,-1),"TOP"),
        ("TOPPADDING",    (0,0),(-1,-1), 0),
        ("BOTTOMPADDING", (0,0),(-1,-1), 0),
        ("LEFTPADDING",   (0,0),(-1,-1), 0),
        ("RIGHTPADDING",  (0,0),(-1,-1), 0),
        ("BOX",           (0,0),(-1,-1), 0.5, C["border"]),
    ]))
    return card


# ── Simple deal table ─────────────────────────────────────────────────────────
def _deal_table(deals: list, styles) -> Table:
    hdr = [Paragraph(h, styles["TableHead"]) for h in
           ["Organisation", "Status", "Amount", "Date Paid/Closed", "What we delivered"]]
    cw  = [(W-2*MARGIN)*f for f in [0.26, 0.15, 0.14, 0.16, 0.29]]
    rows = []
    for d in sorted(deals, key=lambda x: -(x.get("deal_value") or 0)):
        stg  = d.get("stage","—")
        icon = "✅ Paid" if "paid" in stg.lower() else ("📁 Closed" if "closed" in stg.lower() else f"📋 {stg}")
        rows.append([
            Paragraph(_expand_org(d.get("org_name","")), styles["TableCell"]),
            Paragraph(icon,                  styles["TableCell"]),
            Paragraph(f"RM {d['deal_value']:,.0f}" if d.get("deal_value") else "—",
                      styles["TableCell"]),
            Paragraph(d.get("payment_received_date") or d.get("close_date") or "—", styles["TableCell"]),
            Paragraph(d.get("course",""),    styles["TableCell"]),
        ])

    if not rows:
        return Paragraph("No deals to show.", styles["SmallMuted"])

    t = Table([hdr]+rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  C["header_bg"]),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1), 8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [C["white"], C["light"]]),
        ("GRID",          (0,0),(-1,-1), 0.35, C["border"]),
        ("TOPPADDING",    (0,0),(-1,-1), 4),
        ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ("LEFTPADDING",   (0,0),(-1,-1), 5),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ]))
    return t


# ── Week-on-week table ────────────────────────────────────────────────────────
def _wow_table(revenue_history: list, styles) -> Table:
    hdr = [Paragraph(h, styles["TableHead"]) for h in
           ["Week", "Revenue Collected", "Compared to Previous Week"]]
    cw  = [(W-2*MARGIN)*f for f in [0.22, 0.28, 0.50]]
    rows = []
    for i, w in enumerate(revenue_history):
        curr = w["total_revenue"]
        if i > 0:
            prev = revenue_history[i-1]["total_revenue"]
            diff = curr - prev
            if prev > 0:
                pct   = diff / prev * 100
                arrow = "▲" if diff >= 0 else "▼"
                clr   = "#27AE60" if diff >= 0 else "#C0392B"
                delta = Paragraph(
                    f'<font color="{clr}"><b>{arrow} RM {abs(diff):,.0f} ({abs(pct):.0f}%)</b></font>',
                    styles["TableCell"])
            elif diff > 0:
                delta = Paragraph('<font color="#27AE60"><b>▲ New revenue this week</b></font>',
                                  styles["TableCell"])
            else:
                delta = Paragraph("— No change", styles["TableCell"])
        else:
            delta = Paragraph("—", styles["TableCell"])

        rows.append([
            Paragraph(w["week_label"], styles["TableCell"]),
            Paragraph(f"RM {curr:,.0f}", styles["TableCell"]),
            delta,
        ])

    t = Table([hdr]+rows, colWidths=cw)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0),  C["header_bg"]),
        ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0),(-1,-1), 8),
        ("ROWBACKGROUNDS",(0,1),(-1,-2), [C["white"], C["light"]]),
        ("BACKGROUND",    (0,-1),(-1,-1),C["yellow_light"]),
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

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
    )

    def on_page(canvas, doc):
        canvas.saveState()
        # Header strip
        canvas.setFillColor(C["header_bg"])
        canvas.rect(0, H-20*mm, W, 20*mm, fill=1, stroke=0)
        canvas.setFillColor(C["white"])
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(MARGIN, H-12*mm, REPORT_TITLE)
        canvas.setFont("Helvetica", 7)
        canvas.drawRightString(W-MARGIN, H-11*mm,
                               f"{COMPANY}  ·  {report_date.strftime('%d %b %Y')}")
        canvas.drawRightString(W-MARGIN, H-16*mm, f"Period: {period_label}")
        # Footer
        canvas.setFillColor(C["muted"])
        canvas.setFont("Helvetica", 6.5)
        canvas.drawCentredString(W/2, 9*mm,
            f"Generated {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')}"
            f"  ·  Page {doc.page}  ·  Confidential — Katalist Venture")
        canvas.restoreState()

    story  = []
    add    = story.append
    sp     = lambda n=4: Spacer(1, n*mm)
    hr     = lambda c=C["border"]: HRFlowable(width="100%", thickness=0.8,
                                              color=c, spaceAfter=3)

    add(sp(10))

    # ── COLOUR KEY — plain English ────────────────────────────────────────────
    key_rows = [[
        Paragraph(f'<font color="#{_hex(C["yellow"])}"><b>■  Yellow stripe</b></font>  — '
                  f'Top-level Malaysian federal ministry (e.g. Finance, Defence, Education)',
                  styles["SmallMuted"]),
    ],[
        Paragraph(f'<font color="#{_hex(C["red"])}"><b>■  Red stripe</b></font>  — '
                  f'Hot lead — expressed strong interest, needs a fast response',
                  styles["SmallMuted"]),
    ],[
        Paragraph(f'<font color="#{_hex(C["teal"])}"><b>■  Teal stripe</b></font>  — '
                  f'Government agency, GLC, statutory body, or GovTech vendor',
                  styles["SmallMuted"]),
    ]]
    key_tbl = Table(key_rows, colWidths=[W-2*MARGIN])
    key_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C["light"]),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("BOX",           (0,0),(-1,-1), 0.5, C["border"]),
    ]))
    add(key_tbl)
    add(sp(5))

    # ── WEEK AT A GLANCE — plain text summary ────────────────────────────────
    paid_deals     = [d for d in crm_deals if _is_revenue(d.get("stage",""))]
    pipeline_deals = [d for d in crm_deals if _stage_ok(d.get("stage",""))
                      and not _is_revenue(d.get("stage",""))]
    paid_total     = sum(d.get("deal_value",0) or 0 for d in paid_deals)
    pipe_total     = sum(d.get("deal_value",0) or 0 for d in pipeline_deals)
    rev_7d         = _revenue_last_7_days(crm_deals, report_date)
    tier1_count    = sum(1 for x in leads+sessions if x.get("tier1"))
    pub_sess       = sum(1 for s in sessions if _session_type(s) == "Public")
    inh_sess       = len(sessions) - pub_sess
    pending        = _pending_collection(crm_deals, report_date)

    hot_names  = [_expand_org(l["org_name"]) for l in leads if l.get("is_hot")]
    new_names  = [_expand_org(l["org_name"]) for l in leads if (l.get("status") or "").lower() == "new"]

    # Build the narrative paragraph
    lines = []
    lines.append(
        f"This week ({period_label}), we received <b>{len(leads)}</b> government "
        f"{'enquiry' if len(leads)==1 else 'enquiries'} and delivered "
        f"<b>{len(sessions)}</b> training session{'s' if len(sessions)!=1 else ''} "
        f"for government organisations."
    )
    if hot_names:
        lines.append(
            f"<b>{', '.join(hot_names)}</b> "
            f"{'is' if len(hot_names)==1 else 'are'} a hot lead — "
            f"{'they need' if len(hot_names)==1 else 'they need'} a response as soon as possible."
        )
    if tier1_count:
        lines.append(
            f"We have <b>{tier1_count}</b> match{'es' if tier1_count!=1 else ''} "
            f"with top-level federal ministries this week — these are our highest-priority accounts."
        )
    if rev_7d > 0:
        lines.append(f"<b>RM {rev_7d:,.0f}</b> was collected in the last 7 days.")
    else:
        lines.append("No new payments were collected in the last 7 days.")
    if paid_total:
        lines.append(
            f"In total, we have collected <b>RM {paid_total:,.0f}</b> from "
            f"{len(paid_deals)} paid government deal{'s' if len(paid_deals)!=1 else ''} this year."
        )
    if pipe_total:
        lines.append(
            f"We also have <b>RM {pipe_total:,.0f}</b> in active quotes sent to clients "
            f"({len(pipeline_deals)} deal{'s' if len(pipeline_deals)!=1 else ''}) — "
            f"waiting for their decision."
        )
    if pending:
        lines.append(
            f"⚠ <b>{len(pending)} training{'s' if len(pending)!=1 else ''} already delivered "
            f"but payment not yet received</b> — "
            f"RM {sum(d.get('deal_value',0) or 0 for d in pending):,.0f} outstanding."
        )

    summary_text = "  ".join(lines)
    add(_callout(summary_text, C["teal_light"], C["teal"], styles, "Narrative"))
    add(sp(6))

    # ── REVENUE TREND LINE CHART ──────────────────────────────────────────────
    # Keep heading + sub + chart together; table gets its own KeepTogether
    rev_chart = chart_bytes.get("revenue_line") or chart_bytes.get("revenue")
    if rev_chart and revenue_history:
        add(KeepTogether([
            hr(C["teal"]),
            Paragraph("Revenue Collected — Week by Week", styles["SectionHead"]),
            Paragraph(
                "Each dot shows how much money was collected from government training deals "
                "in that week. Only payments that have been fully received are counted here.",
                styles["SectionSub"]),
            sp(2),
            _img_from_bytes(rev_chart, full_w * 0.70),
        ]))
        add(sp(3))
        # WoW table kept together with its label
        add(KeepTogether([
            Paragraph("Week-by-week comparison:", styles["SmallMuted"]),
            sp(1),
            _wow_table(revenue_history, styles),
        ]))
        add(sp(6))

    # ── SECTION 1 — LEADS ────────────────────────────────────────────────────
    # Section header + subtitle kept together — never orphaned at page bottom
    counts = Counter(l.get("status") or "Unknown" for l in leads)
    total  = sum(counts.values()) if leads else 1
    status_parts = ",  ".join(
        f"{_plain_status(s)}: <b>{n}</b> ({n*100//total}%)"
        for s, n in sorted(counts.items(), key=lambda x: -x[1])
    ) if leads else ""

    add(KeepTogether([
        hr(C["teal"]),
        Paragraph(
            f"Section 1  —  Government Enquiries This Week  ({len(leads)})",
            styles["SectionHead"]),
        Paragraph("Source: Marketing Leads Database (Notion)", styles["SectionSub"]),
        sp(3),
        _callout(
            f"Status summary this week — {status_parts}" if leads
            else "No government enquiries were received this week.",
            C["light"], C["border"], styles, "SmallMuted"
        ),
    ]))
    add(sp(3))

    if leads:
        for lead in sorted(leads, key=lambda l: (
                0 if l.get("tier1") else 1, 0 if l.get("is_hot") else 1)):
            add(KeepTogether([_lead_card(lead, styles), sp(3)]))

    add(sp(5))

    # ── SECTION 2 — SESSIONS ─────────────────────────────────────────────────
    sess_summary = (
        f"We ran <b>{len(sessions)}</b> government training session"
        f"{'s' if len(sessions)!=1 else ''} this week — "
        f"<b>{inh_sess}</b> in-house (private, booked for one organisation) "
        f"and <b>{pub_sess}</b> public (open to all participants)."
    ) if sessions else "No training sessions were recorded this week."

    add(KeepTogether([
        hr(C["teal"]),
        Paragraph(
            f"Section 2  —  Training Sessions This Week  ({len(sessions)})",
            styles["SectionHead"]),
        Paragraph("Source: Past Classes Database (Notion)", styles["SectionSub"]),
        sp(3),
        _callout(sess_summary, C["light"], C["border"], styles),
    ]))
    add(sp(3))

    if sessions:
        for s in sorted(sessions, key=lambda s: (0 if s.get("tier1") else 1)):
            add(KeepTogether([_session_card(s, styles), sp(3)]))

    add(sp(5))

    # ── SECTION 3 — SALES & REVENUE (always starts on a fresh page) ──────────
    add(PageBreak())
    add(sp(10))

    # Revenue narrative — kept together with section header
    rev_callout = _callout("No paid deals recorded yet.", C["light"], C["border"], styles)
    if paid_deals:
        rev_lines = [
            f"We have collected a total of <b>RM {paid_total:,.0f}</b> from "
            f"{len(paid_deals)} fully paid government deal{'s' if len(paid_deals)!=1 else ''}.  "
        ]
        for d in sorted(paid_deals, key=lambda x: -(x.get("deal_value") or 0)):
            rev_lines.append(
                f"• <b>{_expand_org(d['org_name'])}</b> — RM {d.get('deal_value',0):,.0f} "
                f"({'received ' + (d.get('payment_received_date') or d['close_date']) if (d.get('payment_received_date') or d.get('close_date')) else 'confirmed'})"
            )
        rev_callout = _callout("  ".join(rev_lines), C["green_light"], C["green"], styles)

    add(KeepTogether([
        hr(C["yellow"]),
        Paragraph("Section 3  —  Sales & Revenue", styles["SectionHead"]),
        Paragraph(
            "Source: Sales CRM Database (Notion)  ·  Only Paid and Closed deals "
            "counted as revenue",
            styles["SectionSub"]),
        sp(4),
        rev_callout,
    ]))

    # Pipeline narrative — kept together
    if pipeline_deals:
        pipe_lines = [
            f"We also have <b>RM {pipe_total:,.0f}</b> in active quotes — "
            f"{len(pipeline_deals)} deal{'s' if len(pipeline_deals)!=1 else ''} "
            f"where we have sent a proposal and are waiting for the client's decision.  "
        ]
        for d in sorted(pipeline_deals, key=lambda x: -(x.get("deal_value") or 0)):
            pipe_lines.append(
                f"• <b>{_expand_org(d['org_name'])}</b> — RM {d.get('deal_value',0):,.0f}"
            )
        add(sp(4))
        add(KeepTogether([
            _callout("  ".join(pipe_lines), C["yellow_light"], C["yellow"], styles),
        ]))

    # Full deals table — heading never separated from the table itself
    qualifying = [d for d in crm_deals if _stage_ok(d.get("stage",""))]
    if qualifying:
        add(sp(4))
        add(KeepTogether([
            Paragraph("All active deals (Paid, Closed & Proposals):", styles["Highlight"]),
            sp(2),
            _deal_table(qualifying, styles),
        ]))

    # Pending collection — entire block kept on one page if it fits
    if pending:
        total_out = sum(d.get("deal_value",0) or 0 for d in pending)
        add(KeepTogether([
            sp(5),
            hr(C["red"]),
            Paragraph(
                f"⚠  Awaiting Payment — {len(pending)} deal(s) outstanding",
                styles["WarnHead"]),
            Paragraph(
                "These trainings have already been delivered to the client, "
                "but we have not yet received payment. Follow up to collect.",
                styles["SectionSub"]),
            sp(3),
            _callout(
                f"Total amount still owed: <b>RM {total_out:,.0f}</b>",
                C["red_light"], C["red"], styles
            ),
            sp(2),
            _deal_table(pending, styles),
        ]))

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return output_path
