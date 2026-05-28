"""
Mock data module. Returns dicts in the exact Section 3 API shapes.

All complaint data is generated deterministically with a fixed seed so the
dashboard looks consistent across restarts. The hotspot clusters are defined
explicitly, with scatter complaints filling out the rest of the 130-complaint
dataset. Adjust CLUSTERS or NUM_SCATTER to change the seeded dataset.
"""

import random
from datetime import datetime, timedelta
from typing import Optional

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

NOW = datetime(2026, 5, 14, 10, 0, 0)

ZONES = ["Zone North", "Zone South", "Zone East", "Zone West", "Zone Central"]

ZONE_CENTERS: dict[str, tuple[float, float]] = {
    "Zone North": (13.052, 77.563),
    "Zone South": (12.872, 77.548),
    "Zone East": (12.961, 77.651),
    "Zone West": (12.981, 77.461),
    "Zone Central": (12.974, 77.578),
}

ZONE_WARDS: dict[str, list[str]] = {
    "Zone North": ["North-1", "North-2", "North-3"],
    "Zone South": ["South-1", "South-2"],
    "Zone East": ["East-1", "East-2", "East-3"],
    "Zone West": ["West-1", "West-2"],
    "Zone Central": ["Central-1", "Central-2", "Central-3"],
}

CATEGORIES = ["water", "sewage", "roads", "solid_waste", "trade_licence"]

CATEGORY_CODES: dict[str, str] = {
    "water": "WAT",
    "sewage": "SEW",
    "roads": "ROA",
    "solid_waste": "WAS",
    "trade_licence": "TRD",
}

SUB_CATEGORIES: dict[str, list[str]] = {
    "water": [
        "no_water_supply", "low_pressure", "contaminated_water",
        "pipeline_leak", "illegal_connection", "meter_billing",
    ],
    "sewage": [
        "sewage_overflow", "blocked_drain", "open_manhole",
        "sewage_backflow", "stormwater_flooding", "foul_smell",
    ],
    "roads": [
        "pothole", "damaged_surface", "dug_not_restored",
        "footpath_damage", "streetlight", "road_waterlogging", "signage_speedbreaker",
    ],
    "solid_waste": [
        "garbage_not_collected", "overflowing_bin", "open_dumping",
        "dead_animal", "debris_not_cleared", "irregular_pickup",
    ],
    "trade_licence": [
        "new_licence_process", "renewal_process", "application_status",
        "documents_required", "fee_clarification", "unlicensed_business",
    ],
}

STATUSES = ["filed", "assigned", "in_progress", "resolved", "escalated"]

SLA_HOURS: dict[str, int] = {
    "water": 24,
    "sewage": 24,
    "roads": 72,
    "solid_waste": 48,
    "trade_licence": 168,
}

DEPARTMENTS: dict[str, str] = {
    "water": "Water Supply Department",
    "sewage": "Sewage and Drainage Department",
    "roads": "Roads and Infrastructure Department",
    "solid_waste": "Solid Waste Management",
    "trade_licence": "Trade and Commerce Department",
}

# Kannada description templates per category
DESCRIPTIONS: dict[str, list[str]] = {
    "water": [
        "ನಮ್ಮ ಪ್ರದೇಶದಲ್ಲಿ ಮೂರು ದಿನಗಳಿಂದ ನೀರು ಸರಬರಾಜು ಇಲ್ಲ.",
        "ನಲ್ಲಿಯಲ್ಲಿ ನೀರಿನ ಒತ್ತಡ ತುಂಬಾ ಕಡಿಮೆ ಇದೆ.",
        "ರಸ್ತೆ ಮೇಲೆ ನೀರಿನ ಪೈಪ್ ಒಡೆದು ನೀರು ವ್ಯರ್ಥವಾಗುತ್ತಿದೆ.",
        "ಕುಡಿಯುವ ನೀರು ಕಂದು ಬಣ್ಣದಿಂದ ಬರುತ್ತಿದೆ, ಕೆಟ್ಟ ವಾಸನೆ ಇದೆ.",
    ],
    "sewage": [
        "ಚರಂಡಿ ತುಂಬಿ ಹೋಗಿದೆ, ನೀರು ರಸ್ತೆ ಮೇಲೆ ಹರಿಯುತ್ತಿದೆ.",
        "ಮ್ಯಾನ್‌ಹೋಲ್ ಮುಚ್ಚಳ ಮುರಿದು ಹೋಗಿದೆ, ದಾರಿ ಅಪಾಯಕರವಾಗಿದೆ.",
        "ಮನೆಯಲ್ಲಿ ಒಳಚರಂಡಿ ನೀರು ಮರಳಿ ಬರುತ್ತಿದೆ.",
        "ಚರಂಡಿಯಿಂದ ತುಂಬಾ ಕೆಟ್ಟ ವಾಸನೆ ಬರುತ್ತಿದೆ.",
    ],
    "roads": [
        "ರಸ್ತೆಯಲ್ಲಿ ದೊಡ್ಡ ಗುಂಡಿಗಳಿವೆ, ವಾಹನ ಓಡಿಸಲು ಕಷ್ಟವಾಗುತ್ತಿದೆ.",
        "ರಸ್ತೆ ಅಗೆದು ಬಿಟ್ಟಿದ್ದಾರೆ, ತಿಂಗಳು ಕಳೆದರೂ ಮುಚ್ಚಿಲ್ಲ.",
        "ಬೀದಿ ದೀಪ ಕೆಟ್ಟು ಹೋಗಿದೆ, ರಾತ್ರಿ ನಡೆದಾಡಲು ಭಯವಾಗುತ್ತದೆ.",
        "ರಸ್ತೆ ಮೇಲೆ ನೀರು ನಿಂತಿದೆ, ಓಡಾಟಕ್ಕೆ ತೊಂದರೆ.",
    ],
    "solid_waste": [
        "ಒಂದು ವಾರದಿಂದ ಕಸ ತೆಗೆದಿಲ್ಲ, ದುರ್ವಾಸನೆ ಬರುತ್ತಿದೆ.",
        "ಸಾರ್ವಜನಿಕ ಕಸದ ಬಕೆಟ್ ತುಂಬಿ ಹರಿಯುತ್ತಿದೆ.",
        "ಖಾಲಿ ಜಾಗದಲ್ಲಿ ಕಸ ಎಸೆಯುತ್ತಿದ್ದಾರೆ, ಸ್ವಚ್ಛಗೊಳಿಸಿ.",
        "ನಿರ್ಮಾಣ ಕೆಲಸದ ಅವಶೇಷಗಳನ್ನು ತೆಗೆದಿಲ್ಲ.",
    ],
    "trade_licence": [
        "ನಮ್ಮ ಅರ್ಜಿ ಮೂರು ತಿಂಗಳಿಂದ ಬಾಕಿ ಇದೆ, ಸ್ಥಿತಿ ತಿಳಿಸಿ.",
        "ಪರವಾನಗಿ ನವೀಕರಣಕ್ಕೆ ಏನೇನು ದಾಖಲೆ ಬೇಕು?",
        "ಪಕ್ಕದ ಅಂಗಡಿ ಪರವಾನಗಿ ಇಲ್ಲದೆ ವ್ಯಾಪಾರ ಮಾಡುತ್ತಿದೆ.",
        "ವ್ಯಾಪಾರ ಪರವಾನಗಿ ಶುಲ್ಕದ ಬಗ್ಗೆ ವಿವರಣೆ ಬೇಕಿದೆ.",
    ],
}

# Hotspot clusters: (zone, category, sub_category, lat, lon, count, recommendation)
CLUSTERS: list[tuple] = [
    (
        "Zone North", "roads", "pothole", 13.052, 77.563, 9,
        "Nine repeat pothole reports at this location in the past month. Road surface is failing. "
        "Schedule immediate inspection and full resurfacing to prevent further complaints and vehicle damage.",
    ),
    (
        "Zone South", "water", "pipeline_leak", 12.872, 77.548, 7,
        "Seven consecutive pipeline leak complaints near this junction. Temporary patching has not held. "
        "Replace the aging pipeline segment to stop water loss and prevent road damage.",
    ),
    (
        "Zone East", "sewage", "blocked_drain", 12.961, 77.651, 8,
        "Chronic drain blockage at this point over multiple months. Root cause is likely an undersized drain "
        "or encroachment. Inspect drain capacity and clear obstructions permanently.",
    ),
    (
        "Zone Central", "solid_waste", "overflowing_bin", 12.974, 77.578, 6,
        "Six overflowing bin complaints from this high-footfall location. Increase collection frequency "
        "to twice daily, or install a larger bin to match pedestrian traffic volume.",
    ),
    (
        "Zone West", "roads", "damaged_surface", 12.981, 77.461, 5,
        "Five road surface damage reports near this stretch. Poor drainage is causing sub-base erosion. "
        "Fix drainage first, then resurface to prevent immediate recurrence.",
    ),
    (
        "Zone North", "sewage", "open_manhole", 13.063, 77.571, 4,
        "Four open manhole reports in this area. Missing covers create a serious pedestrian safety hazard. "
        "Replace all covers with lockable anti-theft type immediately.",
    ),
]

NUM_SCATTER = 101  # total complaints = sum(CLUSTER counts) + NUM_SCATTER = 39 + 101 = 140

# ------------------------------------------------------------------
# Complaint generation
# ------------------------------------------------------------------

def _pick_status(rng: random.Random, age_days: int, is_cluster: bool) -> str:
    if is_cluster:
        return rng.choices(
            ["filed", "assigned", "in_progress", "escalated"],
            weights=[10, 20, 45, 25],
        )[0]
    if age_days > 30:
        return rng.choices(STATUSES, weights=[5, 10, 15, 55, 15])[0]
    if age_days > 7:
        return rng.choices(STATUSES, weights=[10, 20, 35, 25, 10])[0]
    return rng.choices(STATUSES, weights=[35, 30, 20, 5, 10])[0]


def _make_complaint(
    zone: str,
    category: str,
    sub_category: str,
    lat: float,
    lon: float,
    created_at: datetime,
    rng: random.Random,
    counter: dict,
    is_cluster: bool = False,
) -> dict:
    date_key = created_at.strftime("%Y%m%d")
    cat_key = f"{date_key}_{category}"
    counter[cat_key] = counter.get(cat_key, 0) + 1
    seq = counter[cat_key]

    complaint_id = f"KA-{CATEGORY_CODES[category]}-{date_key}-{seq:04d}"

    age_days = (NOW - created_at).days
    status = _pick_status(rng, age_days, is_cluster)
    priority = "high" if (is_cluster or rng.random() < 0.2) else "normal"

    sla_hours = SLA_HOURS[category]
    sla_due_at = created_at + timedelta(hours=sla_hours)
    sla_breached = sla_due_at < NOW and status not in ("resolved",)

    escalation_level = 0
    if status == "escalated":
        escalation_level = 2 if age_days > 14 else 1

    updated_at = created_at + timedelta(
        hours=rng.randint(1, min(age_days * 24, 120) or 1)
    )

    description_list = DESCRIPTIONS.get(category, ["ದೂರು ದಾಖಲಾಗಿದೆ."])
    description = rng.choice(description_list)

    ward_list = ZONE_WARDS[zone]
    ward = rng.choice(ward_list) if rng.random() > 0.1 else ""

    return {
        "complaint_id": complaint_id,
        "category": category,
        "sub_category": sub_category,
        "description": description,
        "citizen_phone": f"+91{rng.randint(7000000000, 9999999999)}",
        "zone": zone,
        "ward": ward,
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "status": status,
        "priority": priority,
        "created_at": created_at.isoformat(),
        "updated_at": updated_at.isoformat(),
        "sla_due_at": sla_due_at.isoformat(),
        "sla_breached": sla_breached,
        "escalation_level": escalation_level,
        "assigned_department": DEPARTMENTS[category],
        "language": "kn",
    }


def _generate_all() -> list[dict]:
    rng = random.Random(42)
    counter: dict[str, int] = {}
    complaints: list[dict] = []

    # Cluster complaints (these create the detectable hotspots)
    for zone, category, sub_cat, lat, lon, count, _ in CLUSTERS:
        for _ in range(count):
            age = rng.randint(1, 25)
            jitter_lat = lat + rng.uniform(-0.003, 0.003)
            jitter_lon = lon + rng.uniform(-0.003, 0.003)
            created_at = NOW - timedelta(days=age, hours=rng.randint(0, 23))
            c = _make_complaint(
                zone, category, sub_cat,
                jitter_lat, jitter_lon,
                created_at, rng, counter, is_cluster=True,
            )
            complaints.append(c)

    # Scatter complaints covering all zones and categories
    category_weights = [30, 20, 25, 15, 10]
    for _ in range(NUM_SCATTER):
        zone = rng.choice(ZONES)
        category = rng.choices(CATEGORIES, weights=category_weights)[0]
        sub_cat = rng.choice(SUB_CATEGORIES[category])
        base_lat, base_lon = ZONE_CENTERS[zone]
        lat = base_lat + rng.uniform(-0.04, 0.04)
        lon = base_lon + rng.uniform(-0.04, 0.04)
        age = rng.randint(1, 60)
        created_at = NOW - timedelta(days=age, hours=rng.randint(0, 23))
        c = _make_complaint(
            zone, category, sub_cat,
            lat, lon, created_at, rng, counter, is_cluster=False,
        )
        complaints.append(c)

    return complaints


# Generate once at import time
_ALL_COMPLAINTS: list[dict] = _generate_all()


def _filter_complaints(
    zone: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
) -> list[dict]:
    result = _ALL_COMPLAINTS
    if zone:
        result = [c for c in result if c["zone"] == zone]
    if category:
        result = [c for c in result if c["category"] == category]
    if status:
        result = [c for c in result if c["status"] == status]
    return result


# ------------------------------------------------------------------
# Public API-shaped getters
# ------------------------------------------------------------------

def get_summary(zone: Optional[str] = None, category: Optional[str] = None) -> dict:
    complaints = _filter_complaints(zone=zone, category=category)

    by_category: dict[str, int] = {cat: 0 for cat in CATEGORIES}
    by_status: dict[str, int] = {s: 0 for s in STATUSES}
    by_zone: dict[str, int] = {}
    sla_breached_count = 0
    escalated_count = 0

    for c in complaints:
        by_category[c["category"]] += 1
        by_status[c["status"]] = by_status.get(c["status"], 0) + 1
        by_zone[c["zone"]] = by_zone.get(c["zone"], 0) + 1
        if c["sla_breached"]:
            sla_breached_count += 1
        if c["status"] == "escalated":
            escalated_count += 1

    return {
        "total_complaints": len(complaints),
        "by_category": by_category,
        "by_status": by_status,
        "by_zone": by_zone,
        "sla_breached_count": sla_breached_count,
    }


def get_trends(days: int = 30, zone: Optional[str] = None, category: Optional[str] = None) -> dict:
    complaints = _filter_complaints(zone=zone, category=category)
    cutoff = NOW - timedelta(days=days)
    recent = [c for c in complaints if datetime.fromisoformat(c["created_at"]) >= cutoff]

    # Build a date -> category -> count map
    date_map: dict[str, dict[str, int]] = {}
    for c in recent:
        date_str = c["created_at"][:10]
        if date_str not in date_map:
            date_map[date_str] = {cat: 0 for cat in CATEGORIES}
        date_map[date_str][c["category"]] += 1

    # Fill every day in the range (even zero-complaint days)
    series = []
    for i in range(days):
        d = (cutoff + timedelta(days=i + 1)).strftime("%Y-%m-%d")
        row = {"date": d}
        row.update(date_map.get(d, {cat: 0 for cat in CATEGORIES}))
        series.append(row)

    return {"days": days, "series": series}


def get_hotspots(zone: Optional[str] = None, category: Optional[str] = None) -> dict:
    hotspots = []
    for zone_name, cat, sub_cat, lat, lon, count, recommendation in CLUSTERS:
        if zone and zone_name != zone:
            continue
        if category and cat != category:
            continue
        hotspots.append(
            {
                "category": cat,
                "sub_category": sub_cat,
                "latitude": lat,
                "longitude": lon,
                "complaint_count": count,
                "zone": zone_name,
                "recommendation": recommendation,
            }
        )
    # Sort worst first
    hotspots.sort(key=lambda h: h["complaint_count"], reverse=True)
    return {"hotspots": hotspots}


def get_complaints(
    zone: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
) -> list[dict]:
    return _filter_complaints(zone=zone, category=category, status=status)
