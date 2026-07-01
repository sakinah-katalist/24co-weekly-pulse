#!/usr/bin/env python3
"""
Demo run — generates this week's PDF using data fetched live from Notion
via Claude's MCP connection. No Notion API token required for this mode.

For the automated weekly scheduler, use run.py (requires NOTION_TOKEN in config.py).
"""

from datetime import datetime, timezone
from pathlib import Path
from charts import revenue_trend_chart, lead_status_donut, tier_breakdown_bar, crm_pipeline_bar
from pdf_report import build_pdf

# ── Week: 19 May – 25 May 2026 ───────────────────────────────────────────────
REPORT_DATE  = datetime(2026, 5, 25, tzinfo=timezone.utc)
PERIOD_LABEL = "19 May – 25 May 2026"

# ── Gov Leads — Marketing Leads DB (fetched via Claude MCP) ─────────────────
LEADS = [
    {
        "contact_name":  "Ayesha",
        "org_name":      "UEM Edgenta (Edgenta Academy Sdn Bhd)",
        "org_type":      "GLC — Government-Linked Company (UEM Group / Khazanah Nasional)",
        "contact_email": "ayesha@edgenta.com",
        "contact_phone": "019-609 2505",
        "lead_source":   "Contact Form",
        "status":        "[Training] Hot Lead",
        "date":          "2026-05-20",
        "enquiry":       "AI training programme for July 2026 — course outlines, trainer profiles, HRD Corp claimability, and availability.",
        "area":          "Generative AI & Automation",
        "notes":         "Synced to CRM. Exploring providers for upcoming AI programmes.",
        "is_hot":        True,
        "tier1":         None,
        "color":         "red",
        "notion_url":    "https://www.notion.so/366b1ded82ca81f6bee7eab157c68ab2",
    },
    {
        "contact_name":  "Haslinda",
        "org_name":      "Prasarana Malaysia Berhad",
        "org_type":      "Government Statutory Body — Public Transport",
        "contact_email": "linda.rosli@prasarana.com.my",
        "contact_phone": "017-306 4225",
        "lead_source":   "Contact Form",
        "status":        "New",
        "date":          "2026-05-22",
        "enquiry":       "Canva Design Masterclass — in-house, 25 pax, at Prasarana premise. Proposed June/July 2026.",
        "area":          "Designing with Canva",
        "notes":         "Requested proposal & quotation.",
        "is_hot":        False,
        "tier1":         None,
        "color":         "teal",
        "notion_url":    "https://www.notion.so/368b1ded82ca8134aab4c79a4de8ce16",
    },
    {
        "contact_name":  "Toby",
        "org_name":      "Cloud Mile Sdn Bhd",
        "org_type":      "GovTech Vendor — IT systems integrator serving GLC clients",
        "contact_email": "toby.lee@mile.cloud",
        "contact_phone": "019-976 2443",
        "lead_source":   "Contact Form",
        "status":        "Contacted",
        "date":          "2026-05-19",
        "enquiry":       "Collaboration — requesting Ali Reza Azmi to provide training to their GLC customer's management team.",
        "area":          "Generative AI",
        "notes":         "Referred via connections. Vendor acting on behalf of GLC end-client.",
        "is_hot":        False,
        "tier1":         None,
        "color":         "teal",
        "notion_url":    "https://www.notion.so/365b1ded82ca8173b646d1ba8544e410",
    },
]

# ── Gov Sessions — Past Classes DB (fetched via Claude MCP) ──────────────────
SESSIONS = [
    {
        "org_name":   "JPSPN",
        "class_name": "Gen AI Essentials: Daripada Kemahiran kepada Penyelesaian Praktikal",
        "date":       "2026-05-25 – 2026-05-26",
        "feedback":   "https://docs.google.com/spreadsheets/d/1v67xrRZJkJwj00AhO7e7E681laJKV-mJSkz_iozvE1o",
        "signup":     "",
        "tier1":      None,
        "color":      "teal",
        "notion_url": "https://www.notion.so/36ab1ded82ca8045befdd10d58b396f7",
    },
    {
        "org_name":   "Public Service Chinese Community (PSCC)",
        "class_name": "Generative AI at Work: From Prompting to Automation",
        "date":       "2026-05-23",
        "feedback":   "https://docs.google.com/spreadsheets/d/1OqjgWes_ENy3pfU9plkv-E2JkGdeUQsPjNiWZ8FNsVg",
        "signup":     "https://docs.google.com/spreadsheets/d/1O0Ay5u4o4eccpwqolCBUarvAeBG6Qo960DZH1DvDGtM",
        "tier1":      None,
        "color":      "teal",
        "notion_url": "https://www.notion.so/35db1ded82ca804a9298e54b44aeb2da",
    },
]

# ── Sales CRM — all gov-related deals (fetched via Claude MCP) ───────────────
CRM_DEALS = [
    {
        "org_name":    "UiTM Arshad Ayub Graduate Business School — Penang",
        "deal_value":  12960.0,
        "stage":       "Paid",
        "close_date":  "2025-07-25",
        "train_date":  "2025-06-23",
        "course":      "AI for Public Service Efficiency – The NextGen Gov: AI-Driven Public Service Revolution",
        "contact":     "Pn Zurina",
        "pax":         None,
        "gross_profit": 0,
        "notion_url":  "https://www.notion.so/196b1ded82ca800d9d9bee13d170e93d",
    },
    {
        "org_name":    "Public Service Chinese Community (PSCC) Malaysia",
        "deal_value":  10800.0,
        "stage":       "Paid",
        "close_date":  "2025-04-15",
        "train_date":  "2025-05-15",
        "course":      "Generative AI Fundamentals & Prompting Skills",
        "contact":     "Ms Lai / Mr Kee",
        "pax":         None,
        "gross_profit": 0,
        "notion_url":  "https://www.notion.so/174b1ded82ca80fcbe26ffc7e6a1755b",
    },
    {
        "org_name":    "Perbadanan SM-WEZ",
        "deal_value":  2495.0,
        "stage":       "Proposal / Quotation 👀",
        "close_date":  "",
        "train_date":  "2026-06-22",
        "course":      "Public class 1 day — 5 pax",
        "contact":     "ain.khalib@melaka.gov.my",
        "pax":         5,
        "gross_profit": 0,
        "notion_url":  "https://www.notion.so/367b1ded82ca8188a91ef893b647f02d",
    },
]

# ── Revenue history — last 5 weeks (based on CRM "Money Received on") ────────
# Computed from CRM data: RM 10,800 received Apr 15 2025, RM 12,960 received Jul 25 2025
REVENUE_HISTORY = [
    {"week_label": "Wk 21 Apr", "monday_date": "2025-04-21", "total_revenue": 0},
    {"week_label": "Wk 28 Apr", "monday_date": "2025-04-28", "total_revenue": 10800},
    {"week_label": "Wk 5 May",  "monday_date": "2025-05-05", "total_revenue": 0},
    {"week_label": "Wk 12 May", "monday_date": "2025-05-12", "total_revenue": 0},
    {"week_label": "This week", "monday_date": "2026-05-19", "total_revenue": 0},
]


def main():
    print("📊 Generating charts…")
    chart_bytes = {
        "revenue":  revenue_trend_chart(REVENUE_HISTORY),
        "donut":    lead_status_donut(LEADS),
        "tier":     tier_breakdown_bar(LEADS, SESSIONS),
        "pipeline": crm_pipeline_bar(CRM_DEALS),
    }

    output_path = str(Path.home() / "Desktop" / f"GovLeads_{REPORT_DATE.strftime('%Y-%m-%d')}.pdf")

    print(f"📄 Building PDF → {output_path}")
    build_pdf(
        leads=LEADS,
        sessions=SESSIONS,
        crm_deals=CRM_DEALS,
        revenue_history=REVENUE_HISTORY,
        report_date=REPORT_DATE,
        period_label=PERIOD_LABEL,
        chart_bytes=chart_bytes,
        output_path=output_path,
    )
    size_kb = Path(output_path).stat().st_size // 1024
    print(f"✅ PDF saved — {size_kb} KB")
    print(f"   Opening: {output_path}")

    import subprocess
    subprocess.run(["open", output_path])


if __name__ == "__main__":
    main()
