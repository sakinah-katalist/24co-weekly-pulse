"""
24co Weekly Pulse — Local Dashboard
Run with:  streamlit run dashboard.py
"""

import json, base64, sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from charts import revenue_trend_chart, lead_status_donut, tier_breakdown_bar, crm_pipeline_bar, monthly_revenue_bar
from pdf_report import build_pdf, _session_type, _pending_collection, _revenue_last_7_days, _expand_org
from emailer import build_email_html, send_report
from config import EMAIL_TO, EMAIL_FROM

DATA_FILE  = str(Path(__file__).parent / "data" / "report.json")
PDF_OUTPUT = str(Path.home() / "Desktop" / "24co_WeeklyPulse_dashboard.pdf")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="24co Weekly Pulse",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global styles ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── BASE ── */
  html, body, [class*="css"] {
    font-size: 15px !important;
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif !important;
  }
  .stMarkdown p, .stMarkdown li { font-size: 14px; line-height: 1.75; }
  .stDataFrame { font-size: 13px !important; }
  .stExpander summary p { font-size: 14px !important; font-weight: 600; }
  .main { background: #EBEEF4; }
  .block-container { padding: 1.6rem 2rem 2rem; max-width: 1300px; }

  /* ── PILL TABS ── */
  .stTabs [data-baseweb="tab-list"] {
    background: #DDE2EA; padding: 5px 6px;
    border-radius: 14px; gap: 4px; border-bottom: none !important;
  }
  .stTabs [data-baseweb="tab"] {
    border-radius: 10px !important; padding: 10px 22px !important;
    font-size: 14px !important; font-weight: 600 !important;
    color: #5A6478 !important; background: transparent !important;
    border: none !important; outline: none !important;
  }
  .stTabs [aria-selected="true"] {
    background: #FFFFFF !important; color: #0D3349 !important;
    box-shadow: 0 2px 10px rgba(0,0,0,.12) !important;
  }
  .stTabs [data-baseweb="tab-highlight"],
  .stTabs [data-baseweb="tab-border"] { display: none !important; }
  .stTabs [data-baseweb="tab-panel"] { padding-top: 22px !important; }

  /* ── KPI CARDS ── */
  .kpi-card {
    background: #fff; border-radius: 14px;
    border: 1px solid #E2E7EE;
    box-shadow: 0 2px 12px rgba(0,0,0,.06);
    padding: 18px 16px 14px; text-align: center; min-height: 108px;
  }
  .kpi-val { font-size: 26px; font-weight: 800; margin: 0 0 4px; line-height: 1.1; }
  .kpi-lbl { font-size: 11px; font-weight: 700; color: #7A8499; margin: 0;
             text-transform: uppercase; letter-spacing: .05em; }
  .kpi-src { font-size: 10px; color: #B0B8C8; margin-top: 5px; }
  .kpi-teal   .kpi-val { color: #1A7F7A; }
  .kpi-green  .kpi-val { color: #1E9650; }
  .kpi-yellow .kpi-val { color: #B8870B; }
  .kpi-red    .kpi-val { color: #C0392B; }

  /* ── SECTION HEADS ── */
  .sec-head {
    font-size: 17px; font-weight: 800; color: #0D2035;
    border-bottom: 3px solid #1A7F7A;
    padding-bottom: 7px; margin: 0 0 4px; letter-spacing: -.01em;
  }
  .sec-sub { font-size: 12px; color: #96A0B0; margin: 0 0 14px; }

  /* ── SOURCE BADGE ── */
  .src-badge {
    display: inline-block; font-size: 10.5px; color: #6B788E;
    background: #EEF1F6; border-radius: 5px;
    padding: 2px 9px; margin-bottom: 13px;
    border: 1px solid #D8DFE8; font-weight: 500;
  }

  /* ── LEGEND CARDS ── */
  .legend-card {
    border-radius: 12px; padding: 18px 20px;
    border: 1px solid #E2E7EE;
    box-shadow: 0 1px 5px rgba(0,0,0,.04); height: 100%;
  }
  .legend-title { font-size: 15px; font-weight: 800; margin: 8px 0 9px; }
  .legend-desc  { font-size: 13px; color: #3D4A5C; line-height: 1.65; margin: 0; }
  .legend-eg    { font-size: 11px; color: #8A96A8; margin-top: 9px; font-style: italic; }

  /* ── ALERTS ── */
  .pending-alert {
    background: #FFF2F2; border: 1px solid #FFCDD2;
    border-left: 5px solid #C0392B; border-radius: 10px;
    padding: 14px 18px; margin: 8px 0;
  }
  .pending-alert p { margin: 0; font-size: 14px; color: #7B1616; font-weight: 500; }

  /* ── INSIGHT CARDS ── */
  .insight {
    border-radius: 10px; padding: 13px 18px;
    margin-bottom: 10px; font-size: 14px;
    line-height: 1.65; color: #2A3140;
    border-left: 5px solid transparent;
  }
  .insight-red    { background:#FFF2F2; border-left-color:#C0392B; }
  .insight-yellow { background:#FFFCEB; border-left-color:#C8960C; }
  .insight-green  { background:#F0FBF4; border-left-color:#1E9650; }
  .insight-teal   { background:#F0FAFA; border-left-color:#1A7F7A; }

  /* ── EXPANDERS ── */
  .streamlit-expanderHeader {
    background: #F4F6FA !important; border-radius: 8px !important;
    font-size: 14px !important; font-weight: 600 !important;
    border: 1px solid #DDE2EA !important;
  }
  .streamlit-expanderContent {
    border: 1px solid #DDE2EA !important; border-top: none !important;
    border-radius: 0 0 8px 8px !important;
    background: #FAFBFD !important; padding: 16px !important;
  }

  /* ── SIDEBAR ── */
  [data-testid="stSidebar"] { background: #0B2C42 !important; }
  [data-testid="stSidebar"] * { color: #D4DCE8 !important; }
  [data-testid="stSidebar"] .stMarkdown p { color: #B0BECE !important; font-size: 13px !important; }
  [data-testid="stSidebar"] h3 {
    color: #FFFFFF !important; font-size: 11px !important;
    letter-spacing: .09em; text-transform: uppercase; margin: 16px 0 8px;
  }
  .notion-tip {
    background: #163552; border: 1px solid #2A5A7A;
    border-radius: 8px; padding: 11px 14px;
    font-size: 12px; color: #9BB8CE !important; margin-bottom: 12px;
  }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _stage_ok(s):
    t = (s or "").lower()
    return any(k in t for k in ("paid","closed","proposal","quotation","almost"))

def _is_revenue(s):
    t = (s or "").lower()
    return "paid" in t or "closed" in t

def _colour_icon(item):
    if item.get("tier1"):   return "🟡"
    if item.get("is_hot"):  return "🔴"
    return "🟢"

def _badge_text(item):
    if item.get("tier1"):  return f"⭐ Tier 1 — {item['tier1']}"
    if item.get("is_hot"): return "🔥 Hot Lead"
    return "Gov / GovTech"

@st.cache_data(ttl=30)
def load_data():
    if not Path(DATA_FILE).exists():
        return None
    with open(DATA_FILE) as f:
        return json.load(f)

def _insight_html(clr, text):
    return f'<div class="insight insight-{clr}">{text}</div>'

def compute_insights(leads, sessions, crm_deals, revenue, report_date):
    out = []
    hot   = [l for l in leads if l.get("is_hot")]
    tier1 = [x for x in leads+sessions if x.get("tier1")]
    new_l = [l for l in leads if (l.get("status") or "").lower() == "new"]
    if hot:
        names = ", ".join(f"<b>{_expand_org(l['org_name'])}</b>" for l in hot)
        out.append(("red", f"🔥 <b>Urgent follow-up needed</b> — {len(hot)} hot lead(s): {names}"))
    if tier1:
        names = ", ".join(f"<b>{_expand_org(x['org_name'])}</b>" for x in tier1)
        out.append(("yellow", f"⭐ <b>Top-priority government match</b> — {len(tier1)} Tier 1 ministry lead(s): {names}"))
    if new_l:
        names = ", ".join(f"<b>{_expand_org(l['org_name'])}</b>" for l in new_l)
        out.append(("teal", f"📬 <b>New leads not yet contacted</b> — {len(new_l)}: {names}"))
    pending = _pending_collection(crm_deals, report_date)
    if pending:
        tot = sum(d.get("deal_value",0) or 0 for d in pending)
        out.append(("red", f"⚠️ <b>Payment outstanding</b> — {len(pending)} training(s) delivered but not yet paid · RM {tot:,.0f} owed"))
    rev_7d = _revenue_last_7_days(crm_deals, report_date)
    if rev_7d > 0:
        out.append(("green", f"💰 <b>RM {rev_7d:,.0f} received</b> in the last 7 days"))
    else:
        out.append(("teal", "📅 No new payments received in the last 7 days"))
    paid = sum(d.get("deal_value",0) or 0 for d in crm_deals if _is_revenue(d.get("stage","")))
    pipe = sum(d.get("deal_value",0) or 0 for d in crm_deals if _stage_ok(d.get("stage","")) and not _is_revenue(d.get("stage","")))
    if paid: out.append(("teal", f"✅ <b>RM {paid:,.0f} total confirmed revenue</b> (Paid & Closed deals)"))
    if pipe: out.append(("yellow", f"📋 <b>RM {pipe:,.0f} in active pipeline</b> — quotes sent, waiting for client decision"))
    if revenue and len(revenue) >= 2:
        curr, prev = revenue[-1]["total_revenue"], revenue[-2]["total_revenue"]
        if prev > 0:
            pct = (curr-prev)/prev*100
            clr = "green" if pct >= 0 else "red"
            dir = "up ▲" if pct >= 0 else "down ▼"
            out.append((clr, f"{'📈' if pct>=0 else '📉'} Revenue <b>{dir} {abs(pct):.1f}%</b> compared to last week (RM {curr:,.0f} vs RM {prev:,.0f})"))
    return out


# ═══════════════════════════════════════════════════════════════════
# PAGE HEADER
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<div style="background:linear-gradient(135deg,#0D3349 0%,#1A5276 100%);
            padding:22px 28px;border-radius:12px;margin-bottom:20px;
            box-shadow:0 4px 16px rgba(13,51,73,.25);">
  <p style="margin:0;color:#8FB8D0;font-size:11px;text-transform:uppercase;
            letter-spacing:.1em;font-weight:600;">Katalist Venture · Weekly Intelligence</p>
  <h1 style="margin:6px 0 2px;color:#fff;font-size:26px;font-weight:900;
             letter-spacing:-.01em;">📊 24co Weekly Pulse</h1>
  <p style="margin:0;color:#A8C8DF;font-size:13px;">
    Government &amp; GovTech activity monitor — powered by Notion data
  </p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 📡 Data")
    st.markdown("""
    <div class="notion-tip">
      Ask Claude to fetch the latest Notion data, then click <b>Refresh</b> below.
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear(); st.rerun()

    st.markdown("### 📄 Report")
    gen_pdf = st.button("⚙️ Build PDF Report", use_container_width=True)

    st.markdown("### 📧 Email")
    all_recip = list(dict.fromkeys(EMAIL_TO + [
        "sakinah@katalist.my","elaikha@katalist.my",
        "syafiq@katalist.my","andy@katalist.my","mubiin@katalist.my",
    ]))
    selected = st.multiselect("Send to:", options=all_recip, default=EMAIL_TO)
    custom = st.text_input("Add recipient:", placeholder="email@example.com")
    if custom and custom not in selected:
        selected.append(custom)
    send_now = st.button("📤 Send Report", use_container_width=True,
                         type="primary", disabled=not selected)
    st.caption(f"From: {EMAIL_FROM}")
    st.markdown("---")
    st.caption("24co Weekly Pulse v2.0")


# ═══════════════════════════════════════════════════════════════════
# LOAD DATA
# ═══════════════════════════════════════════════════════════════════
data = load_data()
if data is None:
    st.warning("⚠️ No data found. Ask Claude to fetch this week's Notion data first, then click Refresh.")
    st.stop()

report_date  = datetime.fromisoformat(data["report_date"])
period_label = data["period_label"]
leads        = data.get("leads", [])
sessions     = data.get("sessions", [])
crm_deals    = data.get("crm_deals", [])
revenue      = data.get("revenue_history", [])

crm_filtered = [d for d in crm_deals if _stage_ok(d.get("stage",""))]
rev_7d       = _revenue_last_7_days(crm_deals, report_date)
paid_total   = sum(d.get("deal_value",0) or 0 for d in crm_deals if _is_revenue(d.get("stage","")))
pipe_total   = sum(d.get("deal_value",0) or 0 for d in crm_filtered if not _is_revenue(d.get("stage","")))
tier1_count  = sum(1 for x in leads+sessions if x.get("tier1"))
pub_sess     = sum(1 for s in sessions if _session_type(s) == "Public")
inh_sess     = len(sessions) - pub_sess
pending      = _pending_collection(crm_deals, report_date)

# Period strip
st.markdown(
    f'<p style="font-size:13px;color:#666;margin:-8px 0 16px;">'
    f'📅 <b>Reporting period:</b> {period_label} &nbsp;·&nbsp; '
    f'Last refreshed: {datetime.now().strftime("%d %b %Y, %H:%M")}</p>',
    unsafe_allow_html=True
)

# ── Pending collection alert (top-level) ──────────────────────────
if pending:
    total_out = sum(d.get("deal_value",0) or 0 for d in pending)
    st.markdown(f"""
    <div class="pending-alert">
      <p>⚠️ <b>Action required:</b> {len(pending)} completed training(s) still waiting for payment
         — <b>RM {total_out:,.0f} outstanding</b>. See Sales CRM tab for details.</p>
    </div>
    """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# KPI TILES
# ═══════════════════════════════════════════════════════════════════
st.markdown('<p class="sec-head">This Week at a Glance</p>', unsafe_allow_html=True)
c1,c2,c3,c4,c5,c6 = st.columns(6)
kpis = [
    (c1, str(len(leads)),                 "New Enquiries",        "teal",  "Marketing Leads DB"),
    (c2, f"{pub_sess} Public / {inh_sess} Private", "Training Sessions", "teal", "Past Classes DB"),
    (c3, str(tier1_count),                "Tier 1 Gov Matches",   "yellow",""),
    (c4, f"RM {rev_7d:,.0f}",             "Revenue This Week",    "green", "CRM — last 7 days"),
    (c5, f"RM {paid_total:,.0f}",         "Total Revenue (Paid)", "teal",  "CRM — all time"),
    (c6, f"RM {pipe_total:,.0f}",         "Pending Pipeline",     "yellow","CRM — open quotes"),
]
for col, val, lbl, clr, src in kpis:
    with col:
        src_html = f'<p class="kpi-src">📂 {src}</p>' if src else ""
        st.markdown(f"""
        <div class="kpi-card kpi-{clr}">
          <p class="kpi-val">{val}</p>
          <p class="kpi-lbl">{lbl}</p>
          {src_html}
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "📋  Leads & Sessions",
    "💼  Sales CRM",
    "🤖  Insights",
    "📄  PDF & Email",
])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1 — LEADS & SESSIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:

    # ── How to read this section ──────────────────────────────────
    with st.expander("📖  How to read this section — what do the colours mean?", expanded=False):
        lc1, lc2, lc3 = st.columns(3)
        with lc1:
            st.markdown("""
            <div class="legend-card" style="background:#FFFBEA;border-color:#F5D76E;">
              <div style="font-size:24px;">🟡</div>
              <p class="legend-title" style="color:#B8860B;">Yellow — Tier 1 Government Ministry</p>
              <p class="legend-desc">
                This organisation belongs to one of Malaysia's <b>8 highest-level federal ministries</b>
                — such as Finance (MOF), Defence (MINDEF), Education (MOE), or Home Affairs (KDN).
                These are the most strategic government accounts.
              </p>
              <p class="legend-eg">Examples: LHDN, BSN, JPA, any ministry HQ</p>
            </div>""", unsafe_allow_html=True)
        with lc2:
            st.markdown("""
            <div class="legend-card" style="background:#FFF3F3;border-color:#F5C6C6;">
              <div style="font-size:24px;">🔴</div>
              <p class="legend-title" style="color:#C0392B;">Red — Hot Lead</p>
              <p class="legend-desc">
                This lead has <b>expressed strong interest</b> and is likely to convert to a booking
                soon. They need a fast response — ideally within 24–48 hours.
              </p>
              <p class="legend-eg">Triggered when Notion status = "Hot Lead"</p>
            </div>""", unsafe_allow_html=True)
        with lc3:
            st.markdown("""
            <div class="legend-card" style="background:#F0FAFA;border-color:#B2DADA;">
              <div style="font-size:24px;">🟢</div>
              <p class="legend-title" style="color:#1A7F7A;">Teal — Standard Government / GovTech</p>
              <p class="legend-desc">
                A government-related organisation — could be a <b>statutory body, GLC (government-linked
                company), public agency, or a tech vendor</b> that serves the government sector.
              </p>
              <p class="legend-eg">Examples: Prasarana, Petronas, MIMOS, GovTech vendors</p>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#F8F9FB;border-radius:8px;padding:14px 18px;margin-top:14px;
                    border:1px solid #E0E4EA;font-size:13px;color:#555;">
          <b>🏢 In-house session</b> — A private, exclusive training booked for one organisation only.
          &nbsp;&nbsp;|&nbsp;&nbsp;
          <b>🌐 Public session</b> — An open class that anyone can register for.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_l, col_r = st.columns(2, gap="large")

    # ── GOV LEADS ────────────────────────────────────────────────
    with col_l:
        st.markdown('<p class="sec-head">Government Enquiries</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="sec-sub">New leads from government-linked organisations this week</p>',
            unsafe_allow_html=True
        )
        st.markdown('<span class="src-badge">📂 Notion — Marketing Leads Database</span>',
                    unsafe_allow_html=True)

        if leads:
            # Status breakdown strip
            counts = Counter(l.get("status") or "Unknown" for l in leads)
            total  = sum(counts.values())
            parts  = " &nbsp;·&nbsp; ".join(
                f'<b>{s}</b>: {n} ({n/total*100:.0f}%)'
                for s, n in sorted(counts.items(), key=lambda x: -x[1])
            )
            st.markdown(
                f'<div style="background:#EEF8F7;border-radius:6px;padding:8px 12px;'
                f'margin-bottom:12px;font-size:13px;color:#1A7F7A;border:1px solid #C8E6E4;">'
                f'Status summary: {parts}</div>',
                unsafe_allow_html=True
            )
            for l in sorted(leads, key=lambda x: (0 if x.get("tier1") else 1, 0 if x.get("is_hot") else 1)):
                label = f"{_colour_icon(l)}  {_expand_org(l['org_name'])}  —  {_badge_text(l)}"
                with st.expander(label, expanded=l.get("is_hot") or bool(l.get("tier1"))):
                    if l.get("description"):
                        st.markdown(f'<p style="font-size:13px;color:#555;font-style:italic;'
                                    f'background:#F8F8F8;padding:8px 12px;border-radius:6px;'
                                    f'margin-bottom:10px;">📌 {l["description"]}</p>',
                                    unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Contact person:** {l.get('contact_name','—')}")
                        st.write(f"**Email:** {l.get('contact_email','—')}")
                        st.write(f"**Phone:** {l.get('contact_phone','—')}")
                        st.write(f"**How they found us:** {l.get('lead_source','—')}")
                    with c2:
                        st.write(f"**Current status:** {l.get('status','—')}")
                        st.write(f"**Date received:** {l.get('date','—')}")
                        st.write(f"**Training area:** {l.get('area','—')}")
                    st.write(f"**What they need:** {l.get('enquiry','—')}")
                    if l.get("notes"):
                        st.write(f"**Internal notes:** {l['notes']}")
                    if l.get("notion_url"):
                        st.markdown(f"[📎 Open in Notion]({l['notion_url']})")
        else:
            st.info("No government enquiries this week.")

    # ── SESSIONS ────────────────────────────────────────────────
    with col_r:
        st.markdown('<p class="sec-head">Training Sessions This Week</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="sec-sub">Government & GovTech sessions delivered this period</p>',
            unsafe_allow_html=True
        )
        st.markdown('<span class="src-badge">📂 Notion — Past Classes Database</span>',
                    unsafe_allow_html=True)

        if sessions:
            pub_list = [s for s in sessions if _session_type(s) == "Public"]
            inh_list = [s for s in sessions if _session_type(s) == "In-house"]
            st.markdown(
                f'<div style="background:#EEF8F7;border-radius:6px;padding:8px 12px;'
                f'margin-bottom:12px;font-size:13px;color:#1A7F7A;border:1px solid #C8E6E4;">'
                f'🌐 <b>Public:</b> {len(pub_list)} &nbsp;·&nbsp; '
                f'🏢 <b>In-house / Private:</b> {len(inh_list)} &nbsp;·&nbsp; '
                f'Total: <b>{len(sessions)}</b></div>',
                unsafe_allow_html=True
            )
            for s in sorted(sessions, key=lambda x: (0 if x.get("tier1") else 1)):
                stype = _session_type(s)
                icon  = "🌐" if stype == "Public" else "🏢"
                label = f"{_colour_icon(s)}  {_expand_org(s['org_name'])}  —  {_badge_text(s)}  {icon} {stype}"
                with st.expander(label, expanded=bool(s.get("tier1"))):
                    if s.get("description"):
                        st.markdown(f'<p style="font-size:13px;color:#555;font-style:italic;'
                                    f'background:#F8F8F8;padding:8px 12px;border-radius:6px;'
                                    f'margin-bottom:10px;">📌 {s["description"]}</p>',
                                    unsafe_allow_html=True)
                    st.write(f"**Training programme:** {s.get('class_name','—')}")
                    st.write(f"**Date:** {s.get('date','—')}")
                    st.write(f"**Session type:** {icon} {stype}")
                    if s.get("notion_url"):
                        st.markdown(f"[📎 Open in Notion]({s['notion_url']})")
        else:
            st.info("No training sessions recorded this week.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2 — SALES CRM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    import pandas as pd

    # ── helpers scoped to this tab ────────────────────────────────
    YEAR = 2026
    YEAR_START = f"{YEAR}-01-01"
    YEAR_END   = f"{YEAR}-12-31"
    MONTH_NAMES = ["January","February","March","April","May","June",
                   "July","August","September","October","November","December"]

    def _paid_deals(deal_list):
        return [d for d in deal_list if _is_revenue(d.get("stage",""))]

    def _deals_in_range(deal_list, start: str, end: str):
        out = []
        for d in _paid_deals(deal_list):
            cd = (d.get("close_date") or "")[:10]
            if cd and start <= cd <= end:
                out.append(d)
        return out

    def _rev(deal_list):
        return sum(d.get("deal_value",0) or 0 for d in deal_list)

    def _deal_table(deal_list):
        rows = []
        for d in sorted(deal_list, key=lambda x: (x.get("close_date") or ""), reverse=True):
            stg  = d.get("stage","")
            icon = "✅" if "paid" in stg.lower() else "📁"
            rows.append({
                "Organisation":   _expand_org(d.get("org_name","")),
                "Status":         f"{icon} {stg}",
                "Value":          f"RM {d.get('deal_value',0) or 0:,.0f}",
                "Date Paid/Closed": d.get("close_date") or "—",
                "Course":         d.get("course",""),
            })
        return pd.DataFrame(rows) if rows else None

    def _kpi_html(val, lbl, sub, colour="teal"):
        return f"""
        <div class="kpi-card kpi-{colour}" style="text-align:left;padding:16px 20px;">
          <p class="kpi-val" style="font-size:26px;">{val}</p>
          <p class="kpi-lbl">{lbl}</p>
          <p class="kpi-src">{sub}</p>
        </div>"""

    # ── reference date from data ──────────────────────────────────
    rd       = report_date
    rd_str   = rd.strftime("%Y-%m-%d")
    cur_mon  = rd.month
    # first day of current month
    cur_mon_start = f"{YEAR}-{cur_mon:02d}-01"
    # first day 3 calendar months ago
    m3 = cur_mon - 3
    y3 = YEAR + (m3 - 1) // 12
    m3 = ((m3 - 1) % 12) + 1
    three_mo_start = f"{y3}-{m3:02d}-01"

    d7  = (rd - timedelta(days=7)).strftime("%Y-%m-%d")
    d14 = (rd - timedelta(days=14)).strftime("%Y-%m-%d")

    # pre-compute each period
    deals_7d  = _deals_in_range(crm_deals, d7, rd_str)
    deals_14d = _deals_in_range(crm_deals, d14, rd_str)
    deals_3m  = _deals_in_range(crm_deals, three_mo_start, rd_str)
    deals_yr  = _deals_in_range(crm_deals, YEAR_START, YEAR_END)
    # monthly
    monthly_data = {}
    for m in range(1, 13):
        ms = f"{YEAR}-{m:02d}-01"
        me_day = 31 if m in (1,3,5,7,8,10,12) else (30 if m in (4,6,9,11) else 28)
        me = f"{YEAR}-{m:02d}-{me_day:02d}"
        monthly_data[m] = _deals_in_range(crm_deals, ms, me)

    # ── page header ───────────────────────────────────────────────
    st.markdown('<p class="sec-head">Sales CRM — Revenue Analysis</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sec-sub">Paid & Closed government deals only — pulled from Notion Sales CRM</p>',
        unsafe_allow_html=True
    )
    st.markdown('<span class="src-badge">📂 Notion — Sales CRM Database</span>',
                unsafe_allow_html=True)

    # ── CRM stage legend ──────────────────────────────────────────
    with st.expander("📖  What do these deal statuses mean?", expanded=False):
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            st.markdown("""
            <div class="legend-card" style="background:#F0FBF4;border-color:#B3E5C4;">
              <div style="font-size:26px;">✅</div>
              <p class="legend-title" style="color:#1A7A3C;">Paid</p>
              <p class="legend-desc">Invoice settled — <b>money received in bank</b>. Counts as confirmed revenue.</p>
            </div>""", unsafe_allow_html=True)
        with dc2:
            st.markdown("""
            <div class="legend-card" style="background:#F0FAFA;border-color:#B2DADA;">
              <div style="font-size:26px;">📁</div>
              <p class="legend-title" style="color:#1A7F7A;">Closed</p>
              <p class="legend-desc">Training delivered, deal marked complete — <b>payment confirmed in CRM</b>.</p>
            </div>""", unsafe_allow_html=True)
        with dc3:
            st.markdown("""
            <div class="legend-card" style="background:#FFFBEA;border-color:#F5E7A0;">
              <div style="font-size:26px;">📋</div>
              <p class="legend-title" style="color:#B8860B;">Proposal / Quotation</p>
              <p class="legend-desc">Quote sent to client — <b>awaiting their decision</b>. Active pipeline, not yet revenue.</p>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════════════
    # REVENUE ANALYSIS — time-period tabs
    # ════════════════════════════════════════════════════════════════
    st.markdown('<p class="sec-head">Revenue Breakdown by Time Period</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sec-sub">Select a time window to see exactly how much was collected and from which deals</p>',
        unsafe_allow_html=True
    )

    tp1, tp2, tp3, tp4, tp5 = st.tabs([
        "📅  Last 7 Days",
        "📅  Last 14 Days",
        "📅  Last 3 Months",
        "📆  By Month (2026)",
        "🗓️  Full Year 2026",
    ])

    # ── Last 7 Days ───────────────────────────────────────────────
    with tp1:
        rev = _rev(deals_7d)
        st.markdown(
            f'<div style="background:#F0FBF4;border-left:5px solid #27AE60;border-radius:8px;'
            f'padding:14px 20px;margin-bottom:16px;">'
            f'<p style="margin:0;font-size:13px;color:#666;">Period: <b>{d7}</b> → <b>{rd_str}</b></p>'
            f'<p style="margin:4px 0 0;font-size:28px;font-weight:800;color:#1A7A3C;">RM {rev:,.0f}</p>'
            f'<p style="margin:2px 0 0;font-size:13px;color:#666;">{len(deals_7d)} deal(s) collected</p>'
            f'</div>',
            unsafe_allow_html=True
        )
        if deals_7d:
            df = _deal_table(deals_7d)
            if df is not None:
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No payments received in the last 7 days.")

    # ── Last 14 Days ──────────────────────────────────────────────
    with tp2:
        rev = _rev(deals_14d)
        st.markdown(
            f'<div style="background:#F0FBF4;border-left:5px solid #27AE60;border-radius:8px;'
            f'padding:14px 20px;margin-bottom:16px;">'
            f'<p style="margin:0;font-size:13px;color:#666;">Period: <b>{d14}</b> → <b>{rd_str}</b></p>'
            f'<p style="margin:4px 0 0;font-size:28px;font-weight:800;color:#1A7A3C;">RM {rev:,.0f}</p>'
            f'<p style="margin:2px 0 0;font-size:13px;color:#666;">{len(deals_14d)} deal(s) collected</p>'
            f'</div>',
            unsafe_allow_html=True
        )
        if deals_14d:
            df = _deal_table(deals_14d)
            if df is not None:
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No payments received in the last 14 days.")

    # ── Last 3 Months ─────────────────────────────────────────────
    with tp3:
        rev = _rev(deals_3m)
        st.markdown(
            f'<div style="background:#F0FBF4;border-left:5px solid #27AE60;border-radius:8px;'
            f'padding:14px 20px;margin-bottom:16px;">'
            f'<p style="margin:0;font-size:13px;color:#666;">Period: <b>{three_mo_start}</b> → <b>{rd_str}</b> (3 calendar months)</p>'
            f'<p style="margin:4px 0 0;font-size:28px;font-weight:800;color:#1A7A3C;">RM {rev:,.0f}</p>'
            f'<p style="margin:2px 0 0;font-size:13px;color:#666;">{len(deals_3m)} deal(s) collected</p>'
            f'</div>',
            unsafe_allow_html=True
        )
        # Month-by-month breakdown within the 3-month window
        months_in_range = [m for m in range(1, 13)
                           if f"{YEAR}-{m:02d}-01" >= three_mo_start
                           and f"{YEAR}-{m:02d}-01" <= rd_str]
        sub_cols = st.columns(len(months_in_range)) if months_in_range else []
        for col, m in zip(sub_cols, months_in_range):
            mdeals = monthly_data[m]
            mrev   = _rev(mdeals)
            clr    = "green" if mrev > 0 else "teal"
            with col:
                st.markdown(_kpi_html(
                    f"RM {mrev:,.0f}", MONTH_NAMES[m-1],
                    f"{len(mdeals)} deal(s)", clr
                ), unsafe_allow_html=True)

        st.markdown("")
        if deals_3m:
            df = _deal_table(deals_3m)
            if df is not None:
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No payments received in the last 3 months.")

    # ── By Month ──────────────────────────────────────────────────
    with tp4:
        st.markdown(
            f'<p style="font-size:14px;color:#666;margin-bottom:12px;">'
            f'Monthly revenue for all of <b>{YEAR}</b> — calendar year Jan 1 to Dec 31</p>',
            unsafe_allow_html=True
        )

        # Full-year monthly chart
        st.image(monthly_revenue_bar(crm_deals, YEAR, cur_mon),
                 use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Monthly breakdown table
        month_rows = []
        running = 0.0
        for m in range(1, 13):
            mdeals = monthly_data[m]
            mrev   = _rev(mdeals)
            running += mrev
            prev_rev = _rev(monthly_data[m-1]) if m > 1 else None
            if prev_rev is not None and prev_rev > 0:
                chg = (mrev - prev_rev) / prev_rev * 100
                chg_str = f"{'▲' if chg>=0 else '▼'} {abs(chg):.0f}%"
            elif mrev > 0 and (prev_rev == 0 or prev_rev is None):
                chg_str = "▲ New revenue"
            else:
                chg_str = "—"

            is_cur  = "◀ current" if m == cur_mon else ""
            is_fut  = m > cur_mon
            month_rows.append({
                "Month":              MONTH_NAMES[m-1] + (" " + is_cur if is_cur else ""),
                "Revenue Received":   f"RM {mrev:,.0f}" if not is_fut else "—  (future)",
                "Deals":              str(len(mdeals)) if not is_fut else "—",
                "vs Prev Month":      chg_str if not is_fut else "—",
                "Running Total (YTD)":f"RM {running:,.0f}" if not is_fut else "—",
            })

        mdf = pd.DataFrame(month_rows)
        st.dataframe(mdf, use_container_width=True, hide_index=True)

        # Year-to-date summary
        ytd = _rev(deals_yr)
        best_m = max(range(1, 13), key=lambda m: _rev(monthly_data[m]))
        best_rev = _rev(monthly_data[best_m])
        active_months = sum(1 for m in range(1, 13) if _rev(monthly_data[m]) > 0)
        st.markdown(
            f'<div style="background:#EEF8F7;border-radius:8px;padding:14px 20px;'
            f'margin-top:12px;border:1px solid #C8E6E4;font-size:14px;">'
            f'📊 <b>Year-to-date ({YEAR}):</b> RM {ytd:,.0f} from {len(deals_yr)} deal(s) '
            f'across {active_months} month(s) &nbsp;·&nbsp; '
            f'Best month: <b>{MONTH_NAMES[best_m-1]}</b> (RM {best_rev:,.0f})'
            f'</div>',
            unsafe_allow_html=True
        )

    # ── Full Year 2026 ────────────────────────────────────────────
    with tp5:
        yr_rev   = _rev(deals_yr)
        yr_deals = len(deals_yr)

        # Top-line KPIs
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(_kpi_html(f"RM {yr_rev:,.0f}", "Total Revenue",
                                  f"Jan 1 – Dec 31 {YEAR}", "green"), unsafe_allow_html=True)
        with k2:
            st.markdown(_kpi_html(str(yr_deals), "Paid Deals",
                                  f"in {YEAR}", "teal"), unsafe_allow_html=True)
        avg = yr_rev / yr_deals if yr_deals else 0
        with k3:
            st.markdown(_kpi_html(f"RM {avg:,.0f}", "Avg Deal Value",
                                  "per paid/closed deal", "teal"), unsafe_allow_html=True)
        months_gone = sum(1 for m in range(1, 13) if m <= cur_mon)
        monthly_run_rate = yr_rev / months_gone if months_gone else 0
        projected = monthly_run_rate * 12
        with k4:
            st.markdown(_kpi_html(f"RM {projected:,.0f}", "Projected Full-Year",
                                  f"based on {months_gone}-month run rate", "yellow"),
                        unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Chart
        st.image(monthly_revenue_bar(crm_deals, YEAR, cur_mon),
                 use_container_width=True)

        # Quarter breakdown
        st.markdown('<p style="font-size:15px;font-weight:700;color:#0D3349;margin:16px 0 8px;">Quarter breakdown</p>',
                    unsafe_allow_html=True)
        q_cols = st.columns(4)
        quarters = [(1,3,"Q1 Jan–Mar"),(4,6,"Q2 Apr–Jun"),(7,9,"Q3 Jul–Sep"),(10,12,"Q4 Oct–Dec")]
        for col, (qstart, qend, qlbl) in zip(q_cols, quarters):
            qdeals = []
            for m in range(qstart, qend+1):
                qdeals.extend(monthly_data[m])
            qrev = _rev(qdeals)
            is_active = any(qstart <= m <= qend for m in range(1, cur_mon+1))
            clr = "green" if qrev > 0 else ("teal" if is_active else "teal")
            with col:
                st.markdown(_kpi_html(
                    f"RM {qrev:,.0f}", qlbl,
                    f"{len(qdeals)} deal(s)", clr
                ), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # All year deals table
        if deals_yr:
            st.markdown('<p style="font-size:15px;font-weight:700;color:#0D3349;margin-bottom:8px;">All paid/closed deals in 2026</p>',
                        unsafe_allow_html=True)
            df = _deal_table(deals_yr)
            if df is not None:
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info(f"No paid/closed deals recorded in {YEAR} yet.")

    # ════════════════════════════════════════════════════════════════
    # PIPELINE OVERVIEW (below revenue analysis)
    # ════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown('<p class="sec-head">Current Pipeline</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sec-sub">Quotes sent to clients — not yet revenue</p>',
        unsafe_allow_html=True
    )

    if crm_filtered:
        by_stage = defaultdict(lambda: {"count": 0, "total": 0.0})
        for d in crm_filtered:
            by_stage[d.get("stage","—")]["count"] += 1
            by_stage[d.get("stage","—")]["total"] += d.get("deal_value",0) or 0

        stage_cols = st.columns(len(by_stage))
        for col, (stage, info) in zip(stage_cols, sorted(by_stage.items(), key=lambda x:-x[1]["total"])):
            clr  = "green" if _is_revenue(stage) else "yellow"
            icon = "✅" if "paid" in stage.lower() else ("📁" if "closed" in stage.lower() else "📋")
            with col:
                st.markdown(f"""
                <div class="kpi-card kpi-{clr}">
                  <p class="kpi-val">RM {info['total']:,.0f}</p>
                  <p class="kpi-lbl">{icon} {stage}</p>
                  <p class="kpi-src">{info['count']} deal{'s' if info['count']!=1 else ''}</p>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.image(crm_pipeline_bar(crm_deals), use_container_width=True)

        st.markdown('<p style="font-size:15px;font-weight:700;color:#0D3349;margin:12px 0 8px;">All qualifying deals</p>',
                    unsafe_allow_html=True)
        rows = []
        for d in sorted(crm_filtered, key=lambda x: -(x.get("deal_value") or 0)):
            stg  = d.get("stage","")
            icon = "✅" if "paid" in stg.lower() else ("📁" if "closed" in stg.lower() else "📋")
            rows.append({
                "Organisation":   _expand_org(d.get("org_name","")),
                "Status":         f"{icon} {stg}",
                "Value":          f"RM {d.get('deal_value',0) or 0:,.0f}",
                "Date Closed":    d.get("close_date") or "Not yet",
                "Course / Notes": d.get("course",""),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── Pending collection ────────────────────────────────────────
    st.markdown("---")
    st.markdown('<p class="sec-head">⚠️ Awaiting Payment</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sec-sub">Trainings delivered but invoice not yet paid</p>',
        unsafe_allow_html=True
    )
    if not pending:
        st.success("✅ All good — every completed training has been paid for.")
    else:
        total_out = sum(d.get("deal_value",0) or 0 for d in pending)
        st.markdown(f"""
        <div class="pending-alert">
          <p>⚠️ <b>{len(pending)} deal(s) — RM {total_out:,.0f} still outstanding.</b></p>
        </div>""", unsafe_allow_html=True)
        prows = [{"Organisation": _expand_org(d.get("org_name","")), "Status": d.get("stage",""),
                  "Amount Owed": f"RM {d.get('deal_value',0) or 0:,.0f}",
                  "Training Date": d.get("train_date","—"), "Contact": d.get("contact","")}
                 for d in pending]
        st.dataframe(pd.DataFrame(prows), use_container_width=True, hide_index=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3 — INSIGHTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:
    st.markdown('<p class="sec-head">What You Need to Know This Week</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sec-sub">Automatically generated from this week\'s data — key actions and observations</p>',
        unsafe_allow_html=True
    )

    insights = compute_insights(leads, sessions, crm_deals, revenue, report_date)
    for clr, txt in insights:
        st.markdown(f'<div class="insight insight-{clr}">{txt}</div>', unsafe_allow_html=True)

    # Charts
    st.markdown("---")
    st.markdown('<p style="font-size:15px;font-weight:700;color:#0D3349;margin-bottom:12px;">Visual breakdown</p>',
                unsafe_allow_html=True)
    ch1, ch2 = st.columns(2, gap="large")
    with ch1:
        if leads:
            st.image(lead_status_donut(leads), use_container_width=True)
    with ch2:
        st.image(tier_breakdown_bar(leads, sessions), use_container_width=True)

    # Lead status table
    if leads:
        st.markdown("---")
        st.markdown('<p style="font-size:15px;font-weight:700;color:#0D3349;margin-bottom:4px;">Lead status breakdown</p>',
                    unsafe_allow_html=True)
        st.caption("How are this week's leads distributed by status?")
        import pandas as pd
        counts = Counter(l.get("status") or "Unknown" for l in leads)
        total  = sum(counts.values())
        srows  = [{"Status": s, "Count": n, "Share": f"{n/total*100:.0f}%"}
                  for s, n in sorted(counts.items(), key=lambda x: -x[1])]
        srows.append({"Status": "Total", "Count": total, "Share": "100%"})
        st.dataframe(pd.DataFrame(srows), use_container_width=True, hide_index=True)

    # Follow-up table
    followup = [l for l in leads if (l.get("status") or "").lower() in
                ("new", "contacted", "[training] hot lead", "[canva] hot lead")]
    if followup:
        st.markdown("---")
        st.markdown('<p style="font-size:15px;font-weight:700;color:#C0392B;margin-bottom:4px;">🎯 Leads needing action</p>',
                    unsafe_allow_html=True)
        st.caption("These leads should be followed up this week.")
        import pandas as pd
        frows = [{"Priority": "🔥 HOT" if l.get("is_hot") else ("⭐ Tier 1" if l.get("tier1") else "📋 Standard"),
                  "Organisation": _expand_org(l.get("org_name","")),
                  "Contact": l.get("contact_name",""),
                  "Status": l.get("status",""),
                  "Training Area": l.get("area",""),
                  }
                 for l in sorted(followup, key=lambda x: (0 if x.get("is_hot") else 1))]
        st.dataframe(pd.DataFrame(frows), use_container_width=True, hide_index=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4 — PDF & EMAIL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab4:
    st.markdown('<p class="sec-head">PDF Report</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sec-sub">Generate the weekly PDF report and send it to the team</p>',
        unsafe_allow_html=True
    )

    pdf_path = Path(PDF_OUTPUT)
    s1, s2 = st.columns([2, 3])
    with s1:
        if pdf_path.exists():
            mtime = datetime.fromtimestamp(pdf_path.stat().st_mtime)
            age   = int((datetime.now() - mtime).total_seconds() // 60)
            st.success(f"✅ PDF ready — {pdf_path.stat().st_size // 1024} KB")
            st.caption(f"Built: {mtime.strftime('%d %b %Y, %H:%M')} ({age} min ago)")
        else:
            st.warning("No PDF yet — click Build below.")

    if gen_pdf or st.button("⚙️ Build PDF Report", key="build_tab"):
        with st.spinner("Building your PDF report..."):
            from charts import revenue_line_chart as _rlc
            cbs = {
                "revenue_line": _rlc(revenue) if revenue else None,
            }
            build_pdf(leads=leads, sessions=sessions, crm_deals=crm_deals,
                      revenue_history=revenue, report_date=report_date,
                      period_label=period_label, chart_bytes=cbs, output_path=PDF_OUTPUT)
        st.success(f"✅ PDF built — {Path(PDF_OUTPUT).stat().st_size // 1024} KB")
        st.rerun()

    if pdf_path.exists():
        with open(PDF_OUTPUT, "rb") as f:
            pdf_bytes = f.read()
        st.download_button("⬇️  Download PDF", data=pdf_bytes,
                           file_name=f"24co_WeeklyPulse_{report_date.strftime('%Y-%m-%d')}.pdf",
                           mime="application/pdf")
        with st.expander("👁️  Preview PDF in browser", expanded=False):
            b64 = base64.b64encode(pdf_bytes).decode()
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{b64}" '
                f'width="100%" height="720px" style="border:1px solid #DDE0E5;'
                f'border-radius:8px;"></iframe>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown('<p class="sec-head">Send to Team</p>', unsafe_allow_html=True)
    if not pdf_path.exists():
        st.warning("Build the PDF first.")
    elif not selected:
        st.warning("Choose at least one recipient in the sidebar.")
    elif send_now:
        with st.spinner(f"Sending to {', '.join(selected)}..."):
            subj, html = build_email_html(leads, sessions, report_date, period_label)
            send_report(subj, html, PDF_OUTPUT, to_override=selected)
        st.success(f"✅ Sent to: {', '.join(selected)}")
        st.balloons()
    else:
        st.info(f"Ready to send to **{', '.join(selected)}** — click **Send Report** in the sidebar.")


# ── Footer ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<p style="font-size:11px;color:#aaa;text-align:center;">'
    '24co Weekly Pulse &nbsp;·&nbsp; Katalist Venture &nbsp;·&nbsp; '
    f'Data source: {DATA_FILE}</p>',
    unsafe_allow_html=True
)
