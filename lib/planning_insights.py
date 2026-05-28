"""
Data-driven preventive planning insights.

Analyses complaint patterns from live data to produce ranked investment
priorities for city officials — no external AI API required.

Scoring model (per zone × category pair):
  volume_score      : complaint count normalised to max across all pairs
  sla_breach_score  : fraction of complaints with SLA breached
  unresolved_score  : fraction not in resolved/escalated
  recurrence_score  : unique active days / days_window
  priority_score    : weighted sum of the above four signals
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Optional

WEIGHTS = {
    "volume":     0.35,
    "recurrence": 0.30,
    "sla_breach": 0.20,
    "unresolved": 0.15,
}

RISK_THRESHOLDS = {"Critical": 0.65, "High": 0.40, "Medium": 0.0}

_ACTIONS: dict[str, dict[str, str]] = {
    "water": {
        "no_water_supply":    "Install a dedicated supply line or pressure booster for this locality.",
        "low_pressure":       "Audit pipeline diameter and elevation; replace undersized sections.",
        "contaminated_water": "Flush and chlorinate the local main; inspect for cross-connections.",
        "pipeline_leak":      "Replace the aging pipeline segment — patch repairs have not held.",
        "illegal_connection": "Conduct a meter audit and seal unauthorized taps in this ward.",
        "meter_billing":      "Deploy a meter inspection team; reset faulty meters within 7 days.",
        "_default":           "Escalate to Water Supply Department for infrastructure audit.",
    },
    "sewage": {
        "sewage_overflow":     "Desilt and expand drain carrying capacity at this junction.",
        "blocked_drain":       "Clear root/debris obstruction; inspect drain for undersizing.",
        "open_manhole":        "Replace all covers with lockable anti-theft type immediately.",
        "sewage_backflow":     "Install non-return valves on the feeder line serving this block.",
        "stormwater_flooding": "Build a retention bund or connect to the stormwater network.",
        "foul_smell":          "Power-jet clean the drain and apply lime treatment.",
        "_default":            "Dispatch Sewage and Drainage team for structural inspection.",
    },
    "roads": {
        "pothole":              "Schedule full-depth reclamation and resurfacing.",
        "damaged_surface":      "Fix sub-base drainage first, then apply bituminous overlay.",
        "dug_not_restored":     "Issue contractor penalty notice; enforce restoration within 48 h.",
        "footpath_damage":      "Rebuild footpath with interlocking tiles; clear encroachments.",
        "streetlight":          "Replace MCB or faulty ballast; consider LED retrofit for entire stretch.",
        "road_waterlogging":    "Clear blocked side drains and regrade road camber.",
        "signage_speedbreaker": "Reinstall signage to IRC standards; rebuild speed breaker to spec.",
        "_default":             "Raise a Roads Infrastructure inspection order for this cluster.",
    },
    "solid_waste": {
        "garbage_not_collected": "Increase collection frequency or add a secondary route.",
        "overflowing_bin":       "Replace bin with larger capacity or add a second bin.",
        "open_dumping":          "Install surveillance camera and fine repeat offenders; clear site.",
        "dead_animal":           "Coordinate with veterinary unit for same-day removal protocol.",
        "debris_not_cleared":    "Issue notice to construction owner; clear debris within 24 h.",
        "irregular_pickup":      "Reroute collection vehicle or adjust timing to match residents.",
        "_default":              "Deploy Solid Waste Management inspection team.",
    },
    "trade_licence": {
        "unlicensed_business": "Schedule enforcement drive; issue notices to unlicensed establishments.",
        "_default":            "Assign Trade and Commerce officer to address backlog in this area.",
    },
}

QUICK_WIN_SUBCATS = {
    "open_manhole", "dead_animal", "dug_not_restored",
    "streetlight", "overflowing_bin", "garbage_not_collected",
}
LONG_TERM_CATS = {"water", "sewage", "roads"}


def _action(category: str, sub_category: str) -> str:
    cat = _ACTIONS.get(category, {})
    return cat.get(sub_category, cat.get("_default", "Refer to the relevant department."))


def compute_preventive_insights(
    complaints: list[dict],
    days_window: int = 60,
    zone: Optional[str] = None,
    category: Optional[str] = None,
) -> dict:
    """
    Returns a structured insights dict:
      priority_areas  : list[dict] — ranked zone×category investment areas
      zone_risk       : dict[str, dict] — risk score + dominant issue per zone
      category_risk   : dict[str, dict] — risk score per category
      trend           : dict — rising / stable / declining per category
      quick_wins      : list[str]
      long_term       : list[str]
      kpis            : dict — summary numbers
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(days=days_window)

    # Filter
    filtered = []
    for c in complaints:
        try:
            ts = datetime.fromisoformat(c["created_at"])
        except (KeyError, ValueError):
            continue
        if ts < cutoff:
            continue
        if zone and c.get("zone") != zone:
            continue
        if category and c.get("category") != category:
            continue
        filtered.append(c)

    if not filtered:
        return {"empty": True}

    # ── Zone × Category matrix ────────────────────────────────────────
    pair_complaints: dict[tuple, list] = defaultdict(list)
    for c in filtered:
        pair_complaints[(c["zone"], c["category"])].append(c)

    max_count = max(len(v) for v in pair_complaints.values()) or 1

    scored_pairs = []
    for (z, cat), members in pair_complaints.items():
        n = len(members)
        unique_days = len({m["created_at"][:10] for m in members})
        sla_n = sum(1 for m in members if m.get("sla_breached"))
        unres_n = sum(1 for m in members if m.get("status") not in ("resolved", "escalated"))
        sub_counts = Counter(m.get("sub_category", "") for m in members)
        dominant_sub = sub_counts.most_common(1)[0][0] if sub_counts else ""

        vol_s = n / max_count
        rec_s = min(unique_days / max(days_window, 1), 1.0)
        sla_s = sla_n / n
        unr_s = unres_n / n

        score = round(
            WEIGHTS["volume"] * vol_s
            + WEIGHTS["recurrence"] * rec_s
            + WEIGHTS["sla_breach"] * sla_s
            + WEIGHTS["unresolved"] * unr_s,
            3,
        )

        risk = "Critical" if score >= RISK_THRESHOLDS["Critical"] else \
               "High"     if score >= RISK_THRESHOLDS["High"]     else "Medium"

        scored_pairs.append({
            "zone":         z,
            "category":     cat,
            "sub_category": dominant_sub,
            "count":        n,
            "unique_days":  unique_days,
            "sla_breach_rate":  round(sla_n / n, 3),
            "unresolved_rate":  round(unres_n / n, 3),
            "recurrence_rate":  round(unique_days / max(days_window, 1), 3),
            "priority_score":   score,
            "risk":             risk,
            "action":           _action(cat, dominant_sub),
            "is_quick_win":     dominant_sub in QUICK_WIN_SUBCATS,
            "is_long_term":     cat in LONG_TERM_CATS and n >= 3,
            "sub_counts":       dict(sub_counts),
        })

    scored_pairs.sort(key=lambda x: x["priority_score"], reverse=True)

    # ── Zone risk rollup ──────────────────────────────────────────────
    zone_data: dict[str, list] = defaultdict(list)
    for c in filtered:
        zone_data[c["zone"]].append(c)

    zone_risk: dict[str, dict] = {}
    max_zone_count = max(len(v) for v in zone_data.values()) or 1
    for z, members in zone_data.items():
        n = len(members)
        sla_n = sum(1 for m in members if m.get("sla_breached"))
        unres_n = sum(1 for m in members if m.get("status") not in ("resolved", "escalated"))
        unique_days = len({m["created_at"][:10] for m in members})
        top_cat = Counter(m["category"] for m in members).most_common(1)[0][0]
        top_sub = Counter(m.get("sub_category", "") for m in members).most_common(1)[0][0]

        vol_s = n / max_zone_count
        rec_s = min(unique_days / max(days_window, 1), 1.0)
        sla_s = sla_n / n
        unr_s = unres_n / n
        score = round(
            WEIGHTS["volume"] * vol_s + WEIGHTS["recurrence"] * rec_s
            + WEIGHTS["sla_breach"] * sla_s + WEIGHTS["unresolved"] * unr_s,
            3,
        )
        risk = "Critical" if score >= RISK_THRESHOLDS["Critical"] else \
               "High"     if score >= RISK_THRESHOLDS["High"]     else "Medium"
        zone_risk[z] = {
            "score": score, "risk": risk, "count": n,
            "sla_breach_rate": round(sla_n / n, 3),
            "unresolved_rate": round(unres_n / n, 3),
            "top_category": top_cat, "top_sub_category": top_sub,
        }

    # ── Category risk rollup ─────────────────────────────────────────
    cat_data: dict[str, list] = defaultdict(list)
    for c in filtered:
        cat_data[c["category"]].append(c)

    category_risk: dict[str, dict] = {}
    max_cat_count = max(len(v) for v in cat_data.values()) or 1
    for cat, members in cat_data.items():
        n = len(members)
        sla_n = sum(1 for m in members if m.get("sla_breached"))
        unres_n = sum(1 for m in members if m.get("status") not in ("resolved", "escalated"))
        unique_days = len({m["created_at"][:10] for m in members})
        top_sub = Counter(m.get("sub_category", "") for m in members).most_common(1)[0][0]
        vol_s = n / max_cat_count
        rec_s = min(unique_days / max(days_window, 1), 1.0)
        sla_s = sla_n / n
        unr_s = unres_n / n
        score = round(
            WEIGHTS["volume"] * vol_s + WEIGHTS["recurrence"] * rec_s
            + WEIGHTS["sla_breach"] * sla_s + WEIGHTS["unresolved"] * unr_s,
            3,
        )
        risk = "Critical" if score >= RISK_THRESHOLDS["Critical"] else \
               "High"     if score >= RISK_THRESHOLDS["High"]     else "Medium"
        category_risk[cat] = {
            "score": score, "risk": risk, "count": n,
            "sla_breach_rate": round(sla_n / n, 3),
            "unresolved_rate": round(unres_n / n, 3),
            "top_sub_category": top_sub,
        }

    # ── Trend: last 14 days vs 14–28 days ───────────────────────────
    mid = now - timedelta(days=14)
    recent_cats: Counter = Counter()
    older_cats: Counter = Counter()
    for c in filtered:
        ts = datetime.fromisoformat(c["created_at"])
        if ts >= mid:
            recent_cats[c["category"]] += 1
        else:
            older_cats[c["category"]] += 1

    trend: dict[str, str] = {}
    all_cats = set(list(recent_cats.keys()) + list(older_cats.keys()))
    for cat in all_cats:
        r, o = recent_cats.get(cat, 0), older_cats.get(cat, 0)
        if o == 0:
            trend[cat] = "New" if r > 0 else "Stable"
        elif r > o * 1.25:
            trend[cat] = "Rising"
        elif r < o * 0.75:
            trend[cat] = "Declining"
        else:
            trend[cat] = "Stable"

    # ── Quick wins and long-term investments ─────────────────────────
    seen_actions: set = set()
    quick_wins: list[str] = []
    long_term: list[str] = []

    for pair in scored_pairs:
        action_txt = pair["action"]
        if action_txt in seen_actions:
            continue
        seen_actions.add(action_txt)
        if pair["is_quick_win"]:
            quick_wins.append(f"{pair['zone']} / {pair['category'].replace('_', ' ').title()}: {action_txt}")
        if pair["is_long_term"] and len(long_term) < 5:
            long_term.append(f"{pair['zone']} / {pair['category'].replace('_', ' ').title()}: {action_txt}")

    # ── KPIs ─────────────────────────────────────────────────────────
    total = len(filtered)
    resolved = sum(1 for c in filtered if c.get("status") == "resolved")
    sla_total = sum(1 for c in filtered if c.get("sla_breached"))
    escalated = sum(1 for c in filtered if c.get("status") == "escalated")

    return {
        "empty": False,
        "priority_areas": scored_pairs[:10],
        "zone_risk": zone_risk,
        "category_risk": category_risk,
        "trend": trend,
        "quick_wins": quick_wins[:5],
        "long_term": long_term[:5],
        "kpis": {
            "total": total,
            "resolved": resolved,
            "sla_breached": sla_total,
            "escalated": escalated,
            "resolution_rate": round(resolved / total * 100, 1) if total else 0,
            "sla_breach_rate": round(sla_total / total * 100, 1) if total else 0,
            "days_window": days_window,
        },
        "top_pair": scored_pairs[0] if scored_pairs else None,
    }
