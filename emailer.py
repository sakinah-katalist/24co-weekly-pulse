"""Send the Hire 24co Weekly Pulse report via Gmail SMTP — clean HTML table email."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from config import EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO, EMAIL_CC

REPORT_TITLE = "24co Weekly Pulse"

# Row highlight colours (light backgrounds, border accent)
ROW_YELLOW = "#FFFBCC"   # Tier 1
ROW_RED    = "#FDECEA"   # Hot lead
ROW_TEAL   = "#F0FAF9"   # Standard gov/govtech
ROW_WHITE  = "#FFFFFF"


def _row_bg(item: dict) -> str:
    if item.get("tier1"):
        return ROW_YELLOW
    if item.get("is_hot"):
        return ROW_RED
    return ROW_WHITE


def _tier_label(item: dict) -> str:
    if item.get("tier1"):
        return f"Tier 1 — {item['tier1']}"
    if item.get("is_hot"):
        return "HOT LEAD"
    return "Gov"


def build_email_html(
    leads: list[dict],
    sessions: list[dict],
    report_date,
    period_label: str,
) -> tuple[str, str]:
    """Returns (subject, html_body)."""
    subject = f"{REPORT_TITLE} — {period_label}"

    # ── Legend row — b. specific definitions ────────────────────────────────
    legend = f"""
    <tr>
      <td colspan="10" style="padding:8px 10px;background:#f5f5f5;
                              border-bottom:1px solid #ddd;">
        <table cellpadding="0" cellspacing="0" style="width:100%;font-size:10px;">
          <tr>
            <td style="padding:2px 6px;">
              <span style="background:#F5C800;padding:2px 7px;font-weight:bold;
                           color:#111;">■ YELLOW</span>
              &nbsp;<b>Tier 1 Ministry</b> — Top 8 federal: KDN, MINDEF, MOF, JPM, KD, MOE, MOH, MITI
            </td>
          </tr>
          <tr>
            <td style="padding:2px 6px;">
              <span style="background:#C0392B;padding:2px 7px;font-weight:bold;
                           color:#fff;">■ RED</span>
              &nbsp;<b>Hot Lead</b> — Status = [Training] Hot Lead or [Canva] Hot Lead in Notion
            </td>
          </tr>
          <tr>
            <td style="padding:2px 6px;">
              <span style="background:#1A7F7A;padding:2px 7px;font-weight:bold;
                           color:#fff;">■ TEAL</span>
              &nbsp;<b>Standard Gov / GovTech</b> — GLCs, statutory bodies, public agencies &amp; GovTech vendors
            </td>
          </tr>
          <tr>
            <td style="padding:4px 6px 2px;color:#777;font-size:9px;">
              <b>CRM Stages:</b>&nbsp;
              ✅ <b>Paid</b> = Invoice settled, full payment received &nbsp;|&nbsp;
              📁 <b>Closed</b> = Deal won &amp; completed, payment confirmed &nbsp;|&nbsp;
              📋 <b>Proposal/Quotation</b> = Quote sent, awaiting client decision
            </td>
          </tr>
        </table>
      </td>
    </tr>
    """

    # ── Leads table ───────────────────────────────────────────────────────────
    def _lead_rows(leads):
        if not leads:
            return '<tr><td colspan="4" style="padding:8px 10px;color:#777;font-style:italic;">No gov/govtech leads this week.</td></tr>'
        sorted_leads = sorted(
            leads,
            key=lambda x: (0 if x.get("tier1") else 1, 0 if x.get("is_hot") else 1),
        )
        html = ""
        for l in sorted_leads:
            bg      = _row_bg(l)
            tier    = _tier_label(l)
            enquiry = (l.get("enquiry") or l.get("status") or "—")[:120]
            contact = l.get("contact_name") or ""
            email   = l.get("contact_email") or ""
            contact_str = f"{contact} · {email}" if email else contact
            html += f"""
            <tr style="background:{bg};">
              <td style="padding:7px 10px;font-weight:600;font-size:12px;
                         border-bottom:1px solid #eee;vertical-align:top;">
                {l.get("org_name","—")}<br>
                <span style="font-weight:400;font-size:10px;color:#666;">{contact_str}</span>
              </td>
              <td style="padding:7px 10px;font-size:11px;color:#333;
                         border-bottom:1px solid #eee;vertical-align:top;white-space:nowrap;">
                {tier}
              </td>
              <td style="padding:7px 10px;font-size:11px;color:#555;
                         border-bottom:1px solid #eee;vertical-align:top;">
                {l.get("area") or "—"}
              </td>
              <td style="padding:7px 10px;font-size:11px;color:#333;
                         border-bottom:1px solid #eee;vertical-align:top;">
                {enquiry}
              </td>
            </tr>
            """
        return html

    leads_section = f"""
    <tr>
      <td colspan="10" style="padding:12px 10px 4px;font-size:13px;
                              font-weight:bold;color:#1A7F7A;border-bottom:2px solid #1A7F7A;">
        Gov / GovTech Leads &nbsp;<span style="font-weight:normal;font-size:11px;color:#888;">
        ({len(leads)} lead{'s' if len(leads) != 1 else ''})</span>
      </td>
    </tr>
    <tr style="background:#f0f0f0;">
      <th style="padding:6px 10px;text-align:left;font-size:10px;color:#444;border-bottom:1px solid #ddd;">Organisation</th>
      <th style="padding:6px 10px;text-align:left;font-size:10px;color:#444;border-bottom:1px solid #ddd;">Tier</th>
      <th style="padding:6px 10px;text-align:left;font-size:10px;color:#444;border-bottom:1px solid #ddd;">Area</th>
      <th style="padding:6px 10px;text-align:left;font-size:10px;color:#444;border-bottom:1px solid #ddd;">Enquiry</th>
    </tr>
    {_lead_rows(leads)}
    """

    # ── Sessions table ────────────────────────────────────────────────────────
    def _session_rows(sessions):
        if not sessions:
            return '<tr><td colspan="4" style="padding:8px 10px;color:#777;font-style:italic;">No gov sessions this week.</td></tr>'
        html = ""
        for s in sorted(sessions, key=lambda x: (0 if x.get("tier1") else 1)):
            bg   = _row_bg(s)
            tier = _tier_label(s)
            html += f"""
            <tr style="background:{bg};">
              <td style="padding:7px 10px;font-weight:600;font-size:12px;
                         border-bottom:1px solid #eee;vertical-align:top;">
                {s.get("org_name","—")}
              </td>
              <td style="padding:7px 10px;font-size:11px;color:#333;
                         border-bottom:1px solid #eee;vertical-align:top;white-space:nowrap;">
                {tier}
              </td>
              <td style="padding:7px 10px;font-size:11px;color:#333;
                         border-bottom:1px solid #eee;vertical-align:top;">
                {s.get("class_name","—")}
              </td>
              <td style="padding:7px 10px;font-size:11px;color:#555;
                         border-bottom:1px solid #eee;vertical-align:top;white-space:nowrap;">
                {s.get("date","—")}
              </td>
            </tr>
            """
        return html

    sessions_section = f"""
    <tr>
      <td colspan="10" style="padding:16px 10px 4px;font-size:13px;
                              font-weight:bold;color:#1A7F7A;border-bottom:2px solid #1A7F7A;">
        Past Gov Sessions &nbsp;<span style="font-weight:normal;font-size:11px;color:#888;">
        ({len(sessions)} session{'s' if len(sessions) != 1 else ''})</span>
      </td>
    </tr>
    <tr style="background:#f0f0f0;">
      <th style="padding:6px 10px;text-align:left;font-size:10px;color:#444;border-bottom:1px solid #ddd;">Organisation</th>
      <th style="padding:6px 10px;text-align:left;font-size:10px;color:#444;border-bottom:1px solid #ddd;">Tier</th>
      <th style="padding:6px 10px;text-align:left;font-size:10px;color:#444;border-bottom:1px solid #ddd;">Class / Training</th>
      <th style="padding:6px 10px;text-align:left;font-size:10px;color:#444;border-bottom:1px solid #ddd;">Date</th>
    </tr>
    {_session_rows(sessions)}
    """

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:20px;background:#f4f4f4;font-family:Arial,sans-serif;">

  <!-- Outer wrapper -->
  <table width="680" cellpadding="0" cellspacing="0"
         style="margin:0 auto;background:#fff;border:1px solid #ddd;border-radius:4px;">

    <!-- Header -->
    <tr>
      <td colspan="10"
          style="background:#0D3349;padding:16px 20px;">
        <p style="margin:0;font-size:10px;color:#aaa;text-transform:uppercase;
                  letter-spacing:.06em;">Katalist Venture — Weekly Intelligence</p>
        <h1 style="margin:4px 0 0;font-size:18px;color:#fff;font-weight:bold;">
          {REPORT_TITLE}
        </h1>
        <p style="margin:3px 0 0;font-size:12px;color:#ccc;">{period_label}</p>
      </td>
    </tr>

    <!-- Intro -->
    <tr>
      <td colspan="10" style="padding:12px 10px 4px;font-size:12px;color:#555;">
        Hi team — here's this week's gov &amp; GovTech activity. Full report in the PDF attachment.
      </td>
    </tr>

    <!-- Legend -->
    {legend}

    <!-- Leads -->
    {leads_section}

    <!-- Sessions -->
    {sessions_section}

    <!-- Footer -->
    <tr>
      <td colspan="10"
          style="padding:12px 10px;background:#f5f5f5;font-size:10px;color:#999;
                 text-align:center;border-top:1px solid #ddd;">
        {REPORT_TITLE} &nbsp;·&nbsp; {report_date.strftime('%d %b %Y')} &nbsp;·&nbsp;
        Full breakdown in attached PDF
      </td>
    </tr>

  </table>
</body>
</html>"""

    return subject, html


def send_report(
    subject: str,
    html_body: str,
    pdf_path: str,
    to_override: list[str] | None = None,
):
    """Send HTML email with PDF attachment. Pass to_override to limit recipients."""
    recipients = to_override if to_override is not None else EMAIL_TO

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_FROM
    msg["To"]      = ", ".join(recipients)
    if EMAIL_CC and to_override is None:
        msg["Cc"] = ", ".join(EMAIL_CC)

    plain = (
        f"Hi team,\n\n{REPORT_TITLE} — {subject}\n\n"
        "Full report is attached as a PDF.\n\n— Katalist Venture"
    )
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    pdf_part = MIMEBase("application", "pdf")
    pdf_part.set_payload(Path(pdf_path).read_bytes())
    encoders.encode_base64(pdf_part)
    pdf_part.add_header("Content-Disposition",
                        f'attachment; filename="{Path(pdf_path).name}"')

    outer = MIMEMultipart("mixed")
    outer["Subject"] = subject
    outer["From"]    = EMAIL_FROM
    outer["To"]      = ", ".join(recipients)
    if EMAIL_CC and to_override is None:
        outer["Cc"] = ", ".join(EMAIL_CC)
    outer.attach(msg)
    outer.attach(pdf_part)

    all_rcpt = recipients + (EMAIL_CC if EMAIL_CC and to_override is None else [])
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_FROM, EMAIL_PASSWORD)
        smtp.sendmail(EMAIL_FROM, all_rcpt, outer.as_bytes())

    print(f"✓ Email sent to: {', '.join(all_rcpt)}")
