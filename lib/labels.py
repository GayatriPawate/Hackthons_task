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


def _current_language() -> str:
    """Return the currently selected UI language code ('kn', 'en', or 'bi').

    Falls back to 'kn' when Streamlit session state is not available (e.g. tests).
    """
    try:
        import streamlit as st  # local import keeps labels usable outside Streamlit
        return st.session_state.get("ui_language", "kn")
    except Exception:
        return "kn"


def bilingual_text(kannada_text: str, english_text: str) -> str:
    """Render text honoring the selected UI language.

    - 'kn'  -> Kannada only
    - 'en'  -> English only
    - 'bi'  -> "Kannada (English)"
    """
    lang = _current_language()
    if lang == "en":
        return english_text or kannada_text
    if lang == "bi":
        if not kannada_text:
            return english_text
        if not english_text:
            return kannada_text
        return f"{kannada_text} ({english_text})"
    # default: kn
    return kannada_text or english_text


UI_TEXTS: dict[str, tuple[str, str]] = {
    "app_title": ("ಕರ್ನಾಟಕ ಮುನ್ಸಿಪಲ್ ನಗರ ವಿಶ್ಲೇಷಣಾ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್", "Karnataka Municipal Urban Analytics Dashboard"),
    "app_caption": ("ಎಲ್ಲಾ ಟ್ಯಾಬ್‌ಗಳಲ್ಲಿಯೂ ತ್ವರಿತ ಒಳನೋಟಕ್ಕಾಗಿ ಫಿಲ್ಟರ್‌ಗಳನ್ನು ಬಳಸಿ.", "Use the filters to sharpen the view across all tabs."),
    "current_filters": ("ಪ್ರಸ್ತುತ ಫಿಲ್ಟರ್‌ಗಳು", "Current filters"),
    "filter_by_zone": ("ವಲಯದಿಂದ ಫಿಲ್ಟರ್ ಮಾಡಿ", "Filter by Zone"),
    "filter_by_category": ("ವರ್ಗದಿಂದ ಫಿಲ್ಟರ್ ಮಾಡಿ", "Filter by Category"),
    "all_zones": ("ಎಲ್ಲಾ ವಲಯಗಳು", "All Zones"),
    "all_categories": ("ಎಲ್ಲಾ ವರ್ಗಗಳು", "All Categories"),
    "refresh_data": ("ಡೇಟಾವನ್ನು تازهಗೊಳಿಸಿ", "Refresh Data"),
    "loading_data": ("ಡೇಟಾವನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...", "Loading data..."),
    "mock_mode": ("ಮಾಕ್ ಮೋಡ್ — ಡೇಟಾ ಅನುಕರಿಸಲಾಗಿದೆ.", "Mock mode — data is simulated."),
    "live_api": ("ಲೈವ್ API", "Live API"),
    "overview_title": ("ಒಮ್ಮೆ ನೋಡಿದಾಗಿನ ನಗರ ದೃಶ್ಯ", "City at a Glance"),
    "overview_caption": ("ಪ್ರತಿ 60 ಸೆಕೆಂಡ್ಗಳಿಗೊಮ್ಮೆ ನವೀಕರಣವಾಗುತ್ತದೆ.", "Updated every 60 seconds."),
    "analytics_title": ("ವಲಯಾಂತರ ವಿಶ್ಲೇಷಣೆ", "Cross-Zone Analytics"),
    "hotspot_title": ("ದೀರ್ಘಕಾಲೀನ ಸಮಸ್ಯೆಯ ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗಳು", "Chronic Problem Hotspots"),
    "hotspot_caption": ("ಪ್ರತಿ ದೂರು ಒಂದೊಂದು ಬಿಂದುವಾಗಿ ತೋರಿಸಲಾಗುತ್ತದೆ.", "Each complaint is shown as a separate dot."),
    "planning_title": ("ಪೂರ್ವಸಿದ್ಧತಾ ಯೋಜನಾ ಒಳನೋಟಗಳು", "Preventive Planning Insights"),
    "planning_caption": ("ದೂರು ಮಾದರಿಗಳ ಆಧಾರದ ಮೇಲೆ ಮೂಲಸೌಕರ್ಯ ಹೂಡಿಕೆಗೆ ವಿಶ್ಲೇಷಣೆ.", "Data-driven analysis of complaint patterns to prioritise preventive infrastructure investment."),
    "hotspot_ai_title": ("AI ದೀರ್ಘಕಾಲೀನ ಹಾಟ್‌ಸ್ಪಾಟ್ ವಿಶ್ಲೇಷಣೆ", "AI Chronic Hotspot Analysis"),
    "tracker_title": ("ದೂರು ಟ್ರ್ಯಾಕರ್ ಮತ್ತು ಆಡಳಿತ ನಿರ್ವಹಣೆ", "Complaint Tracker & Admin Management"),
    "tracker_caption": ("ದೂರು ಆಯ್ಕೆ ಮಾಡಿ, ಪ್ರಗತಿ ನವೀಕರಿಸಿ, ಪರಿಹರಿಸಿ ಅಥವಾ ಎಸ್ಕಲೇಟ್ ಮಾಡಿ.", "Select any complaint to view its live tracking timeline and take admin actions."),
    "complaints_title": ("ದೂರುಗಳ ಪಟ್ಟಿ", "Complaints"),
    "complaints_caption": ("ಎಲ್ಲಾ ದೂರುಗಳನ್ನು ಫಿಲ್ಟರ್ ಮಾಡಿ ಮತ್ತು ವಿವರಗಳನ್ನು ವೀಕ್ಷಿಸಿ.", "Filter and review all complaint records."),
    "complaint_language": ("ದೂರಿನ ಭಾಷೆ", "Complaint language"),
    "select_complaint_id": ("ದೂರು ಐಡಿ ಆಯ್ಕೆಮಾಡಿ", "Select Complaint ID"),
    "no_complaints": ("ದೂರುಗಳಿಲ್ಲ.", "No complaints."),
    "no_hotspots": ("ಆಯ್ಕೆಯ ವಲಯದಲ್ಲಿ ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗಳು ಕಂಡುಬಂದಿಲ್ಲ.", "No hotspots identified for the selected zone."),
    "no_planning_data": ("ಆಯ್ಕೆಯ ಫಿಲ್ಟರ್‌ಗಳಿಗೆ ದೂರುಗಳ ಡೇಟಾ ಲಭ್ಯವಿಲ್ಲ.", "No complaint data available for the selected filters."),
    "resolution_rate": ("ಪರಿಹಾರ ದರ", "Resolution rate"),
    "total_complaints": ("ಒಟ್ಟು ದೂರುಗಳು", "Total Complaints"),
    "resolved": ("ಪರಿಹರಿಸಲಾಗಿದೆ", "Resolved"),
    "open_complaints": ("ತೆರೆದ ದೂರುಗಳು", "Open Complaints"),
    "sla_breached": ("SLA ಮೀರಿದೆ", "SLA Breached"),
    "escalated": ("ಎಸ್ಕಲೇಟ್ ಮಾಡಲಾಗಿದೆ", "Escalated"),
    "view": ("ವೀಕ್ಷಿಸಿ", "View"),
    "hide": ("ಮರೆಮಾಡಿ", "Hide"),
    "status": ("ಸ್ಥಿತಿ", "Status"),
    "zone": ("ವಲಯ", "Zone"),
    "category": ("ವರ್ಗ", "Category"),
    "priority": ("ಪ್ರಾಥಮ್ಯ", "Priority"),
    "department": ("ಇಲಾಖೆ", "Department"),
    "language": ("ಭಾಷೆ", "Language"),
    "complaint_detail": ("ದೂರು ವಿವರ", "Complaint Detail"),
    "tab_overview": ("ಒಮ್ಮೆ ನೋಡಿದಾಗಿನ ದೃಶ್ಯ", "Overview"),
    "tab_analytics": ("ವಿಶ್ಲೇಷಣೆ", "Analytics"),
    "tab_hotspot_map": ("ಹಾಟ್‌ಸ್ಪಾಟ್ ನಕ್ಷೆ", "Hotspot Map"),
    "tab_planning": ("ಪೂರ್ವಸಿದ್ಧತಾ ಯೋಜನೆ", "Preventive Planning"),
    "tab_chronic": ("ದೀರ್ಘಕಾಲೀನ ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗಳು", "Chronic Hotspots"),
    "tab_tracker": ("ಟ್ರ್ಯಾಕ್ ಮತ್ತು ನಿರ್ವಹಣೆ", "Track & Manage"),
    "tab_complaints": ("ದೂರುಗಳು", "Complaints"),
    "no_data": ("ಡೇಟಾ ಲಭ್ಯವಿಲ್ಲ.", "No data available."),
    "loading_planning": ("ದೂರು ಮಾದರಿಗಳನ್ನು ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ…", "Analysing complaint patterns…"),
    "drafting_summary": ("ಸಾರ್ವಂ ಕಾರ್ಯನಿರ್ವಾಹಕ ಸಾರಾಂಶ ರಚಿಸಲಾಗುತ್ತಿದೆ...", "Drafting Sarvam executive summary..."),
}


def ui_text(key: str) -> str:
    kannada_text, english_text = UI_TEXTS.get(key, ("", key))
    return bilingual_text(kannada_text, english_text)
