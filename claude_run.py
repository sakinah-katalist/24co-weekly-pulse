#!/usr/bin/env python3
"""
On-demand runner — called by Claude each Monday.
Reads data from a JSON file (written by Claude from live Notion MCP fetch),
generates the PDF, and opens it.

Usage: python3 claude_run.py [optional/path/to/data.json]
"""

import json, sys, subprocess
from datetime import datetime, timezone
from pathlib import Path
from charts import revenue_line_chart
from pdf_report import build_pdf

DEFAULT_DATA = Path(__file__).parent / "data" / "report.json"


def main():
    data_file = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT_DATA)
    with open(data_file) as f:
        d = json.load(f)

    report_date  = datetime.fromisoformat(d["report_date"])
    period_label = d["period_label"]
    leads        = d["leads"]
    sessions     = d["sessions"]
    crm_deals    = d["crm_deals"]
    revenue      = d["revenue_history"]

    print(f"📊 Building report for {period_label}…")
    print(f"   {len(leads)} gov lead(s) · {len(sessions)} session(s) · {len(crm_deals)} CRM deal(s)")

    chart_bytes = {
        "revenue_line": revenue_line_chart(revenue) if revenue else None,
    }

    filename    = f"24co_WeeklyPulse_{report_date.strftime('%Y-%m-%d')}.pdf"
    output_path = str(Path.home() / "Desktop" / filename)

    build_pdf(
        leads=leads, sessions=sessions, crm_deals=crm_deals,
        revenue_history=revenue, report_date=report_date,
        period_label=period_label, chart_bytes=chart_bytes,
        output_path=output_path,
    )

    size_kb = Path(output_path).stat().st_size // 1024
    print(f"✅ PDF saved → {output_path}  ({size_kb} KB)")
    subprocess.run(["open", output_path])
    return output_path


if __name__ == "__main__":
    main()
