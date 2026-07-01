"""Fetch Marketing Leads, Past Classes, and Sales CRM from Notion."""

from datetime import datetime, timedelta, timezone
from notion_client import Client
from config import (
    NOTION_TOKEN,
    MARKETING_LEADS_DB_ID, PAST_CLASSES_DB_ID, SALES_CRM_DB_ID,
    LEADS_FIELDS, CLASSES_FIELDS, CRM_FIELDS,
    WEEKS_TO_COMPARE,
)
from classifier import classify_org, get_color

notion = Client(auth=NOTION_TOKEN)

# Contact Status values that mean "hot lead" in your Notion
HOT_LEAD_STATUSES = {"[training] hot lead", "[canva] hot lead"}


def _prop(page: dict, field: str, default=""):
    """Safely extract a Notion property value as a plain string or number."""
    props = page.get("properties", {})
    p = props.get(field)
    if not p:
        return default
    t = p.get("type", "")
    try:
        if t == "title":
            return "".join(r["plain_text"] for r in p["title"])
        if t == "rich_text":
            return "".join(r["plain_text"] for r in p["rich_text"])
        if t == "select":
            return (p["select"] or {}).get("name", default)
        if t == "multi_select":
            return ", ".join(o["name"] for o in p["multi_select"])
        if t == "status":
            return (p["status"] or {}).get("name", default)
        if t == "number":
            return p["number"] if p["number"] is not None else default
        if t == "checkbox":
            return p["checkbox"]
        if t == "date":
            return (p["date"] or {}).get("start", default)
        if t == "email":
            return p["email"] or default
        if t == "phone_number":
            return p["phone_number"] or default
        if t == "url":
            return p["url"] or default
        if t in ("created_time", "last_edited_time"):
            return p.get(t, default)
        if t == "people":
            return ", ".join((u.get("name") or "") for u in p["people"])
        if t == "formula":
            inner = p["formula"]
            return inner.get("string") or inner.get("number") or default
        if t == "rollup":
            arr = p["rollup"]
            if arr.get("type") == "number":
                return arr.get("number") or default
            return default
    except Exception:
        pass
    return default


def _query_all(db_id: str, filter_payload: dict | None = None) -> list[dict]:
    """Paginate through all results from a Notion database query."""
    results, cursor = [], None
    while True:
        kwargs: dict = {"database_id": db_id, "page_size": 100}
        if filter_payload:
            kwargs["filter"] = filter_payload
        if cursor:
            kwargs["start_cursor"] = cursor
        resp = notion.databases.query(**kwargs)
        results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp["next_cursor"]
    return results


def _week_range(weeks_ago: int = 0) -> tuple[datetime, datetime]:
    """Return (monday_00:00, sunday_23:59) UTC for N weeks ago."""
    today = datetime.now(timezone.utc).date()
    last_monday = today - timedelta(days=today.weekday() + 7 * weeks_ago)
    last_sunday  = last_monday + timedelta(days=6)
    start = datetime(last_monday.year, last_monday.month, last_monday.day, tzinfo=timezone.utc)
    end   = datetime(last_sunday.year, last_sunday.month, last_sunday.day, 23, 59, 59, tzinfo=timezone.utc)
    return start, end


# ── Marketing Leads ──────────────────────────────────────────────────────────

def fetch_leads(weeks_ago: int = 0) -> list[dict]:
    start, end = _week_range(weeks_ago)
    date_field = LEADS_FIELDS["date"]   # "Submitted at"

    filter_payload = {
        "and": [
            {"property": date_field, "date": {"on_or_after":  start.date().isoformat()}},
            {"property": date_field, "date": {"on_or_before": end.date().isoformat()}},
        ]
    }
    pages = _query_all(MARKETING_LEADS_DB_ID, filter_payload)

    leads = []
    for p in pages:
        org   = _prop(p, LEADS_FIELDS["org_name"])        # Company Name
        ctype = _prop(p, LEADS_FIELDS["org_type"])        # Company/Individual
        cl    = classify_org(org, ctype)
        if not cl["is_gov"]:
            continue

        raw_status = _prop(p, LEADS_FIELDS["status"]) or ""
        is_hot     = raw_status.lower() in HOT_LEAD_STATUSES

        leads.append({
            "contact_name":  _prop(p, LEADS_FIELDS["contact_name"]),
            "org_name":      org,
            "org_type":      ctype,
            "contact_email": _prop(p, LEADS_FIELDS["contact_email"]),
            "contact_phone": _prop(p, LEADS_FIELDS["contact_phone"]),
            "lead_source":   _prop(p, LEADS_FIELDS["lead_source"]),   # Channel
            "status":        raw_status,
            "date":          _prop(p, LEADS_FIELDS["date"]),
            "enquiry":       _prop(p, LEADS_FIELDS["enquiry"]),        # How can we help?
            "area":          _prop(p, LEADS_FIELDS["area"]),           # Area of Interest
            "notes":         _prop(p, LEADS_FIELDS["notes"]),
            "is_hot":        is_hot,
            "tier1":         cl["tier1_ministry"],
            "color":         get_color(cl["tier1_ministry"], is_hot),
            "notion_url":    p.get("url", ""),
        })
    return leads


# ── Past Classes ─────────────────────────────────────────────────────────────

def fetch_sessions(weeks_ago: int = 0) -> list[dict]:
    start, end = _week_range(weeks_ago)
    date_field = CLASSES_FIELDS["date"]   # "Class Date"

    filter_payload = {
        "and": [
            {"property": date_field, "date": {"on_or_after":  start.date().isoformat()}},
            {"property": date_field, "date": {"on_or_before": end.date().isoformat()}},
        ]
    }
    pages = _query_all(PAST_CLASSES_DB_ID, filter_payload)

    sessions = []
    for p in pages:
        org = _prop(p, CLASSES_FIELDS["org_name"])   # Company/Sector
        cl  = classify_org(org)
        if not cl["is_gov"]:
            continue
        sessions.append({
            "org_name":   org,
            "class_name": _prop(p, CLASSES_FIELDS["class_name"]),
            "date":       _prop(p, CLASSES_FIELDS["date"]),
            "feedback":   _prop(p, CLASSES_FIELDS["feedback"]),   # URL to feedback form
            "signup":     _prop(p, CLASSES_FIELDS["signup"]),
            "tier1":      cl["tier1_ministry"],
            "color":      get_color(cl["tier1_ministry"], False),
            "notion_url": p.get("url", ""),
        })
    return sessions


# ── Sales CRM ────────────────────────────────────────────────────────────────

def fetch_crm_all() -> list[dict]:
    """Fetch all CRM records (full pipeline snapshot)."""
    pages = _query_all(SALES_CRM_DB_ID)
    deals = []
    for p in pages:
        raw_val = _prop(p, CRM_FIELDS["deal_value"], 0)
        deals.append({
            "org_name":    _prop(p, CRM_FIELDS["org_name"]),        # Customer
            "deal_value":  float(raw_val) if raw_val else 0.0,
            "stage":       _prop(p, CRM_FIELDS["stage"]),           # Status
            "close_date":  _prop(p, CRM_FIELDS["close_date"]),      # Money Received on
            "train_date":  _prop(p, CRM_FIELDS["train_date"]),      # Training Date
            "owner":       _prop(p, CRM_FIELDS["owner"]),
            "course":      _prop(p, CRM_FIELDS["course"]),
            "contact":     _prop(p, CRM_FIELDS["contact"]),
            "pax":         _prop(p, CRM_FIELDS["pax"]),
            "gross_profit":_prop(p, CRM_FIELDS["gross_profit"], 0),
            "notion_url":  p.get("url", ""),
        })
    return deals


def fetch_weekly_revenue_history() -> list[dict]:
    """
    Revenue per week based on 'Money Received on' date in CRM.
    Returns [{week_label, monday_date, total_revenue}] oldest→newest.
    """
    all_deals = fetch_crm_all()
    weeks = []
    for w in range(WEEKS_TO_COMPARE + 1):
        start, end = _week_range(w)
        label = f"Wk {start.strftime('%-d %b')}" if w > 0 else "This week"
        total = sum(
            d["deal_value"] for d in all_deals
            if d["close_date"]
            and start.date().isoformat() <= d["close_date"] <= end.date().isoformat()
        )
        weeks.append({
            "week_label":    label,
            "monday_date":   start.date().isoformat(),
            "total_revenue": total,
        })
    weeks.reverse()   # oldest → newest
    return weeks
