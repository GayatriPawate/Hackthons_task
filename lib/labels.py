"""Human-readable labels and colors for all categorical keys used in the dashboard."""

CATEGORY_LABELS: dict[str, str] = {
    "water": "Water Supply",
    "sewage": "Sewage & Drainage",
    "roads": "Roads & Infrastructure",
    "solid_waste": "Solid Waste",
    "trade_licence": "Trade Licence",
}

SUB_CATEGORY_LABELS: dict[str, str] = {
    # water
    "no_water_supply": "No water supply",
    "low_pressure": "Low water pressure",
    "contaminated_water": "Contaminated / dirty water",
    "pipeline_leak": "Pipeline leakage or burst",
    "illegal_connection": "Illegal water connection",
    "meter_billing": "Meter or billing issue",
    # sewage
    "sewage_overflow": "Sewage overflow on road",
    "blocked_drain": "Blocked or choked drain",
    "open_manhole": "Open / broken manhole",
    "sewage_backflow": "Sewage backflow into homes",
    "stormwater_flooding": "Stormwater drain flooding",
    "foul_smell": "Foul smell from drain",
    # roads
    "pothole": "Pothole",
    "damaged_surface": "Damaged road surface",
    "dug_not_restored": "Road dug, not restored",
    "footpath_damage": "Damaged footpath",
    "streetlight": "Streetlight not working",
    "road_waterlogging": "Waterlogging on road",
    "signage_speedbreaker": "Damaged speed breaker / signage",
    # solid_waste
    "garbage_not_collected": "Garbage not collected",
    "overflowing_bin": "Overflowing dustbin",
    "open_dumping": "Open / illegal dumping",
    "dead_animal": "Dead animal removal",
    "debris_not_cleared": "Construction debris not cleared",
    "irregular_pickup": "Irregular door-to-door pickup",
    # trade_licence
    "new_licence_process": "New licence application process",
    "renewal_process": "Licence renewal process",
    "application_status": "Application status query",
    "documents_required": "Documents required",
    "fee_clarification": "Fee / category clarification",
    "unlicensed_business": "Unlicensed business complaint",
}

STATUS_LABELS: dict[str, str] = {
    "filed": "Filed",
    "assigned": "Assigned",
    "in_progress": "In Progress",
    "resolved": "Resolved",
    "escalated": "Escalated",
}

PRIORITY_LABELS: dict[str, str] = {
    "normal": "Normal",
    "high": "High",
}

LANGUAGE_LABELS: dict[str, str] = {
    "kn": "Kannada",
    "kn-IN": "Kannada",
    "ta": "Tamil",
    "ta-IN": "Tamil",
    "en": "English",
    "en-IN": "English",
}

# Plotly / folium hex colors per category
CATEGORY_COLORS: dict[str, str] = {
    "water": "#3B82F6",
    "sewage": "#8B5CF6",
    "roads": "#F59E0B",
    "solid_waste": "#10B981",
    "trade_licence": "#F97316",
}

STATUS_COLORS: dict[str, str] = {
    "filed": "#6B7280",
    "assigned": "#3B82F6",
    "in_progress": "#F59E0B",
    "resolved": "#10B981",
    "escalated": "#EF4444",
}

CATEGORIES: list[str] = list(CATEGORY_LABELS.keys())

STATUSES: list[str] = list(STATUS_LABELS.keys())

ESCALATION_BADGE: dict[int, str] = {
    0: "",
    1: "Zonal Officer",
    2: "Commissioner",
}
