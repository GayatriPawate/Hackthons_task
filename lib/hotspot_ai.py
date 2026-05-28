"""
AI-based chronic hotspot identification using DBSCAN spatial clustering.

Algorithm:
1. DBSCAN clusters complaints by GPS coordinates (eps ~300 m).
2. Each cluster is scored on four signals:
   - complaint_frequency  : total complaints in cluster
   - recurrence_rate      : fraction of days in window that had >= 1 complaint
   - sla_breach_rate      : fraction of complaints that breached SLA
   - unresolved_rate      : fraction not in resolved/escalated
3. Scores are normalised 0-1 and combined into a weighted severity_score.
4. Severity is labelled Critical / High / Medium based on thresholds.
5. A rule-based recommendation is generated from the dominant sub-category
   and the signals that are highest for that cluster.
"""

from __future__ import annotations

import math
from collections import Counter
from datetime import datetime
from typing import Optional

import numpy as np

SEVERITY_WEIGHTS = {
    "complaint_frequency": 0.35,
    "recurrence_rate": 0.30,
    "sla_breach_rate": 0.20,
    "unresolved_rate": 0.15,
}

# Minimum complaints for a cluster to be reported
MIN_CLUSTER_SIZE = 3

# DBSCAN radius in degrees (~300 m at Karnataka latitude)
DBSCAN_EPS_DEG = 0.003

# Severity thresholds (on 0-1 score)
CRITICAL_THRESHOLD = 0.70
HIGH_THRESHOLD = 0.45

_RECOMMENDATIONS: dict[str, dict[str, str]] = {
    "water": {
        "no_water_supply": "Install a dedicated supply line or pressure booster for this locality.",
        "low_pressure": "Audit pipeline diameter and elevation; replace undersized sections.",
        "contaminated_water": "Flush and chlorinate the local main; inspect for cross-connections.",
        "pipeline_leak": "Replace the aging pipeline segment — patch repairs have not held.",
        "illegal_connection": "Conduct a meter audit and seal unauthorized taps in this ward.",
        "meter_billing": "Deploy a meter inspection team; reset faulty meters within 7 days.",
        "default": "Escalate to Water Supply Department for infrastructure audit of this cluster.",
    },
    "sewage": {
        "sewage_overflow": "Desilt and expand the drain carrying capacity at this junction.",
        "blocked_drain": "Clear root/debris obstruction; inspect drain diameter for undersizing.",
        "open_manhole": "Replace all covers with lockable anti-theft type immediately — pedestrian hazard.",
        "sewage_backflow": "Install non-return valves on the feeder line serving this block.",
        "stormwater_flooding": "Build a retention bund or connect to the stormwater network.",
        "foul_smell": "Power-jet clean the drain and apply lime treatment to suppress odour.",
        "default": "Dispatch Sewage and Drainage team for structural inspection and desilting.",
    },
    "roads": {
        "pothole": "Schedule full-depth reclamation and resurfacing — patch fills have failed repeatedly.",
        "damaged_surface": "Fix sub-base drainage first, then apply bituminous overlay.",
        "dug_not_restored": "Issue contractor penalty notice; enforce road-cut restoration within 48 h.",
        "footpath_damage": "Rebuild footpath with interlocking tiles; clear encroachments.",
        "streetlight": "Replace MCB or faulty ballast; consider LED retrofit for entire stretch.",
        "road_waterlogging": "Clear blocked side drains and regrade road camber to drain runoff.",
        "signage_speedbreaker": "Reinstall signage to IRC standards; rebuild speed breaker to spec.",
        "default": "Raise a roads infrastructure inspection order for this cluster.",
    },
    "solid_waste": {
        "garbage_not_collected": "Increase collection frequency or add a secondary route for this ward.",
        "overflowing_bin": "Replace bin with larger capacity or add a second bin at this location.",
        "open_dumping": "Install surveillance camera and fine repeat offenders; clear site.",
        "dead_animal": "Coordinate with veterinary unit for same-day removal protocol.",
        "debris_not_cleared": "Issue notice to construction owner; clear debris within 24 h.",
        "irregular_pickup": "Reroute the collection vehicle or adjust timing to match resident schedules.",
        "default": "Deploy Solid Waste Management inspection team to this cluster.",
    },
    "trade_licence": {
        "unlicensed_business": "Schedule an enforcement drive; issue notices to all unlicensed establishments.",
        "default": "Assign a Trade and Commerce officer to address the backlog in this area.",
    },
}


def _recommendation(category: str, dominant_sub: str) -> str:
    cat_map = _RECOMMENDATIONS.get(category, {})
    return cat_map.get(dominant_sub, cat_map.get("default", "Refer to the relevant department for investigation."))


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _zone_based_clusters(filtered: list[dict]) -> dict[int, list[dict]]:
    """Fallback: group by zone+category when GPS coords are absent."""
    from collections import defaultdict
    groups: dict[tuple, list] = defaultdict(list)
    for c in filtered:
        groups[(c.get("zone", ""), c.get("category", ""))].append(c)
    # Only keep groups with at least MIN_CLUSTER_SIZE complaints
    return {
        i: members
        for i, (_, members) in enumerate(groups.items())
        if len(members) >= MIN_CLUSTER_SIZE
    }


def identify_chronic_hotspots(
    complaints: list[dict],
    days_window: int = 60,
    zone: Optional[str] = None,
    category: Optional[str] = None,
) -> list[dict]:
    """
    Identify chronic hotspots using DBSCAN (GPS) or zone-level grouping (fallback).

    Each returned dict has:
        cluster_id, category, sub_category, zone, latitude, longitude,
        complaint_count, recurrence_rate, sla_breach_rate, unresolved_rate,
        severity_score, severity_label, recommendation, top_complaints (list)
    """
    now = datetime.utcnow()

    # Filter to window and optional filters
    filtered: list[dict] = []
    for c in complaints:
        try:
            ts = datetime.fromisoformat(c["created_at"])
        except (KeyError, ValueError):
            continue
        if (now - ts).days > days_window:
            continue
        if zone and c.get("zone") != zone:
            continue
        if category and c.get("category") != category:
            continue
        filtered.append(c)

    if len(filtered) < MIN_CLUSTER_SIZE:
        return []

    # Separate into complaints with and without GPS
    with_coords = [c for c in filtered if c.get("latitude") is not None and c.get("longitude") is not None]
    without_coords = [c for c in filtered if c.get("latitude") is None or c.get("longitude") is None]

    clusters: dict[int, list[dict]] = {}

    # GPS clustering via DBSCAN
    if len(with_coords) >= MIN_CLUSTER_SIZE:
        from sklearn.cluster import DBSCAN
        coords = np.array([[c["latitude"], c["longitude"]] for c in with_coords])
        eps_rad = DBSCAN_EPS_DEG * (math.pi / 180)
        db = DBSCAN(eps=eps_rad, min_samples=MIN_CLUSTER_SIZE, algorithm="ball_tree", metric="haversine")
        labels = db.fit_predict(np.radians(coords))
        for label, complaint in zip(labels, with_coords):
            if label == -1:
                continue
            clusters.setdefault(label, []).append(complaint)

    # Zone-level fallback for complaints without GPS (or when DBSCAN finds nothing)
    if not clusters:
        clusters = _zone_based_clusters(filtered)
    elif without_coords:
        # Merge no-coord complaints into existing zone clusters where possible
        zone_cat_to_cluster: dict[tuple, int] = {}
        for cid, members in clusters.items():
            top_zone = Counter(m.get("zone") for m in members).most_common(1)[0][0]
            top_cat = Counter(m.get("category") for m in members).most_common(1)[0][0]
            zone_cat_to_cluster[(top_zone, top_cat)] = cid
        for c in without_coords:
            key = (c.get("zone", ""), c.get("category", ""))
            if key in zone_cat_to_cluster:
                clusters[zone_cat_to_cluster[key]].append(c)

    if not clusters:
        return []

    # Score each cluster
    all_counts = [len(v) for v in clusters.values()]
    max_count = max(all_counts) or 1

    hotspots: list[dict] = []

    for cluster_id, members in clusters.items():
        count = len(members)

        # Dominant category and sub-category
        cat_counts = Counter(m["category"] for m in members)
        dominant_cat = cat_counts.most_common(1)[0][0]
        sub_counts = Counter(m["sub_category"] for m in members if m.get("category") == dominant_cat)
        dominant_sub = sub_counts.most_common(1)[0][0] if sub_counts else "unknown"

        # Dominant zone
        zone_counts = Counter(m["zone"] for m in members)
        dominant_zone = zone_counts.most_common(1)[0][0]

        # Centroid — use GPS where available, else fall back to zone centre
        _ZONE_CENTERS = {
            "Zone North":   (13.052, 77.563),
            "Zone South":   (12.872, 77.548),
            "Zone East":    (12.961, 77.651),
            "Zone West":    (12.981, 77.461),
            "Zone Central": (12.974, 77.578),
        }
        coords_members = [m for m in members if m.get("latitude") is not None and m.get("longitude") is not None]
        if coords_members:
            centroid_lat = round(sum(m["latitude"] for m in coords_members) / len(coords_members), 6)
            centroid_lon = round(sum(m["longitude"] for m in coords_members) / len(coords_members), 6)
        else:
            fallback = _ZONE_CENTERS.get(dominant_zone, (12.974, 77.578))
            centroid_lat, centroid_lon = fallback

        # Recurrence: unique days with at least one complaint / days_window
        unique_days = len({m["created_at"][:10] for m in members})
        recurrence_rate = round(unique_days / days_window, 3)

        # SLA breach rate
        sla_count = sum(1 for m in members if m.get("sla_breached"))
        sla_breach_rate = round(sla_count / count, 3)

        # Unresolved rate
        unresolved = sum(1 for m in members if m.get("status") not in ("resolved",))
        unresolved_rate = round(unresolved / count, 3)

        # Frequency score (normalised to max cluster size)
        freq_score = count / max_count

        # Weighted severity score
        severity_score = round(
            SEVERITY_WEIGHTS["complaint_frequency"] * freq_score
            + SEVERITY_WEIGHTS["recurrence_rate"] * recurrence_rate
            + SEVERITY_WEIGHTS["sla_breach_rate"] * sla_breach_rate
            + SEVERITY_WEIGHTS["unresolved_rate"] * unresolved_rate,
            3,
        )

        if severity_score >= CRITICAL_THRESHOLD:
            severity_label = "Critical"
            badge_color = "#EF4444"
        elif severity_score >= HIGH_THRESHOLD:
            severity_label = "High"
            badge_color = "#F59E0B"
        else:
            severity_label = "Medium"
            badge_color = "#3B82F6"

        recommendation = _recommendation(dominant_cat, dominant_sub)

        # Most recent 3 complaint IDs for reference
        sorted_members = sorted(members, key=lambda m: m["created_at"], reverse=True)
        top_ids = [m["complaint_id"] for m in sorted_members[:3]]

        hotspots.append(
            {
                "cluster_id": int(cluster_id),
                "category": dominant_cat,
                "sub_category": dominant_sub,
                "zone": dominant_zone,
                "latitude": centroid_lat,
                "longitude": centroid_lon,
                "complaint_count": count,
                "unique_days_active": unique_days,
                "recurrence_rate": recurrence_rate,
                "sla_breach_rate": sla_breach_rate,
                "unresolved_rate": unresolved_rate,
                "severity_score": severity_score,
                "severity_label": severity_label,
                "badge_color": badge_color,
                "recommendation": recommendation,
                "recent_complaint_ids": top_ids,
                "category_counts": dict(cat_counts),
            }
        )

    # Sort by severity score descending
    hotspots.sort(key=lambda h: h["severity_score"], reverse=True)
    return hotspots
