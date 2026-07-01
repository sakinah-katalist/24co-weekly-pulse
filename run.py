#!/usr/bin/env python3
"""
Weekly Gov Leads Monitor — main runner.

Usage:
    python run.py              # Full run: fetch, generate PDF, send email
    python run.py --pdf-only   # Generate PDF locally, skip email
    python run.py --dry-run    # Print what would be sent, no PDF/email
"""

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from notion_fetcher import fetch_leads, fetch_sessions, fetch_crm_all, fetch_weekly_revenue_history
from charts import revenue_trend_chart, lead_status_donut, tier_breakdown_bar, crm_pipeline_bar
from pdf_report import build_pdf
from emailer import send_report, build_email_body
from config import REPORT_OUTPUT_DIR


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-only", action="store_true", help="Generate PDF but skip email")
    parser.add_argument("--dry-run",  action="store_true", help="Print summary only, no PDF/email")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)

    # Build period label: Mon DD Mon – Sun DD Mon YYYY
    from notion_fetcher import _week_range
    start, end = _week_range(0)
    period_label = f"{start.strftime('%-d %b')} – {end.strftime('%-d %b %Y')}"

    print(f"🔍 Fetching Notion data for {period_label}…")

    leads    = fetch_leads(weeks_ago=0)
    sessions = fetch_sessions(weeks_ago=0)
    crm_all  = fetch_crm_all()
    revenue  = fetch_weekly_revenue_history()

    print(f"   Found {len(leads)} gov lead(s), {len(sessions)} session(s), {len(crm_all)} CRM deal(s)")

    if args.dry_run:
        subject, body = build_email_body(leads, sessions, now, period_label)
        print(f"\n─── EMAIL SUBJECT ───\n{subject}")
        print(f"\n─── EMAIL BODY ───\n{body}")
        print("\n✓ Dry run complete — no PDF or email sent.")
        return

    print("📊 Generating charts…")
    chart_bytes = {
        "revenue":  revenue_trend_chart(revenue) if revenue else None,
        "donut":    lead_status_donut(leads)  if leads    else None,
        "tier":     tier_breakdown_bar(leads, sessions),
        "pipeline": crm_pipeline_bar(crm_all) if crm_all else None,
    }

    filename   = f"GovLeads_{now.strftime('%Y-%m-%d')}.pdf"
    output_dir = Path(REPORT_OUTPUT_DIR).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(output_dir / filename)

    print(f"📄 Building PDF → {output_path}")
    build_pdf(
        leads=leads,
        sessions=sessions,
        crm_deals=crm_all,
        revenue_history=revenue,
        report_date=now,
        period_label=period_label,
        chart_bytes=chart_bytes,
        output_path=output_path,
    )
    print(f"   ✓ PDF saved ({Path(output_path).stat().st_size // 1024} KB)")

    if args.pdf_only:
        print("✓ PDF-only mode — skipping email.")
        return

    subject, body = build_email_body(leads, sessions, now, period_label)
    print(f"📧 Sending email: {subject}")
    send_report(subject=subject, body_text=body, pdf_path=output_path)
    print("✓ Done.")


if __name__ == "__main__":
    main()
