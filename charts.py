"""Generate matplotlib charts as PNG bytes for embedding in the PDF."""

import io
import re
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np

BRAND = {
    "yellow": "#F5C800",
    "red":    "#C0392B",
    "teal":   "#1A7F7A",
    "bg":     "#FFFFFF",   # white bg so charts look clean in PDF
    "text":   "#1C1C1C",
    "grid":   "#E8E8E8",
}
BRAND["gold"] = BRAND["yellow"]

# Stages included in CRM analysis
CRM_INCLUDED = ("paid", "closed", "proposal", "quotation", "almost")


def _stage_ok(stage: str) -> bool:
    s = (stage or "").lower()
    return any(k in s for k in CRM_INCLUDED)


def _clean(s: str) -> str:
    """Strip emojis / non-ASCII that matplotlib cannot render."""
    return re.sub(r"[^\x00-\x7F]+", "", s).strip() or "Unknown"


def _save(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _base_ax(figsize):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(BRAND["bg"])
    ax.set_facecolor(BRAND["bg"])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=BRAND["text"], labelsize=8)
    ax.set_axisbelow(True)
    return fig, ax


# ── Revenue trend ─────────────────────────────────────────────────────────────
def revenue_trend_chart(weeks: list[dict]) -> bytes:
    """Bar + line combo: weekly revenue, oldest → newest."""
    labels = [w["week_label"] for w in weeks]
    values = [w["total_revenue"] for w in weeks]
    n = len(labels)

    current = values[-1] if values else 0
    prev    = values[-2] if n > 1 else 0
    if prev > 0:
        pct = (current - prev) / prev * 100
    elif current > 0:
        pct = 100.0
    else:
        pct = 0.0

    fig, ax = _base_ax((max(6.5, n * 1.3), 2.6))

    bar_colors = [BRAND["teal"]] * n
    if n:
        bar_colors[-1] = BRAND["yellow"]

    ax.bar(labels, values, color=bar_colors, width=0.55,
           zorder=2, edgecolor="white", linewidth=0.8)
    ax.plot(labels, values, color=BRAND["red"], linewidth=1.8,
            marker="o", markersize=5, zorder=3)

    # % change badge — always placed in top-right axes fraction
    if n > 1:
        arrow = "▲" if pct >= 0 else "▼"
        clr   = "#27AE60" if pct >= 0 else BRAND["red"]
        ax.annotate(
            f"{arrow} {abs(pct):.1f}% vs prev week",
            xy=(0.98, 0.93), xycoords="axes fraction",
            ha="right", va="top",
            fontsize=8, color=clr, fontweight="bold",
        )

    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"RM {x:,.0f}")
    )
    ax.yaxis.grid(True, color=BRAND["grid"], linestyle="--", linewidth=0.6)
    ax.xaxis.grid(False)
    ax.tick_params(axis="x", rotation=10, labelsize=7.5)
    ax.set_title("Weekly Revenue — Paid/Closed Gov CRM Deals",
                 fontsize=9, color=BRAND["text"], pad=8, fontweight="bold")

    legend_patches = [
        mpatches.Patch(color=BRAND["yellow"], label="Current week"),
        mpatches.Patch(color=BRAND["teal"],   label="Prior weeks"),
    ]
    ax.legend(handles=legend_patches, fontsize=7.5, framealpha=0)
    fig.tight_layout(pad=0.6)
    return _save(fig)


# ── Lead status donut ─────────────────────────────────────────────────────────
def lead_status_donut(leads: list[dict]) -> bytes:
    """Donut with count AND % in legend labels (g)."""
    from collections import Counter
    counts = Counter(l.get("status") or "Unknown" for l in leads)
    if not counts:
        counts = {"No leads": 1}

    raw_labels = list(counts.keys())
    sizes      = list(counts.values())
    total      = sum(sizes)

    # g. Count + percentage in every legend label
    rich_labels = [
        f"{k}  ({v} · {v/total*100:.0f}%)"
        for k, v in counts.items()
    ]

    palette = [BRAND["teal"], BRAND["yellow"], BRAND["red"],
               "#8E44AD", "#2980B9", "#E67E22"]
    colors  = (palette * ((len(raw_labels) // len(palette)) + 1))[:len(raw_labels)]

    fig, ax = _base_ax((4.6, 3.0))
    wedges, _, autotexts = ax.pie(
        sizes, labels=None, colors=colors,
        autopct=lambda p: f"{p:.0f}%" if p > 7 else "",
        startangle=90, pctdistance=0.70,
        wedgeprops={"width": 0.52, "edgecolor": "white", "linewidth": 1.5},
    )
    for t in autotexts:
        t.set_fontsize(7.5)
        t.set_color(BRAND["text"])

    ax.legend(wedges, rich_labels, loc="lower center",
              bbox_to_anchor=(0.5, -0.22), ncol=1, fontsize=7, framealpha=0)
    ax.set_title(
        f"Lead Status Breakdown  (n={total})",
        fontsize=9, color=BRAND["text"], pad=4, fontweight="bold",
    )
    fig.tight_layout(pad=0.5)
    return _save(fig)


# ── Tier breakdown bar ────────────────────────────────────────────────────────
def tier_breakdown_bar(leads: list[dict], sessions: list[dict]) -> bytes:
    def counts(items):
        t1  = sum(1 for i in items if i.get("tier1"))
        std = len(items) - t1
        return t1, std

    l_t1, l_std = counts(leads)
    s_t1, s_std = counts(sessions)
    x      = np.arange(2)
    t1_vals  = [l_t1, s_t1]
    std_vals = [l_std, s_std]

    fig, ax = _base_ax((4.2, 2.8))
    ax.bar(x, t1_vals,  color=BRAND["yellow"], label="Tier 1",
           width=0.45, edgecolor="white")
    ax.bar(x, std_vals, color=BRAND["teal"],   label="Standard gov",
           width=0.45, bottom=t1_vals, edgecolor="white")

    ax.set_xticks(x)
    ax.set_xticklabels(["Incoming Leads", "Past Sessions"], fontsize=8)
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.yaxis.grid(True, color=BRAND["grid"], linestyle="--", linewidth=0.6)
    ax.xaxis.grid(False)
    ax.legend(fontsize=7.5, framealpha=0)
    ax.set_title("Gov Activity — Tier 1 vs Standard",
                 fontsize=9, color=BRAND["text"], pad=8, fontweight="bold")
    fig.tight_layout(pad=0.6)
    return _save(fig)


# ── CRM pipeline bar ──────────────────────────────────────────────────────────
def crm_pipeline_bar(deals: list[dict]) -> bytes:
    """Horizontal bars — only Paid, Closed, Proposal/Quotation stages. Lifetime data."""
    from collections import defaultdict

    by_stage = defaultdict(float)
    for d in deals:
        raw   = d.get("stage") or "Unknown"
        stage = _clean(raw)
        if _stage_ok(raw):
            by_stage[stage] += d.get("deal_value", 0) or 0

    if not by_stage:
        by_stage["No qualifying data"] = 0

    stages = sorted(by_stage, key=lambda s: by_stage[s], reverse=True)
    values = [by_stage[s] for s in stages]

    palette = [BRAND["teal"], BRAND["yellow"], BRAND["red"],
               "#2980B9", "#8E44AD"]
    colors  = (palette * ((len(stages) // len(palette)) + 1))[:len(stages)]

    fig_h = max(1.8, len(stages) * 0.65)
    fig, ax = _base_ax((7.5, fig_h))

    x_max = max(values) if max(values) > 0 else 1
    min_display = x_max * 0.015  # minimum visible bar width for tiny values
    display_values = [max(v, min_display) if v > 0 else 0 for v in values]

    bars = ax.barh(stages, display_values, color=colors, edgecolor="white",
                   linewidth=0.8, height=0.5)
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"RM {x:,.0f}")
    )
    ax.xaxis.grid(True, color=BRAND["grid"], linestyle="--", linewidth=0.6)
    ax.yaxis.grid(False)
    ax.tick_params(axis="x", labelsize=7.5)
    ax.tick_params(axis="y", labelsize=8.5)

    threshold = x_max * 0.12
    for bar, val, dval in zip(bars, values, display_values):
        if val <= 0:
            continue
        bar_w = dval
        if bar_w >= threshold:
            ax.text(x_max * 0.012, bar.get_y() + bar.get_height() / 2,
                    f"RM {val:,.0f}", va="center",
                    fontsize=7.5, color="white", fontweight="bold")
        else:
            ax.text(bar_w + x_max * 0.012, bar.get_y() + bar.get_height() / 2,
                    f"RM {val:,.0f}", va="center",
                    fontsize=7.5, color=BRAND["text"], fontweight="bold")

    ax.set_title(
        "Sales CRM — Value by Stage  ·  Lifetime (All Deals)",
        fontsize=9, color=BRAND["text"], pad=8, fontweight="bold",
    )
    fig.tight_layout(pad=0.6)
    return _save(fig)


# ── Simple revenue line chart (PDF use) ──────────────────────────────────────
def revenue_line_chart(weeks: list[dict]) -> bytes:
    """
    Clean, minimal line graph — no bars, no jargon.
    Each dot = one week's revenue. Labels show RM amount at each point.
    """
    if not weeks:
        return b""
    labels = [w["week_label"] for w in weeks]
    values = [w["total_revenue"] for w in weeks]
    n = len(labels)

    fig, ax = _base_ax((5.0, 2.8))
    ax.set_facecolor("#FAFAFA")
    fig.patch.set_facecolor("#FAFAFA")

    # Subtle horizontal reference line at 0
    ax.axhline(0, color="#CCCCCC", linewidth=0.8, zorder=1)

    # The line itself
    ax.plot(range(n), values, color=BRAND["teal"], linewidth=2.5,
            marker="o", markersize=8, markerfacecolor=BRAND["teal"],
            markeredgecolor="white", markeredgewidth=2, zorder=3, solid_capstyle="round")

    # Highlight current (last) point in yellow
    if n > 0:
        ax.plot(n-1, values[-1], "o", markersize=11,
                color=BRAND["yellow"], markeredgecolor="white",
                markeredgewidth=2, zorder=4)

    # Set y-axis: start at 0, leave 30% headroom above peak for labels
    y_max = max(values) if max(values) > 0 else 1000
    ax.set_ylim(0, y_max * 1.30)

    # Value labels above each dot
    for i, val in enumerate(values):
        ax.annotate(
            f"RM {val:,.0f}" if val > 0 else "RM 0",
            xy=(i, val), xytext=(0, 12),
            textcoords="offset points",
            ha="center", va="bottom",
            fontsize=8, color=BRAND["text"], fontweight="bold",
        )

    ax.set_xticks(range(n))
    ax.set_xticklabels(labels, fontsize=8.5, color=BRAND["text"])
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"RM {x:,.0f}"))
    ax.tick_params(axis="y", labelsize=7.5, colors="#888")
    ax.yaxis.grid(True, color="#EEEEEE", linewidth=0.6)
    ax.xaxis.grid(False)

    # Remove top/right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")

    # Current week annotation
    if n > 1:
        curr, prev = values[-1], values[-2]
        if prev > 0:
            pct = (curr - prev) / prev * 100
            arrow = "▲" if pct >= 0 else "▼"
            clr   = "#27AE60" if pct >= 0 else BRAND["red"]
            ax.annotate(
                f"{arrow} {abs(pct):.0f}% vs last week",
                xy=(0.99, 0.97), xycoords="axes fraction",
                ha="right", va="top", fontsize=8,
                color=clr, fontweight="bold",
            )

    ax.set_title("Weekly Revenue Collected",
                 fontsize=9, color=BRAND["text"], pad=12, fontweight="600")
    fig.tight_layout(pad=1.0)
    return _save(fig)


# ── Monthly revenue bar (full calendar year) ──────────────────────────────────
def monthly_revenue_bar(deals: list[dict], year: int = 2026,
                        current_month: int | None = None) -> bytes:
    """
    12-bar chart — one bar per month of `year`.
    Paid deals created (added) in `year`, bucketed by creation month —
    same definition as the YTD Revenue card, so the totals reconcile.
    Current month bar is highlighted yellow.
    """
    MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
              "Jul","Aug","Sep","Oct","Nov","Dec"]

    monthly = [0.0] * 12
    for d in deals:
        s = (d.get("stage") or "").lower()
        if "paid" not in s or "before adam" in s:  # Paid status only
            continue
        ad = d.get("added_date") or ""
        try:
            dt = datetime.strptime(ad[:10], "%Y-%m-%d")
            if dt.year == year:
                monthly[dt.month - 1] += d.get("deal_value", 0) or 0
        except ValueError:
            pass

    bar_colors = []
    for i, v in enumerate(monthly):
        if current_month and i + 1 == current_month:
            bar_colors.append(BRAND["yellow"])
        elif v > 0:
            bar_colors.append(BRAND["teal"])
        else:
            bar_colors.append("#DEDEDE")

    fig, ax = _base_ax((10.5, 3.0))
    bars = ax.bar(MONTHS, monthly, color=bar_colors, width=0.62,
                  edgecolor="white", linewidth=0.8, zorder=2)

    # Value labels above non-zero bars
    y_max = max(monthly) if max(monthly) > 0 else 1
    for bar, val in zip(bars, monthly):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2,
                    val + y_max * 0.02,
                    f"RM {val:,.0f}",
                    ha="center", va="bottom", fontsize=7.5,
                    color=BRAND["text"], fontweight="bold")

    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"RM {x:,.0f}")
    )
    ax.yaxis.grid(True, color=BRAND["grid"], linestyle="--", linewidth=0.6)
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)
    # Single Text artist with both lines — titles are always included in the
    # tight bbox on every matplotlib version (see the xlabel note below).
    ax.set_title(f"Monthly Revenue — {year}  (Paid deals added in {year})\n"
                 f"*For Canva, GenAI, and Google Workspace training",
                 fontsize=9, color=BRAND["text"], pad=8, fontweight="bold")

    patches = [
        mpatches.Patch(color=BRAND["yellow"], label="Current month — Paid deals"),
        mpatches.Patch(color=BRAND["teal"],   label=f"Paid deals (added in {year})"),
        mpatches.Patch(color="#DEDEDE",        label="No Paid deals"),
    ]
    ax.legend(handles=patches, fontsize=7.5, framealpha=0, loc="upper right")

    # Year total below the axis — matches the YTD Revenue card exactly,
    # since both count Paid deals created in `year`.
    # NOTE: use the x-axis LABEL, not an annotate() placed outside the axes.
    # An out-of-axes annotation is dropped by bbox_inches="tight" on some
    # matplotlib versions; xlabel is a first-class axis artist that every
    # version lays out below the tick labels and always includes.
    year_total = sum(monthly)
    n_months   = sum(1 for v in monthly if v > 0)
    ax.set_xlabel(
        f"Total {year}:  RM {year_total:,.0f}"
        f"   ·   across {n_months} month{'s' if n_months != 1 else ''}",
        fontsize=10, color=BRAND["teal"], fontweight="bold", labelpad=12,
    )
    ax.xaxis.label.set_bbox(dict(boxstyle="round,pad=0.45",
                                 facecolor="#E6F4F3",
                                 edgecolor=BRAND["teal"], linewidth=0.9))

    fig.tight_layout(pad=0.6)
    return _save(fig)


# ── Revenue dashboard: YoY vs target, growth, collection ──────────────────────
def revenue_dashboard(deals: list[dict], year: int = 2026,
                      monthly_target: float = 200_000,
                      current_month: int | None = None) -> bytes:
    """
    Three-panel revenue view, matching the Revenue tab's definitions:
      top    — grouped columns: prev-year actual vs expected vs actual + target
      bottom — YoY growth lines (expected & actual), and collection-rate bars

    Deals are bucketed by CREATION month.
      Expected = Paid + Closed (everything invoiced)
      Actual   = Paid only (money received)
    Collection rate is left BLANK, not 0%, where expected is zero — the
    ratio is undefined there and a 0% bar would read as a real shortfall.
    """
    from collections import defaultdict
    import matplotlib.gridspec as gridspec

    MONTHS = ["Jan","Feb","Mar","Apr","May","Jun",
              "Jul","Aug","Sep","Oct","Nov","Dec"]
    prev = year - 1

    def _low(d):  return (d.get("stage") or "").lower()
    def _paid(d): return "paid" in _low(d) and "before adam" not in _low(d)
    def _clsd(d): return "closed" in _low(d) and "before adam" not in _low(d)

    def _bucket(yr, pred):
        out = defaultdict(float)
        for d in deals:
            ad = d.get("added_date") or ""
            if len(ad) >= 7 and ad[:4] == str(yr) and pred(d):
                out[int(ad[5:7])] += d.get("deal_value", 0) or 0
        return [out[m] for m in range(1, 13)]

    a_prev = _bucket(prev, _paid)
    e_curr = _bucket(year, lambda d: _paid(d) or _clsd(d))
    a_curr = _bucket(year, _paid)

    cm = current_month or 12
    # Current-year series stop at the current month; later months have no data
    e_plot = [v if i < cm else np.nan for i, v in enumerate(e_curr)]
    a_plot = [v if i < cm else np.nan for i, v in enumerate(a_curr)]

    fig = plt.figure(figsize=(13.5, 7.2))
    fig.patch.set_facecolor(BRAND["bg"])
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.45, 1.0],
                           hspace=0.42, wspace=0.20)

    C_PREV = "#7F8FA6"          # neutral: last year is the baseline
    C_EXP  = BRAND["yellow"]    # invoiced but not necessarily collected
    C_ACT  = BRAND["teal"]      # money in

    def _style(ax):
        ax.set_facecolor(BRAND["bg"])
        for s in ax.spines.values():
            s.set_visible(False)
        ax.tick_params(colors=BRAND["text"], labelsize=8)
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color=BRAND["grid"], linestyle="--", linewidth=0.6)
        ax.xaxis.grid(False)

    # ── Panel 1: grouped columns ─────────────────────────────────
    ax1 = fig.add_subplot(gs[0, :]); _style(ax1)
    x = np.arange(12); w = 0.27
    ax1.bar(x - w, a_prev, w, label=f"FY{prev} actual", color=C_PREV,
            edgecolor="white", linewidth=0.6, zorder=2)
    ax1.bar(x,     e_plot, w, label=f"FY{year} expected", color=C_EXP,
            edgecolor="white", linewidth=0.6, zorder=2)
    ax1.bar(x + w, a_plot, w, label=f"FY{year} actual", color=C_ACT,
            edgecolor="white", linewidth=0.6, zorder=2)
    ax1.axhline(monthly_target, color="#8A8A8A", linestyle="--", linewidth=1.3, zorder=3)
    ax1.annotate(f"RM {monthly_target:,.0f} target",
                 xy=(0.995, monthly_target), xycoords=("axes fraction", "data"),
                 xytext=(0, 4), textcoords="offset points", ha="right", va="bottom",
                 fontsize=8, color="#6A6A6A", fontweight="bold")
    ax1.set_xticks(x); ax1.set_xticklabels(MONTHS, fontsize=8.5)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"RM {v:,.0f}"))
    ax1.set_title(f"Monthly Revenue — FY{prev} vs FY{year}  ·  deals by creation month",
                  fontsize=10, color=BRAND["text"], pad=10, fontweight="bold")
    ax1.legend(fontsize=8, framealpha=0, ncol=3, loc="upper right")

    # ── Panel 2: YoY growth lines ────────────────────────────────
    ax2 = fig.add_subplot(gs[1, 0]); _style(ax2)
    last_complete = cm - 1          # current month is only part-elapsed
    g_exp = [((e_curr[i] - a_prev[i]) / a_prev[i] * 100)
             if (a_prev[i] and i < last_complete) else np.nan for i in range(12)]
    g_act = [((a_curr[i] - a_prev[i]) / a_prev[i] * 100)
             if (a_prev[i] and i < last_complete) else np.nan for i in range(12)]
    ax2.axhline(0, color="#B0B0B0", linewidth=1)
    ax2.plot(x, g_exp, marker="o", markersize=4.5, linewidth=1.8,
             color=C_EXP, label="Expected")
    ax2.plot(x, g_act, marker="o", markersize=4.5, linewidth=1.8,
             color=C_ACT, label="Actual")
    ax2.set_xticks(x); ax2.set_xticklabels(MONTHS, fontsize=7.5)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}%"))
    ax2.set_title(f"Year-on-year growth vs FY{prev}",
                  fontsize=9, color=BRAND["text"], pad=8, fontweight="bold")
    ax2.legend(fontsize=7.5, framealpha=0, ncol=2)
    if 1 <= cm <= 12:
        ax2.annotate(f"excludes {MONTHS[cm-1]} — month still in progress",
                     xy=(0.99, 0.03), xycoords="axes fraction",
                     ha="right", va="bottom", fontsize=6.5, color="#8A8A8A")

    # ── Panel 3: collection rate ─────────────────────────────────
    ax3 = fig.add_subplot(gs[1, 1]); _style(ax3)
    # Undefined where nothing was invoiced — omitted, not drawn as 0%.
    coll = [(a_curr[i] / e_curr[i] * 100) if (i < cm and e_curr[i] > 0) else np.nan
            for i in range(12)]
    cols = [BRAND["red"] if (v == v and v < 50)
            else (BRAND["yellow"] if (v == v and v < 80) else BRAND["teal"])
            for v in coll]
    ax3.bar(x, coll, 0.6, color=cols, edgecolor="white", linewidth=0.6, zorder=2)
    for i, v in enumerate(coll):
        if v == v:
            ax3.text(i, v + 2.5, f"{v:.0f}%", ha="center", va="bottom",
                     fontsize=7, color=BRAND["text"], fontweight="bold")
    ax3.set_ylim(0, 112)
    ax3.set_xticks(x); ax3.set_xticklabels(MONTHS, fontsize=7.5)
    ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}%"))
    ax3.set_title("Collection rate  ·  actual ÷ expected",
                  fontsize=9, color=BRAND["text"], pad=8, fontweight="bold")
    ax3.annotate("blank = nothing invoiced yet", xy=(0.99, 0.03),
                 xycoords="axes fraction", ha="right", va="bottom",
                 fontsize=6.5, color=BRAND["muted"] if "muted" in BRAND else "#888888")

    return _save(fig)
