"""
Karnataka Urban Analytics Dashboard
Official-facing intelligence layer for Municipal Commissioner and Zonal Officers.
"""

from __future__ import annotations

from html import escape
from hashlib import md5

import streamlit as st
import plotly.express as px
import streamlit.components.v1 as components


st.set_page_config(
    page_title="Karnataka Urban Analytics",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={"About": "Karnataka Municipal Urban Analytics Dashboard"},
)

# --- Language selection in top-right corner ---
if "ui_language" not in st.session_state:
    st.session_state["ui_language"] = "kn"

_lang_col1, _lang_col2, _lang_col3 = st.columns([8, 1, 1])
with _lang_col3:
    _LANG_OPTIONS = [("kn", "Kannada"), ("en", "English"), ("bi", "Bilingual")]
    _LANG_INDEX = {"kn": 0, "en": 1, "bi": 2}
    _prev_lang = st.session_state["ui_language"]
    _lang_choice = st.selectbox(
        "Language",
        options=_LANG_OPTIONS,
        format_func=lambda x: x[1],
        index=_LANG_INDEX.get(_prev_lang, 0),
        key="ui_language_select",
    )
    if _lang_choice[0] != _prev_lang:
        st.session_state["ui_language"] = _lang_choice[0]
        # Clear widget state that stores language-specific option strings,
        # so dropdowns re-default to the freshly-translated options.
        for _stale_key in ("zone_filter", "category_filter"):
            st.session_state.pop(_stale_key, None)
        st.rerun()


def _ka(english_text: str) -> str:
    """Translate English -> selected UI language for dynamic labels (zones, categories)."""
    lang = st.session_state.get("ui_language", "kn")
    if lang == "en":
        return english_text
    translated = translate_text(english_text, "en-IN", "kn-IN")
    if not translated:
        return english_text
    if lang == "bi":
        return f"{translated} ({english_text})"
    return translated

st.markdown(
    """
    <style>
    /* ── Global ── */
    html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
    .block-container { padding-top: 1.6rem !important; padding-bottom: 2rem !important; }

    /* ── Page header ── */
    h1 {
        font-size: 1.65rem !important;
        font-weight: 700 !important;
        background: linear-gradient(90deg, #1e3a5f 0%, #2563EB 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem !important;
    }

    /* ── Filter bar ── */
    [data-testid="stHorizontalBlock"] { align-items: flex-end !important; gap: 0.75rem; }

    /* ── Metric row: equal top alignment ── */
    [data-testid="column"] { align-self: stretch !important; }

    /* ── Metric cards ── */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem 1.2rem 0.6rem !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #64748b !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 2.4rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
        line-height: 1.15 !important;
    }
    [data-testid="stMetricDelta"] { font-size: 0.78rem !important; }

    /* ── View → buttons ── */
    [data-testid="stButton"] > button {
        border-radius: 8px !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
        padding: 0.3rem 0.9rem !important;
        border: 1.5px solid #2563EB !important;
        color: #2563EB !important;
        background: transparent !important;
        transition: all 0.18s ease;
    }
    [data-testid="stButton"] > button:hover {
        background: #2563EB !important;
        color: #ffffff !important;
    }

    /* ── Tabs ── */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 0.25rem;
        border-bottom: 2px solid #e2e8f0;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0 !important;
        padding: 0.55rem 1.1rem !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        color: #64748b !important;
        background: transparent !important;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        color: #2563EB !important;
        border-bottom: 3px solid #2563EB !important;
        background: #eff6ff !important;
    }

    /* ── Section headers ── */
    h2 { font-size: 1.25rem !important; font-weight: 700 !important; color: #1e293b !important; }
    h3 { font-size: 1.05rem !important; font-weight: 600 !important; color: #334155 !important; }

    /* ── Divider ── */
    hr { border-color: #e2e8f0 !important; margin: 1rem 0 !important; }

    /* ── Dataframe ── */
    [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }

    /* ── Info / success / warning boxes ── */
    [data-testid="stAlert"] { border-radius: 10px !important; font-size: 0.86rem !important; }

    /* ── Containers with border ── */
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        border-radius: 12px !important;
        border-color: #e2e8f0 !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }

    /* ── Selectbox ── */
    [data-baseweb="select"] > div {
        border-radius: 8px !important;
        border-color: #cbd5e1 !important;
        font-size: 0.88rem !important;
    }

    /* ── Caption text ── */
    [data-testid="stCaptionContainer"] { color: #64748b !important; font-size: 0.78rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    :root {
        --ink: #0f172a;
        --muted: #64748b;
        --brand: #1d4ed8;
        --brand-2: #0ea5e9;
        --surface: rgba(255,255,255,0.78);
        --shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(29, 78, 216, 0.14), transparent 32%),
            radial-gradient(circle at top right, rgba(14, 165, 233, 0.13), transparent 30%),
            linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
    }

    .main .block-container {
        max-width: 1500px;
        padding-top: 1.4rem !important;
        padding-bottom: 2.25rem !important;
    }

    .hero-shell {
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.55);
        background:
            linear-gradient(135deg, rgba(15, 118, 110, 0.12), rgba(29, 78, 216, 0.10) 45%, rgba(14, 165, 233, 0.12)),
            var(--surface);
        backdrop-filter: blur(12px);
        border-radius: 24px;
        box-shadow: var(--shadow);
        padding: 1.4rem 1.6rem;
        margin-bottom: 1rem;
    }

    .hero-shell:before {
        content: "";
        position: absolute;
        inset: -40px -20px auto auto;
        width: 180px;
        height: 180px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(29, 78, 216, 0.28) 0%, rgba(29, 78, 216, 0) 70%);
        pointer-events: none;
    }

    .hero-kicker {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.3rem 0.7rem;
        border-radius: 999px;
        background: rgba(29, 78, 216, 0.10);
        color: var(--brand);
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .hero-title {
        margin-top: 0.65rem;
        font-size: 2.1rem;
        line-height: 1.05;
        font-weight: 850;
        letter-spacing: -0.04em;
        color: var(--ink);
    }

    .hero-subtitle {
        max-width: 760px;
        margin-top: 0.65rem;
        color: var(--muted);
        font-size: 0.98rem;
        line-height: 1.55;
    }

    .hero-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-top: 1rem;
    }

    .hero-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.45rem 0.8rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(148, 163, 184, 0.22);
        box-shadow: 0 6px 14px rgba(15, 23, 42, 0.04);
        color: #334155;
        font-size: 0.8rem;
        font-weight: 700;
    }

    .panel-title {
        font-size: 1.05rem;
        font-weight: 800;
        color: var(--ink);
        margin-bottom: 0.25rem;
    }

    .panel-kicker {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--brand);
        margin-bottom: 0.25rem;
    }

    .panel-subtitle {
        font-size: 0.84rem;
        color: var(--muted);
        line-height: 1.45;
        margin-bottom: 0.8rem;
    }

    .panel-shell {
        border-radius: 18px;
        background: rgba(255,255,255,0.86);
        border: 1px solid rgba(219, 227, 238, 0.95);
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
        padding: 1rem 1.1rem;
    }

    [data-testid="stMetric"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(246, 249, 253, 0.98));
        border: 1px solid rgba(219, 227, 238, 0.95);
        border-radius: 18px;
        padding: 1rem 1.05rem 0.75rem !important;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.72rem !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--muted) !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 2.35rem !important;
        font-weight: 850 !important;
        color: var(--ink) !important;
        line-height: 1.1 !important;
    }

    [data-testid="stButton"] > button {
        border-radius: 12px !important;
        font-size: 0.8rem !important;
        font-weight: 700 !important;
        padding: 0.5rem 1rem !important;
        border: 1px solid rgba(29, 78, 216, 0.25) !important;
        color: white !important;
        background: linear-gradient(135deg, var(--brand) 0%, var(--brand-2) 100%) !important;
        box-shadow: 0 10px 18px rgba(29, 78, 216, 0.18);
    }

    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 0.45rem;
        border-bottom: 1px solid rgba(219, 227, 238, 0.95);
    }

    [data-testid="stTabs"] [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0 !important;
        padding: 0.65rem 1rem !important;
        font-weight: 800 !important;
        font-size: 0.84rem !important;
        color: #64748b !important;
        background: rgba(255,255,255,0.55) !important;
        border: 1px solid rgba(219, 227, 238, 0.4) !important;
        border-bottom: none !important;
    }

    [data-testid="stTabs"] [aria-selected="true"] {
        color: var(--brand) !important;
        background: #ffffff !important;
        box-shadow: 0 -4px 14px rgba(15, 23, 42, 0.04);
    }

    [data-testid="stDataFrame"],
    [data-testid="stAlert"],
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        border-radius: 16px !important;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
    }

    [data-baseweb="select"] > div {
        border-radius: 12px !important;
        font-size: 0.88rem !important;
        background: rgba(255,255,255,0.95) !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# Imports after page config so Streamlit doesn't complain
# ------------------------------------------------------------------
from lib.api import get_summary, get_trends, get_hotspots, get_complaints, is_mock_mode, api_base_url, get_complaint, update_complaint_status, escalate_complaint
from lib.transform import (
    summary_to_category_df,
    summary_to_zone_df,
    summary_to_status_df,
    trends_to_df,
    hotspots_to_df,
    complaints_to_df,
)
from lib.labels import (
    CATEGORY_LABELS,
    CATEGORY_COLORS,
    STATUS_LABELS,
    STATUS_COLORS,
    STATUSES,
    CATEGORIES,
    LANGUAGE_LABELS,
    ui_text,
    bilingual_text,
)
from lib.sarvam_text import normalize_language_code, language_label, translate_text

# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
# Horizontal filter bar (replaces sidebar)
# ------------------------------------------------------------------
_hero_kicker = bilingual_text("ಮುನ್ಸಿಪಲ್ ಗುಪ್ತಚರ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್", "Municipal intelligence dashboard")
_hero_title = bilingual_text("ಕರ್ನಾಟಕ ನಗರ ವಿಶ್ಲೇಷಣೆ", "Karnataka Urban Analytics")
_hero_subtitle = bilingual_text(
    "ನಾಗರಿಕ ಕಾರ್ಯಾಚರಣೆಗಳಿಗಾಗಿ ಶುದ್ಧವಾದ ನಿಯಂತ್ರಣ ಕೇಂದ್ರ — ದೂರುಗಳನ್ನು ಗಮನಿಸಿ, ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗಳನ್ನು ಗುರುತಿಸಿ, ಮತ್ತು ಎಲ್ಲ ವಲಯಗಳಲ್ಲಿ ಕ್ರಮವನ್ನು ಆದ್ಯತೆಯಂತೆ ಕ್ರಮಗೊಳಿಸಿ.",
    "A polished command center for civic operations — monitor complaints, identify hotspots, and prioritize action across every zone in one glance.",
)
_hero_chip_1 = bilingual_text("ಲೈವ್ ಸಾರಾಂಶ ಮೆಟ್ರಿಕ್ಸ್", "Live summary metrics")
_hero_chip_2 = bilingual_text("ವಲಯ ಮತ್ತು ವರ್ಗ ಫಿಲ್ಟರ್‌ಗಳು", "Zone and category filters")
_hero_chip_3 = bilingual_text("AI ಹಾಟ್‌ಸ್ಪಾಟ್ ಮತ್ತು ಯೋಜನೆ ವೀಕ್ಷಣೆಗಳು", "AI hotspot and planning views")

st.markdown(
    f"""
    <div class="hero-shell">
        <div class="hero-kicker">{escape(_hero_kicker)}</div>
        <div class="hero-title">{escape(_hero_title)}</div>
        <div class="hero-subtitle">
            {escape(_hero_subtitle)}
        </div>
        <div class="hero-meta">
            <span class="hero-chip">{escape(_hero_chip_1)}</span>
            <span class="hero-chip">{escape(_hero_chip_2)}</span>
            <span class="hero-chip">{escape(_hero_chip_3)}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.title(ui_text("app_title"))
st.caption(ui_text("app_caption"))

_fc1, _fc2, _fc3, _fc4 = st.columns([2, 2, 1, 2])

with _fc1:
    ALL_ZONES_LABEL = ui_text("all_zones")
    zone_options = [
        ALL_ZONES_LABEL,
        _ka("Zone North"),
        _ka("Zone South"),
        _ka("Zone East"),
        _ka("Zone West"),
        _ka("Zone Central"),
    ]
    selected_zone_label: str = st.selectbox(
        ui_text("filter_by_zone"),
        options=zone_options,
        key="zone_filter",
        help=_ka("Narrow every chart and table to a single municipal zone."),
    )
    active_zone: str | None = None if selected_zone_label == ALL_ZONES_LABEL else selected_zone_label

with _fc2:
    ALL_CATEGORIES_LABEL = ui_text("all_categories")
    category_options = [ALL_CATEGORIES_LABEL] + [_ka(CATEGORY_LABELS[k]) for k in CATEGORIES]
    selected_category_label: str = st.selectbox(
        ui_text("filter_by_category"),
        options=category_options,
        key="category_filter",
        help=_ka("Narrow every chart and table to a single problem category."),
    )
    active_category: str | None = None if selected_category_label == ALL_CATEGORIES_LABEL else next(
        (k for k, v in CATEGORY_LABELS.items() if v == selected_category_label), None
    )

with _fc3:
    st.write("")  # vertical alignment spacer
    st.write("")

with _fc4:
    st.write("")
    if st.button(ui_text("refresh_data"), use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if is_mock_mode():
        st.info(ui_text("mock_mode"), icon="🔶")
    else:
        st.success(f"{ui_text('live_api')}: {api_base_url()}", icon="✅")

st.caption(
    f"{ui_text('current_filters')}: {ui_text('zone')} = {selected_zone_label}, {ui_text('category')} = {selected_category_label}. "
    + bilingual_text("ಫಿಲ್ಟರ್‌ಗಳನ್ನು ಬಳಸಿ ವೀಕ್ಷಣೆಯನ್ನು ಸಂಕುಚಿತಗೊಳಿಸಿ ಅಥವಾ ವಿಸ್ತರಿಸಿ.", "Use the filters to narrow or broaden the view across the dashboard.")
)

st.divider()

# ------------------------------------------------------------------
# Cached data loaders - 60 s TTL to avoid hammering the backend
# ------------------------------------------------------------------

@st.cache_data(ttl=60, show_spinner=False)
def load_summary(zone: str | None, category: str | None) -> dict:
    return get_summary(zone=zone, category=category)


@st.cache_data(ttl=60, show_spinner=False)
def load_trends(zone: str | None, category: str | None) -> dict:
    return get_trends(days=30, zone=zone, category=category)


@st.cache_data(ttl=60, show_spinner=False)
def load_hotspots(zone: str | None, category: str | None) -> dict:
    return get_hotspots(zone=zone, category=category)


@st.cache_data(ttl=60, show_spinner=False)
def load_complaints(zone: str | None, category: str | None, status: str | None) -> list:
    return get_complaints(zone=zone, category=category, status=status)


@st.cache_data(ttl=60, show_spinner=False)
def load_complaint_detail(complaint_id: str) -> dict:
    """Look up a single complaint (with history) from the /complaints endpoint."""
    from lib.sarvam_text import enrich_complaint_record

    return enrich_complaint_record(get_complaint(complaint_id))


# Load data used across multiple tabs
with st.spinner(ui_text("loading_data")):
    try:
        summary = load_summary(active_zone, active_category)
        trends_data = load_trends(active_zone, active_category)
        hotspots_data = load_hotspots(active_zone, active_category)
    except (ConnectionError, RuntimeError, TimeoutError) as exc:
        st.error(bilingual_text("ಡೇಟಾ ಲೋಡ್ ಆಗಲಿಲ್ಲ", "Could not load data") + f": {exc}")
        st.info(bilingual_text("ಬ್ಯಾಕೆಂಡ್ ಆಫ್ಲೈನ್ ಇದ್ದರೆ .env ನಲ್ಲಿ USE_MOCK_DATA=true ಹಾಕಿ.", "Set USE_MOCK_DATA=true in your .env file to use simulated data while the backend is offline."))
        st.stop()


def _render_hotspot_map(df, height: int = 520) -> None:
    """Render a hotspot map with Folium when available, otherwise Plotly."""
    try:
        import folium
        from streamlit_folium import st_folium

        center_lat = df["latitude"].mean()
        center_lon = df["longitude"].mean()

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles="OpenStreetMap",
        )

        max_count = max(int(df["complaint_count"].max()), 1)
        for _, row in df.iterrows():
            radius = 12 + int((row["complaint_count"] / max_count) * 18)
            hex_color = CATEGORY_COLORS.get(row["category"], "#6B7280")

            popup_html = f"""
            <div style="min-width:210px;font-family:sans-serif;font-size:13px">
                <b style="font-size:14px">{row['category_label']}</b><br>
                {row['sub_category_label']}<br>
                <hr style="margin:4px 0">
                Zone: <b>{row['zone']}</b><br>
                Repeat complaints: <b>{row['complaint_count']}</b><br>
                <hr style="margin:4px 0">
                <i style="color:#555">{row['recommendation']}</i>
            </div>
            """

            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=radius,
                color=hex_color,
                fill=True,
                fill_color=hex_color,
                fill_opacity=0.75,
                weight=2,
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"{row['category_label']}: {row['complaint_count']} complaints - {row['zone']}",
            ).add_to(m)

        st_folium(m, width=None, height=height, returned_objects=[])
        return
    except Exception:
        fig = px.scatter_mapbox(
            df,
            lat="latitude",
            lon="longitude",
            color="category_label",
            size="complaint_count",
            size_max=28,
            hover_name="sub_category_label",
            hover_data={
                "zone": True,
                "complaint_count": True,
                "recommendation": True,
                "latitude": False,
                "longitude": False,
                "category_label": False,
            },
            color_discrete_map={CATEGORY_LABELS.get(k, k): v for k, v in CATEGORY_COLORS.items()},
            zoom=11,
            height=height,
        )
        fig.update_layout(
            mapbox_style="open-street-map",
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend_title_text="Category",
        )
        st.plotly_chart(fig, use_container_width=True)


def _render_complaint_dot_map(complaints: list[dict], hotspots_df=None, height: int = 520) -> None:
    """Render one dot per complaint, jittered slightly so overlapping complaints remain visible."""
    import pandas as _pd

    complaint_df = complaints_to_df(complaints)
    if complaint_df.empty:
        st.info(bilingual_text("ಆಯ್ದ ಫಿಲ್ಟರ್‌ಗಳಿಗೆ ದೂರು ಸ್ಥಳಾಂಕಗಳು ಇಲ್ಲ.", "No complaint coordinates available for the selected filters."))
        return

    complaint_df = complaint_df.dropna(subset=["latitude", "longitude"]).copy()
    if complaint_df.empty:
        st.info(bilingual_text("ಆಯ್ದ ಫಿಲ್ಟರ್‌ಗಳಿಗೆ ದೂರು ಸ್ಥಳಾಂಕಗಳು ಇಲ್ಲ.", "No complaint coordinates available for the selected filters."))
        return

    complaint_df["category_label"] = complaint_df["category"].map(lambda k: CATEGORY_LABELS.get(k, k))
    complaint_df["status_label"] = complaint_df["status"].map(lambda k: STATUS_LABELS.get(k, k))
    complaint_df["status_color"] = complaint_df["status"].map(lambda k: STATUS_COLORS.get(k, "#6B7280"))
    complaint_df["inner_dot_size"] = complaint_df["status"].map(
        {
            "filed": 4.0,
            "assigned": 4.8,
            "in_progress": 5.8,
            "resolved": 4.2,
            "escalated": 7.2,
        }
    ).fillna(4.6)
    complaint_df["marker_size"] = 6

    def _jitter(value: str, scale: float = 0.0008) -> tuple[float, float]:
        digest = md5(value.encode("utf-8")).hexdigest()
        lat_raw = int(digest[:8], 16)
        lon_raw = int(digest[8:16], 16)
        lat_offset = ((lat_raw % 2000) - 1000) / 1000 * scale
        lon_offset = ((lon_raw % 2000) - 1000) / 1000 * scale
        return lat_offset, lon_offset

    complaint_df["j_latitude"] = complaint_df.apply(
        lambda row: row["latitude"] + _jitter(str(row.get("complaint_id", "")))[0],
        axis=1,
    )
    complaint_df["j_longitude"] = complaint_df.apply(
        lambda row: row["longitude"] + _jitter(str(row.get("complaint_id", "")))[1],
        axis=1,
    )

    try:
        import folium
        from streamlit_folium import st_folium

        center_lat = complaint_df["j_latitude"].mean()
        center_lon = complaint_df["j_longitude"].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="OpenStreetMap")

        if hotspots_df is not None and not hotspots_df.empty:
            max_count = max(int(hotspots_df["complaint_count"].max()), 1)
            for _, row in hotspots_df.iterrows():
                radius = 10 + int((row["complaint_count"] / max_count) * 18)
                hex_color = CATEGORY_COLORS.get(row["category"], "#6B7280")
                folium.CircleMarker(
                    location=[row["latitude"], row["longitude"]],
                    radius=radius,
                    color=hex_color,
                    fill=True,
                    fill_color=hex_color,
                    fill_opacity=0.12,
                    weight=2,
                    tooltip=f"{row['category_label']}: {row['complaint_count']} complaints",
                ).add_to(m)

        for _, row in complaint_df.iterrows():
            hex_color = row["status_color"]
            popup_html = f"""
            <div style="min-width:220px;font-family:sans-serif;font-size:13px">
                <b style="font-size:14px">{row['complaint_id']}</b><br>
                {row['category_label']}<br>
                {row.get('sub_category_label', '')}<br>
                <hr style="margin:4px 0">
                {ui_text('zone')}: <b>{row['zone']}</b><br>
                {ui_text('status')}: <b>{row['status_label']}</b><br>
                Ward: <b>{row.get('ward', '—')}</b>
            </div>
            """
            folium.CircleMarker(
                location=[row["j_latitude"], row["j_longitude"]],
                radius=4.5,
                color=hex_color,
                fill=True,
                fill_color=hex_color,
                fill_opacity=0.9,
                weight=1.5,
                popup=folium.Popup(popup_html, max_width=280),
                tooltip=f"{row['complaint_id']} — {row['category_label']}",
            ).add_to(m)

        st_folium(m, width=None, height=height, returned_objects=[])
        return
    except Exception:
        fig = px.scatter_mapbox(
            complaint_df,
            lat="j_latitude",
            lon="j_longitude",
            color="status_label",
            size="marker_size",
            size_max=10,
            hover_name="complaint_id",
            hover_data={
                "zone": True,
                "status_label": True,
                "category_label": False,
                "latitude": False,
                "longitude": False,
                "j_latitude": False,
                "j_longitude": False,
            },
            color_discrete_map={STATUS_LABELS.get(k, k): v for k, v in STATUS_COLORS.items()},
            zoom=11,
            height=height,
        )
        fig.update_layout(
            mapbox_style="open-street-map",
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            legend_title_text="Status",
        )
        st.plotly_chart(fig, use_container_width=True)


def _render_zone_bubble_map(zone_hotspots: list[dict], complaints: list[dict], height: int = 520) -> None:
    """Render large zone-level bubbles for chronic hotspots."""
    if not zone_hotspots:
        st.info(bilingual_text("ಆಯ್ದ ಫಿಲ್ಟರ್‌ಗಳಿಗೆ ವಲಯಮಟ್ಟದ ದೀರ್ಘಕಾಲೀನ ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗಳು ಇಲ್ಲ.", "No zone-level chronic hotspots available for the selected filters."))
        return

    complaint_df = complaints_to_df(complaints)
    if complaint_df.empty:
        st.info(bilingual_text("ದೀರ್ಘಕಾಲೀನ ಹಾಟ್‌ಸ್ಪಾಟ್ ಗುಬ್ಬೆಗಳ ಒಳಗೆ ಪ್ರದರ್ಶಿಸಲು ದೂರು ಸಾಲುಗಳಿಲ್ಲ.", "No complaint rows available to render inside the chronic hotspot bubbles."))
        return

    complaint_df = complaint_df.dropna(subset=["latitude", "longitude"]).copy()
    if complaint_df.empty:
        st.info(bilingual_text("ಗುಬ್ಬೆಗಳ ಒಳಗೆ ಪ್ರದರ್ಶಿಸಲು ದೂರು ಸ್ಥಳಾಂಕಗಳು ಇಲ್ಲ.", "No complaint coordinates available to render inside the chronic hotspot bubbles."))
        return

    complaint_df["status_label"] = complaint_df["status"].map(lambda k: STATUS_LABELS.get(k, k))
    complaint_df["status_color"] = complaint_df["status"].map(lambda k: STATUS_COLORS.get(k, "#6B7280"))
    complaint_df["inner_dot_size"] = complaint_df["status"].map(
        {
            "filed": 4.0,
            "assigned": 4.8,
            "in_progress": 5.8,
            "resolved": 4.2,
            "escalated": 7.2,
        }
    ).fillna(4.6)

    zone_centers = {
        "Zone North": (13.052, 77.563),
        "Zone South": (12.872, 77.548),
        "Zone East": (12.961, 77.651),
        "Zone West": (12.981, 77.461),
        "Zone Central": (12.974, 77.578),
    }

    zone_df = {}
    for row in zone_hotspots:
        zone_name = row.get("zone", "Unknown")
        current = zone_df.get(zone_name)
        severity_rank = {"Critical": 3, "High": 2, "Medium": 1}.get(row.get("severity_label"), 0)
        if current is None or severity_rank > current["severity_rank"] or (
            severity_rank == current["severity_rank"] and row.get("complaint_count", 0) > current["complaint_count"]
        ):
            zone_df[zone_name] = {
                "zone": zone_name,
                "complaint_count": 0,
                "severity_rank": severity_rank,
                "severity_label": row.get("severity_label", "Medium"),
                "badge_color": row.get("badge_color", "#6B7280"),
                "category_label": row.get("category_label") or CATEGORY_LABELS.get(row.get("category"), row.get("category")),
                "sub_category_label": row.get("sub_category_label") or row.get("sub_category"),
                "recommendation": row.get("recommendation", "Investigate the dominant repeat complaint cluster."),
            }
        zone_df[zone_name]["complaint_count"] += int(row.get("complaint_count", 0))

    bubbles = list(zone_df.values())

    try:
        import folium
        from streamlit_folium import st_folium

        center_lat = sum(zone_centers.get(b["zone"], (12.974, 77.578))[0] for b in bubbles) / len(bubbles)
        center_lon = sum(zone_centers.get(b["zone"], (12.974, 77.578))[1] for b in bubbles) / len(bubbles)
        m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="OpenStreetMap")

        max_count = max(int(b["complaint_count"]) for b in bubbles) or 1
        for bubble in bubbles:
            lat, lon = zone_centers.get(bubble["zone"], (12.974, 77.578))
            radius = 18 + int((bubble["complaint_count"] / max_count) * 28)

            zone_complaints = complaint_df[complaint_df["zone"] == bubble["zone"]]
            if not zone_complaints.empty:
                inner_scale = 0.006 + (radius / 1000)
                for _, complaint in zone_complaints.iterrows():
                    digest = md5(str(complaint["complaint_id"]).encode("utf-8")).hexdigest()
                    lat_offset = ((int(digest[:8], 16) % 2000) - 1000) / 1000 * inner_scale
                    lon_offset = ((int(digest[8:16], 16) % 2000) - 1000) / 1000 * inner_scale
                    folium.CircleMarker(
                        location=[lat + lat_offset, lon + lon_offset],
                        radius=float(complaint["inner_dot_size"]),
                        color=complaint["status_color"],
                        fill=True,
                        fill_color=complaint["status_color"],
                        fill_opacity=0.95,
                        weight=1,
                        tooltip=f"{complaint['complaint_id']} - {complaint['status_label']}",
                    ).add_to(m)

            folium.CircleMarker(
                location=[lat, lon],
                radius=radius,
                color=bubble["badge_color"],
                fill=True,
                fill_color=bubble["badge_color"],
                fill_opacity=0.30,
                weight=3,
                tooltip=f"{bubble['zone']} - {bubble['complaint_count']} chronic complaints",
                popup=folium.Popup(
                    f"""
                    <div style="min-width:220px;font-family:sans-serif;font-size:13px">
                        <b style="font-size:14px">{bubble['zone']}</b><br>
                        {bilingual_text("ತೀವ್ರತೆ", "Severity")}: <b>{bubble['severity_label']}</b><br>
                        {bilingual_text("ದೀರ್ಘಕಾಲೀನ ದೂರುಗಳು", "Chronic complaints")}: <b>{bubble['complaint_count']}</b><br>
                        {bilingual_text("ಮುಖ್ಯ ಸಮಸ್ಯೆ", "Top issue")}: {bubble['category_label']} / {bubble['sub_category_label']}<br>
                        <hr style="margin:4px 0">
                        <i style="color:#555">{bubble['recommendation']}</i>
                    </div>
                    """,
                    max_width=280,
                ),
            ).add_to(m)

        st_folium(m, width=None, height=height, returned_objects=[])
        return
    except Exception:
        import pandas as _pd
        import plotly.graph_objects as go

        bubble_df = _pd.DataFrame(bubbles)
        bubble_df["latitude"] = bubble_df["zone"].map(lambda z: zone_centers.get(z, (12.974, 77.578))[0])
        bubble_df["longitude"] = bubble_df["zone"].map(lambda z: zone_centers.get(z, (12.974, 77.578))[1])
        fig = go.Figure()

        for _, row in bubble_df.iterrows():
            fig.add_trace(
                go.Scattermapbox(
                    lat=[row["latitude"]],
                    lon=[row["longitude"]],
                    mode="markers",
                    marker=dict(
                        size=18 + min(int(row["complaint_count"]) * 2, 42),
                        color=row["badge_color"],
                        opacity=0.30,
                    ),
                    name=row["zone"],
                    hovertext=(
                        f"{row['zone']}<br>"
                        f"{bilingual_text('ತೀವ್ರತೆ', 'Severity')}: {row['severity_label']}<br>"
                        f"{bilingual_text('ದೀರ್ಘಕಾಲೀನ ದೂರುಗಳು', 'Chronic complaints')}: {row['complaint_count']}"
                    ),
                    hoverinfo="text",
                )
            )

        for _, complaint in complaint_df.iterrows():
            lat, lon = zone_centers.get(complaint["zone"], (12.974, 77.578))
            digest = md5(str(complaint["complaint_id"]).encode("utf-8")).hexdigest()
            inner_scale = 0.006
            lat_offset = ((int(digest[:8], 16) % 2000) - 1000) / 1000 * inner_scale
            lon_offset = ((int(digest[8:16], 16) % 2000) - 1000) / 1000 * inner_scale
            fig.add_trace(
                go.Scattermapbox(
                    lat=[lat + lat_offset],
                    lon=[lon + lon_offset],
                    mode="markers",
                    marker=dict(size=float(complaint["inner_dot_size"]) * 1.7, color=complaint["status_color"]),
                    name=complaint["status_label"],
                    hovertext=(
                        f"{complaint['complaint_id']}<br>"
                        f"{complaint['zone']}<br>"
                        f"Status: {complaint['status_label']}"
                    ),
                    hoverinfo="text",
                    showlegend=False,
                )
            )

        fig.update_layout(
            mapbox_style="open-street-map",
            mapbox=dict(
                center=dict(
                    lat=bubble_df["latitude"].mean(),
                    lon=bubble_df["longitude"].mean(),
                ),
                zoom=11,
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=height,
        )
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------
# Session state for Overview drill-down
# ------------------------------------------------------------------
if "overview_drill" not in st.session_state:
    st.session_state.overview_drill = None

# ------------------------------------------------------------------
# Tabs
# ------------------------------------------------------------------
tab_overview, tab_analytics, tab_map, tab_planning, tab_hotspot_ai, tab_tracker, tab_table = st.tabs(
    [
        ui_text("tab_overview"),
        ui_text("tab_analytics"),
        ui_text("tab_hotspot_map"),
        ui_text("tab_planning"),
        ui_text("tab_chronic"),
        ui_text("tab_tracker"),
        ui_text("tab_complaints"),
    ]
)

# =====================================================================
# Tab 1: Overview - headline metrics
# =====================================================================
with tab_overview:
    zone_tag = f" - {active_zone}" if active_zone else ""
    st.header(f"{ui_text('overview_title')}{zone_tag}")
    st.caption(f"{ui_text('overview_caption')} Refresh in the sidebar to force an update.")
    total = summary["total_complaints"]
    resolved = summary["by_status"].get("resolved", 0)
    open_count = total - resolved
    sla_breached = summary["sla_breached_count"]
    escalated = summary["by_status"].get("escalated", 0)
    pct_resolved = round((resolved / total * 100), 1) if total else 0

    col1, col2, col3, col4, col5 = st.columns(5)

    def _drill_button(key: str, col):
        active = st.session_state.overview_drill == key
        btn_label = bilingual_text("ಮರೆಮಾಡಿ ▼", "Hide") if active else bilingual_text("ವೀಕ್ಷಿಸಿ →", "View")
        if col.button(btn_label, key=f"btn_{key}", use_container_width=True):
            st.session_state.overview_drill = None if active else key
            st.rerun()

    with col1:
        st.metric(ui_text("total_complaints"), total)
        _drill_button("total", col1)

    with col2:
        st.metric(ui_text("resolved"), resolved)
        _drill_button("resolved", col2)

    with col3:
        st.metric(ui_text("open_complaints"), open_count)
        _drill_button("open", col3)

    with col4:
        st.metric(ui_text("sla_breached"), sla_breached)
        _drill_button("sla", col4)

    with col5:
        st.metric(ui_text("escalated"), escalated)
        _drill_button("escalated", col5)

    # Resolution rate banner below the metric cards
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:16px;
                    background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
                    padding:10px 20px;margin-top:12px;">
            <span style="font-size:0.78rem;font-weight:600;text-transform:uppercase;
                         letter-spacing:0.05em;color:#15803d;">{ui_text('resolution_rate')}</span>
            <span style="font-size:1.6rem;font-weight:700;color:#15803d;">{pct_resolved}%</span>
            <span style="font-size:0.82rem;color:#4ade80;">
                {resolved} of {total} complaints resolved
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Drill-down complaint list
    drill = st.session_state.overview_drill
    if drill:
        _DRILL_TITLES = {
            "total":    "All Complaints",
            "resolved": "Resolved Complaints",
            "open":     "Open Complaints (filed / assigned / in progress)",
            "sla":      "SLA Breached Complaints",
            "escalated":"Escalated Complaints",
        }
        st.subheader(_DRILL_TITLES[drill])

        @st.cache_data(ttl=60, show_spinner=False)
        def _load_drill(zone, category):
            return load_complaints(zone, category, None)

        all_c = complaints_to_df(_load_drill(active_zone, active_category))

        if not all_c.empty:
            if drill == "resolved":
                drilled = all_c[all_c["status"] == "resolved"]
            elif drill == "open":
                drilled = all_c[all_c["status"].isin(["filed", "assigned", "in_progress"])]
            elif drill == "sla":
                drilled = all_c[all_c["sla_breached"] == True]
            elif drill == "escalated":
                drilled = all_c[all_c["status"] == "escalated"]
            else:
                drilled = all_c

            drilled = drilled.sort_values("created_at", ascending=False)
            st.caption(bilingual_text(f"{len(drilled)} ದೂರುಗಳು", f"{len(drilled)} complaints"))

            _cols_map = {
                "complaint_id":       "Complaint ID",
                "category_label":     "Category",
                "sub_category_label": "Sub-category",
                "zone":               "Zone",
                "ward":               "Ward",
                "status_label":       "Status",
                "priority_label":     "Priority",
                "created_date":       "Filed On",
                "sla_breached":       "SLA Breached",
            }
            show_cols = {k: v for k, v in _cols_map.items() if k in drilled.columns}
            st.dataframe(
                drilled[list(show_cols.keys())].rename(columns=show_cols),
                use_container_width=True,
                hide_index=True,
                height=350,
            )
        else:
            st.info(ui_text("no_complaints"))

    st.divider()

    # Quick status breakdown as a horizontal stacked bar
    st.subheader(bilingual_text("ಪರಿಹಾರ ಹಂತ", "Resolution pipeline"))
    status_df = summary_to_status_df(summary)
    if not status_df.empty:
        fig = px.bar(
            status_df,
            x="Count",
            y=["Status"],
            color="Status",
            color_discrete_map={
                row["Status"]: row["color"] for _, row in status_df.iterrows()
            },
            orientation="h",
            text="Count",
            height=120,
        )
        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=0, r=0, t=40, b=0),
            xaxis_title="",
            yaxis_title="",
            yaxis=dict(showticklabels=False),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)


# =====================================================================
# Tab 2: Analytics - bar charts and trend
# =====================================================================
with tab_analytics:
    zone_tag = f" - {active_zone}" if active_zone else ""
    st.header(f"{ui_text('analytics_title')}{zone_tag}")

    # Row 1: category + zone
    col_cat, col_zone = st.columns(2)

    with col_cat:
        st.subheader(bilingual_text("ವರ್ಗವಾರು ದೂರುಗಳು", "Complaints by category"))
        cat_df = summary_to_category_df(summary)
        if not cat_df.empty:
            fig = px.bar(
                cat_df,
                x="Complaints",
                y="Category",
                orientation="h",
                color="Category",
                color_discrete_map={
                    CATEGORY_LABELS.get(k, k): v for k, v in CATEGORY_COLORS.items()
                },
                text="Complaints",
                height=300,
            )
            fig.update_layout(
                showlegend=False,
                margin=dict(l=0, r=20, t=10, b=0),
                xaxis_title=bilingual_text("ದೂರುಗಳ ಸಂಖ್ಯೆ", "Number of complaints"),
                yaxis_title="",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    with col_zone:
        st.subheader(bilingual_text("ವಲಯವಾರು ದೂರುಗಳು", "Complaints by zone"))
        zone_df = summary_to_zone_df(summary)
        if not zone_df.empty:
            fig = px.bar(
                zone_df,
                x="Complaints",
                y="Zone",
                orientation="h",
                color_discrete_sequence=["#3B82F6"],
                text="Complaints",
                height=300,
            )
            fig.update_layout(
                showlegend=False,
                margin=dict(l=0, r=20, t=10, b=0),
                xaxis_title=bilingual_text("ದೂರುಗಳ ಸಂಖ್ಯೆ", "Number of complaints"),
                yaxis_title="",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

    # Row 2: 30-day trend
    st.subheader(bilingual_text("ಕಳೆದ 30 ದಿನಗಳ ದೂರು ಟ್ರೆಂಡ್ (ವರ್ಗವಾರು)", "Complaint trend - last 30 days (by category)"))
    trend_df = trends_to_df(trends_data)
    if not trend_df.empty:
        # Build color map using human-readable labels
        color_map = {CATEGORY_LABELS.get(k, k): v for k, v in CATEGORY_COLORS.items()}
        fig = px.line(
            trend_df.reset_index(),
            x="date",
            y=trend_df.columns.tolist(),
            color_discrete_map=color_map,
            markers=True,
            height=350,
        )
        fig.update_layout(
            legend_title_text=bilingual_text("ವರ್ಗ", "Category"),
            xaxis_title=bilingual_text("ದಿನಾಂಕ", "Date"),
            yaxis_title=bilingual_text("ದೂರುಗಳು", "Complaints"),
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(bilingual_text("ಆಯ್ದ ವಲಯ/ಅವಧಿಗೆ ಟ್ರೆಂಡ್ ಡೇಟಾ ಇಲ್ಲ.", "No trend data available for the selected zone/period."))

# =====================================================================
# Tab 3: Hotspot Map
# =====================================================================
with tab_map:
    zone_tag = f" - {active_zone}" if active_zone else ""
    st.header(f"{ui_text('hotspot_title')}{zone_tag}")
    st.caption(
        ui_text("hotspot_caption") + " Each complaint is shown as a separate dot, with clustered hotspots lightly outlined behind them."
    )

    hs_df = hotspots_to_df(hotspots_data)
    complaint_dots = load_complaints(active_zone, active_category, None)

    if hs_df.empty and not complaint_dots:
        st.info(ui_text("no_hotspots"))
    else:
        _render_complaint_dot_map(complaint_dots, hotspots_df=hs_df, height=520)

        # Legend
        st.divider()
        st.caption(_ka("Dot colors represent complaint status; faint outlines show the broader hotspot clusters."))
        cols = st.columns(len(STATUS_COLORS))
        for col, (key, color) in zip(cols, STATUS_COLORS.items()):
            col.markdown(
                f'<span style="display:inline-block;width:12px;height:12px;'
                f'border-radius:50%;background:{color};margin-right:6px"></span>'
                f'{STATUS_LABELS.get(key, key)}',
                unsafe_allow_html=True,
            )

# =====================================================================
# Tab 4: Preventive Planning
# =====================================================================
with tab_planning:
    from lib.planning_insights import compute_preventive_insights
    from lib.planning_ai import generate_planning_insights
    from lib.labels import SUB_CATEGORY_LABELS as _SCL, CATEGORY_LABELS as _CL

    zone_tag = f" — {active_zone}" if active_zone else ""
    st.header(f"{ui_text('planning_title')}{zone_tag}")
    st.caption(
        bilingual_text(
            "ದೂರು ಮಾದರಿಗಳ ಆಧಾರದ ಮೇಲೆ ಪೂರ್ವಸಿದ್ಧತಾ ಮೂಲಸೌಕರ್ಯ ಹೂಡಿಕೆ ವಿಶ್ಲೇಷಣೆ.",
            "Data-driven analysis of complaint patterns to prioritise preventive infrastructure investment.",
        )
        + " Sarvam turns the signals into an executive summary."
    )

    @st.cache_data(ttl=60, show_spinner=False)
    def load_planning_data(zone, category):
        from lib.api import get_complaints as _gc
        return compute_preventive_insights(_gc(), days_window=60, zone=zone, category=category)

    with st.spinner(ui_text("loading_planning")):
        ins = load_planning_data(active_zone, active_category)

    if ins.get("empty"):
        st.info(ui_text("no_planning_data"))
    else:
        kpis = ins["kpis"]

        def _build_ai_summary_payload(data: dict) -> dict:
            return {
                "total_complaints": data["kpis"]["total"],
                "by_status": {
                    "resolved": data["kpis"]["resolved"],
                    "escalated": data["kpis"]["escalated"],
                },
                "sla_breached_count": data["kpis"]["sla_breached"],
                "by_category": {key: value["count"] for key, value in data["category_risk"].items()},
                "by_zone": {key: value["count"] for key, value in data["zone_risk"].items()},
            }

        def load_sarvam_report(zone, category):
            planning_data = load_planning_data(zone, category)
            if planning_data.get("empty"):
                return {"ok": False, "error": "No complaint data available for the selected filters."}
            return generate_planning_insights(
                planning_data["priority_areas"],
                _build_ai_summary_payload(planning_data),
                zone=zone,
                category=category,
            )

        with st.spinner(ui_text("drafting_summary")):
            ai_report = load_sarvam_report(active_zone, active_category)

        if not ai_report.get("ok"):
            top_pair = ins.get("top_pair") or {}
            ai_report = {
                "ok": True,
                "source": "local-fallback",
                "model_used": "deterministic-summary",
                "executive_summary": (
                    f"The dashboard currently shows {kpis['total']} complaints, with "
                    f"{kpis['sla_breached']} SLA breaches and {kpis['escalated']} escalations. "
                    f"The most urgent area is {top_pair.get('zone', 'the highest-risk zone')}, "
                    f"focused on {top_pair.get('category', 'the most active category')}."
                ),
            }

        source_label = {
            "fallback": bilingual_text("ನಿಯಮಿತ ಬ್ಯಾಕಪ್", "Deterministic fallback"),
            "local-fallback": bilingual_text("ಸ್ಥಳೀಯ ಬ್ಯಾಕಪ್", "Local fallback"),
        }.get(ai_report.get("source"), bilingual_text("ಸಾರ್ವಂ", "Sarvam"))
        summary_text = _ka(ai_report.get("executive_summary", ""))
        st.markdown(
            f"""
            <div class="panel-shell" style="margin-bottom:1rem;">
                <div class="panel-kicker">{bilingual_text("ಯೋಜನಾ ಸಾರಾಂಶ", "Planning summary")}</div>
                <div class="panel-title">{bilingual_text("ಲೈವ್ ದೂರು ಸಂಕೇತಗಳಿಂದ AI ವಿವರಣೆ", "AI narrative generated from live complaint signals")}</div>
                <div class="panel-subtitle">{summary_text}</div>
                <div style="margin-top:0.75rem;font-size:0.78rem;color:#64748b;">
                    {bilingual_text("ಮೂಲ", "Source")}: <b>{source_label}</b> &nbsp;|&nbsp; {bilingual_text("ಮಾದರಿ", "Model used")}: <b>{ai_report.get('model_used', 'sarvam-30b')}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        kpis = ins["kpis"]

        # ── KPI banner ───────────────────────────────────────────────
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric(ui_text("total_complaints"), kpis["total"])
        k2.metric(ui_text("resolved"), kpis["resolved"])
        k3.metric(ui_text("sla_breached"), kpis["sla_breached"])
        k4.metric(ui_text("escalated"), kpis["escalated"])
        k5.metric(ui_text("resolution_rate"), f"{kpis['resolution_rate']}%")
        st.divider()

        # ── Top priority banner ──────────────────────────────────────
        top = ins.get("top_pair")
        if top:
            risk_color = {"Critical": "#EF4444", "High": "#F59E0B", "Medium": "#3B82F6"}.get(top["risk"], "#6B7280")
            cat_label = _CL.get(top["category"], top["category"])
            sub_label = _SCL.get(top["sub_category"], top["sub_category"])
            st.markdown(
                f"""
                <div style="background:linear-gradient(135deg,#1e3a5f 0%,#2563EB 100%);
                            color:white;border-radius:14px;padding:20px 24px;margin-bottom:8px;">
                    <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;
                                letter-spacing:0.08em;opacity:0.75;margin-bottom:6px;">
                        Highest Priority Investment Area
                    </div>
                    <div style="font-size:1.15rem;font-weight:700;margin-bottom:4px;">
                        {top['zone']} &nbsp;·&nbsp; {cat_label} &nbsp;·&nbsp; {sub_label}
                    </div>
                    <div style="font-size:0.88rem;opacity:0.9;margin-bottom:10px;">
                        {top['count']} complaints &nbsp;|&nbsp;
                        SLA breached: {int(top['sla_breach_rate']*100)}% &nbsp;|&nbsp;
                        Unresolved: {int(top['unresolved_rate']*100)}% &nbsp;|&nbsp;
                        <span style="background:{risk_color};padding:2px 10px;border-radius:20px;
                                     font-size:0.78rem;font-weight:700;">{top['risk']}</span>
                    </div>
                    <div style="font-size:0.9rem;background:rgba(255,255,255,0.15);
                                border-radius:8px;padding:10px 14px;">
                        🔧 {top['action']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.divider()

        # ── Priority investment list + Zone risk side by side ────────
        left_col, right_col = st.columns([3, 2])

        with left_col:
            st.subheader(bilingual_text("ಪ್ರಮುಖ ಹೂಡಿಕೆ ಪ್ರದೇಶಗಳು", "Priority Investment Areas"))
            RISK_COLORS = {"Critical": "#EF4444", "High": "#F59E0B", "Medium": "#3B82F6"}
            for rank, area in enumerate(ins["priority_areas"], 1):
                rc = RISK_COLORS.get(area["risk"], "#6B7280")
                cat_label = _CL.get(area["category"], area["category"])
                sub_label = _SCL.get(area["sub_category"], area["sub_category"])
                with st.container(border=True):
                    c1, c2 = st.columns([1, 8])
                    with c1:
                        st.markdown(
                            f'<div style="background:{rc};color:white;border-radius:8px;'
                            f'padding:8px 4px;text-align:center;font-weight:700;font-size:1.2rem;">'
                            f'#{rank}</div>',
                            unsafe_allow_html=True,
                        )
                    with c2:
                        trend_icon = {"Rising": "📈", "Declining": "📉", "Stable": "➡️", "New": "🆕"}.get(
                            ins["trend"].get(area["category"], "Stable"), "➡️"
                        )
                        st.markdown(
                            f'**{area["zone"]}** &nbsp;·&nbsp; {cat_label} &nbsp;·&nbsp; {sub_label} &nbsp;'
                            f'<span style="background:{rc};color:white;padding:1px 8px;'
                            f'border-radius:12px;font-size:0.72rem;">{area["risk"]}</span> '
                            f'{trend_icon}',
                            unsafe_allow_html=True,
                        )
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric(bilingual_text("ದೂರುಗಳು", "Complaints"), area["count"])
                        m2.metric(bilingual_text("ಸಕ್ರಿಯ ದಿನಗಳು", "Active Days"), area["unique_days"])
                        m3.metric(bilingual_text("SLA ಮೀರಿಕೆ", "SLA Breach"), f"{int(area['sla_breach_rate']*100)}%")
                        m4.metric(bilingual_text("ಪರಿಹಾರವಾಗಿಲ್ಲ", "Unresolved"), f"{int(area['unresolved_rate']*100)}%")
                        st.info(area["action"], icon="🔧")

        with right_col:
            st.subheader(bilingual_text("ವಲಯ ಅಪಾಯ ಸಾರಾಂಶ", "Zone Risk Summary"))
            RISK_COLORS_ZONE = {"Critical": "#EF4444", "High": "#F59E0B", "Medium": "#10B981"}
            for z, zdata in sorted(ins["zone_risk"].items(),
                                   key=lambda x: x[1]["score"], reverse=True):
                rc = RISK_COLORS_ZONE.get(zdata["risk"], "#6B7280")
                cat_label = _CL.get(zdata["top_category"], zdata["top_category"])
                sub_label = _SCL.get(zdata["top_sub_category"], zdata["top_sub_category"])
                st.markdown(
                    f"""
                    <div style="border-left:4px solid {rc};padding:10px 14px;
                                margin-bottom:8px;background:#f8fafc;border-radius:0 10px 10px 0;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="font-weight:700;font-size:0.92rem;">{z}</span>
                            <span style="background:{rc};color:white;padding:2px 10px;
                                         border-radius:20px;font-size:0.72rem;font-weight:700;">
                                {zdata['risk']}
                            </span>
                        </div>
                        <div style="font-size:0.78rem;color:#64748b;margin-top:4px;">
                            {zdata['count']} complaints &nbsp;·&nbsp; {cat_label}
                        </div>
                        <div style="font-size:0.78rem;color:#475569;margin-top:2px;">
                            Top issue: {sub_label}
                        </div>
                        <div style="font-size:0.78rem;color:#475569;margin-top:2px;">
                            SLA breach {int(zdata['sla_breach_rate']*100)}%
                            &nbsp;·&nbsp; Unresolved {int(zdata['unresolved_rate']*100)}%
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.divider()

        # ── Category trend chart ─────────────────────────────────────
        st.subheader(bilingual_text("ವರ್ಗ ಪ್ರವಣತೆ ಮತ್ತು ಅಪಾಯ", "Category Trend & Risk"))
        cat_rows = []
        TREND_ICON = {"Rising": "📈", "Declining": "📉", "Stable": "➡️", "New": "🆕"}
        for cat, cdata in sorted(ins["category_risk"].items(),
                                 key=lambda x: x[1]["score"], reverse=True):
            cat_rows.append({
                "Category": _CL.get(cat, cat),
                "Complaints": cdata["count"],
                "Risk": cdata["risk"],
                "SLA Breach %": f"{int(cdata['sla_breach_rate']*100)}%",
                "Unresolved %": f"{int(cdata['unresolved_rate']*100)}%",
                "Trend": TREND_ICON.get(ins["trend"].get(cat, "Stable"), "➡️") + " " + ins["trend"].get(cat, "Stable"),
                "Top Issue": _SCL.get(cdata["top_sub_category"], cdata["top_sub_category"]),
                "Priority Score": cdata["score"],
            })
        if cat_rows:
            import pandas as _pd
            cat_df = _pd.DataFrame(cat_rows)
            fig = px.bar(
                cat_df, x="Complaints", y="Category", orientation="h",
                color="Priority Score",
                color_continuous_scale=["#10B981", "#F59E0B", "#EF4444"],
                text="Complaints", height=280,
            )
            fig.update_layout(
                margin=dict(l=0, r=20, t=10, b=0),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False,
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(cat_df.drop(columns=["Priority Score"]),
                         use_container_width=True, hide_index=True)

        st.divider()

        # ── Quick wins + Long-term ────────────────────────────────────
        qw_col, lt_col = st.columns(2)
        with qw_col:
            st.subheader(bilingual_text("ತ್ವರಿತ ಜಯಗಳು (≤ 2 ವಾರಗಳು)", "Quick Wins (≤ 2 weeks)"))
            if ins["quick_wins"]:
                for qw in ins["quick_wins"]:
                    st.markdown(f"✅ {qw}")
            else:
                st.info(bilingual_text("ತ್ವರಿತ ಜಯಗಳು ಕಂಡುಬಂದಿಲ್ಲ. ದೂರುಗಳಿಗೆ ನಿರಂತರ ಮೂಲಸೌಕರ್ಯ ಹೂಡಿಕೆ ಅಗತ್ಯ.", "No quick wins identified. Complaints need sustained infrastructure investment."))
        with lt_col:
            st.subheader(bilingual_text("ದೀರ್ಘಾವಧಿ ಹೂಡಿಕೆಗಳು (3–12 ತಿಂಗಳು)", "Long-term Investments (3–12 months)"))
            if ins["long_term"]:
                for lt in ins["long_term"]:
                    st.markdown(f"🏗️ {lt}")
            else:
                st.info(bilingual_text("ದೀರ್ಘಕಾಲೀನ ಮಾದರಿಗಳನ್ನು ನೋಡಲು ಇನ್ನಷ್ಟು ದೂರು ಡೇಟಾ ಸೇರಿಸಿ.", "Add more complaint data to surface long-term patterns."))

# =====================================================================
# Tab 5: Chronic Hotspot AI
# =====================================================================
with tab_hotspot_ai:
    from lib.hotspot_ai import identify_chronic_hotspots
    from lib.labels import CATEGORY_LABELS, CATEGORY_COLORS, SUB_CATEGORY_LABELS

    zone_tag = f" - {active_zone}" if active_zone else ""
    cat_tag = f" / {CATEGORY_LABELS.get(active_category, active_category)}" if active_category else ""
    st.header(f"{ui_text('hotspot_ai_title')}{zone_tag}{cat_tag}")
    st.caption(
        bilingual_text(
            "DBSCAN ಸ್ಥಳೀಯ ಕ್ಲಸ್ಟರಿಂಗ್ ~300 ಮೀ ಒಳಗಿನ ಪುನರಾವರ್ತಿತ ದೂರು ಸ್ಥಳಗಳನ್ನು ಪತ್ತೆಹಚ್ಚುತ್ತದೆ.",
            "DBSCAN spatial clustering detects locations with repeat complaints within ~300 m.",
        )
        + " "
        + bilingual_text(
            "ಪ್ರತಿ ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗೆ ದೂರು ಆವೃತ್ತಿ, ಮರುಕಳಿಕೆ, SLA ಮೀರಿಕೆ ಮತ್ತು ಪರಿಹಾರರಹಿತ ಅನುಪಾತದ ಆಧಾರದಲ್ಲಿ ಅಂಕ ನೀಡಲಾಗುತ್ತದೆ.",
            "Each hotspot is scored on complaint frequency, recurrence, SLA breach rate, and unresolved ratio.",
        )
    )

    col_w1, col_w2 = st.columns([1, 3])
    with col_w1:
        window_days = st.slider(bilingual_text("ವಿಶ್ಲೇಷಣಾ ಅವಧಿ (ದಿನಗಳು)", "Analysis window (days)"), min_value=7, max_value=90, value=60, step=7)

    all_c = load_complaints(active_zone, active_category, None)

    @st.cache_data(ttl=60, show_spinner=False)
    def load_ai_hotspots(zone: str | None, category: str | None, days: int) -> list:
        return identify_chronic_hotspots(all_c, days_window=days, zone=zone, category=category)

    with st.spinner(bilingual_text("ಸ್ಥಳೀಯ ಕ್ಲಸ್ಟರಿಂಗ್ ಚಾಲನೆಗೊಳ್ಳುತ್ತಿದೆ...", "Running spatial clustering...")):
        ai_hotspots = load_ai_hotspots(active_zone, active_category, window_days)

    if not ai_hotspots:
        st.info(bilingual_text("ಪ್ರಸ್ತುತ ಫಿಲ್ಟರ್‌ಗಳು ಮತ್ತು ಸಮಯಾವಧಿಗೆ ದೀರ್ಘಕಾಲೀನ ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗಳು ಕಂಡುಬಂದಿಲ್ಲ.", "No chronic hotspots detected for the current filters and time window. Try widening the window or removing filters."))
    else:
        # Summary chips
        n_critical = sum(1 for h in ai_hotspots if h["severity_label"] == "Critical")
        n_high = sum(1 for h in ai_hotspots if h["severity_label"] == "High")
        n_medium = sum(1 for h in ai_hotspots if h["severity_label"] == "Medium")
        chip1, chip2, chip3, chip4 = st.columns(4)
        chip1.metric(bilingual_text("ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗಳು ಪತ್ತೆಯಾಗಿದೆ", "Hotspots detected"), len(ai_hotspots))
        chip2.metric(bilingual_text("ಅತ್ಯಂತ ಗಂಭೀರ", "Critical"), n_critical)
        chip3.metric(bilingual_text("ಉಚ್ಚ", "High"), n_high)
        chip4.metric(bilingual_text("ಮಧ್ಯಮ", "Medium"), n_medium)

        st.divider()

        # Map
        if ai_hotspots:
            import pandas as _pd

            ai_hotspots_df = _pd.DataFrame(ai_hotspots)
            ai_hotspots_df["category_label"] = ai_hotspots_df["category"].map(lambda k: CATEGORY_LABELS.get(k, k))
            ai_hotspots_df["sub_category_label"] = ai_hotspots_df["sub_category"].map(lambda k: SUB_CATEGORY_LABELS.get(k, k))
            _render_zone_bubble_map(ai_hotspots_df.to_dict("records"), all_c, height=500)

        st.divider()
        st.caption(bilingual_text("ಗುಬ್ಬೆಯ ಗಾತ್ರವು ವಲಯದ ದೀರ್ಘಕಾಲೀನ ಲೋಡ್ ತೋರಿಸುತ್ತದೆ.", "Bubble size shows the chronic load for each zone; colors reflect the severity of the worst hotspot in that zone."))
        st.subheader(bilingual_text("ಶ್ರೇಣಿಬದ್ಧ ಹಾಟ್‌ಸ್ಪಾಟ್ ವಿವರಗಳು", "Ranked hotspot details"))

        for rank, h in enumerate(ai_hotspots, 1):
            cat_label = CATEGORY_LABELS.get(h["category"], h["category"])
            sub_label = SUB_CATEGORY_LABELS.get(h["sub_category"], h["sub_category"])

            with st.container(border=True):
                left, right = st.columns([1, 7])
                with left:
                    st.markdown(
                        f"""
                        <div style="background:{h['badge_color']};color:white;border-radius:10px;
                                    padding:12px 8px;text-align:center;line-height:1.2">
                            <div style="font-size:1.8rem;font-weight:700">#{rank}</div>
                            <div style="font-size:0.72rem;margin-top:2px">{h['severity_label']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with right:
                    st.markdown(f"**{cat_label}** &mdash; {sub_label} &nbsp;·&nbsp; {h['zone']}")
                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Complaints", h["complaint_count"])
                    m2.metric("Active days", h["unique_days_active"])
                    m3.metric("SLA breach", f"{int(h['sla_breach_rate']*100)}%")
                    m4.metric("Unresolved", f"{int(h['unresolved_rate']*100)}%")
                    m5.metric("Severity score", f"{h['severity_score']:.2f}")
                    st.info(h["recommendation"], icon="🤖")
                    if h["recent_complaint_ids"]:
                        st.caption("Recent complaints: " + " · ".join(h["recent_complaint_ids"]))

        # Export table
        st.divider()
        st.subheader("Export table")
        export_rows = []
        for h in ai_hotspots:
            export_rows.append({
                "Severity": h["severity_label"],
                "Score": h["severity_score"],
                "Category": CATEGORY_LABELS.get(h["category"], h["category"]),
                "Sub-category": SUB_CATEGORY_LABELS.get(h["sub_category"], h["sub_category"]),
                "Zone": h["zone"],
                "Complaints": h["complaint_count"],
                "Active Days": h["unique_days_active"],
                "SLA Breach %": f"{int(h['sla_breach_rate']*100)}%",
                "Unresolved %": f"{int(h['unresolved_rate']*100)}%",
                "Lat": h["latitude"],
                "Lon": h["longitude"],
                "Recommendation": h["recommendation"],
            })
        import pandas as _pd
        st.dataframe(_pd.DataFrame(export_rows), use_container_width=True, hide_index=True)


# =====================================================================
# Tab 6: Track & Manage
# =====================================================================
with tab_tracker:
    from lib.labels import SUB_CATEGORY_LABELS

    st.header(ui_text("tracker_title"))
    st.caption(
        ui_text("tracker_caption")
        + " Kannada and Tamil text stays in native script."
    )

    # Status flow definition
    STATUS_FLOW = ["filed", "assigned", "in_progress", "resolved"]
    STATUS_NEXT: dict[str, list[str]] = {
        "filed":       ["assigned", "escalated"],
        "assigned":    ["in_progress", "escalated"],
        "in_progress": ["resolved", "escalated"],
        "resolved":    [],
        "escalated":   ["resolved"],
    }
    STATUS_ICONS = {
        "filed":       "📋",
        "assigned":    "👤",
        "in_progress": "🔧",
        "resolved":    "✅",
        "escalated":   "🚨",
    }
    STATUS_COLORS_HEX = {
        "filed":       "#6B7280",
        "assigned":    "#3B82F6",
        "in_progress": "#F59E0B",
        "resolved":    "#10B981",
        "escalated":   "#EF4444",
    }

    # ── Complaint selector ───────────────────────────────────────────
    lang_options = ["All Languages"] + sorted({language_label(c.get("language")) for c in load_complaints(active_zone, active_category, None)})
    selected_lang_label = st.selectbox(ui_text("complaint_language"), lang_options, key="tracker_language_filter")
    selected_language_code = None if selected_lang_label == "All Languages" else normalize_language_code(next(
        (code for code, label in LANGUAGE_LABELS.items() if label == selected_lang_label), None
    ))

    sel_col, info_col = st.columns([2, 3])

    all_complaints_raw = load_complaints(active_zone, active_category, None)
    if selected_language_code:
        all_complaints_raw = [
            c for c in all_complaints_raw
            if normalize_language_code(c.get("language")) == selected_language_code
        ]

    if not all_complaints_raw:
        st.info(bilingual_text("ಆಯ್ದ ಫಿಲ್ಟರ್‌ಗಳು ಮತ್ತು ಭಾಷೆಗೆ ದೂರುಗಳಿಲ್ಲ.", "No complaints available for the selected filters and language."))
    else:
        with sel_col:
            # Build ID list sorted newest first
            sorted_complaints = sorted(all_complaints_raw, key=lambda c: c["created_at"], reverse=True)
            id_options = [c["complaint_id"] for c in sorted_complaints]

            if "tracker_complaint_id" not in st.session_state:
                st.session_state.tracker_complaint_id = id_options[0]

            selected_id = st.selectbox(
                ui_text("select_complaint_id"),
                options=id_options,
                index=id_options.index(st.session_state.tracker_complaint_id)
                      if st.session_state.tracker_complaint_id in id_options else 0,
                key="tracker_select",
            )
            st.session_state.tracker_complaint_id = selected_id

        with info_col:
            meta = next((c for c in sorted_complaints if c["complaint_id"] == selected_id), None)
            if meta:
                m1, m2, m3 = st.columns(3)
                m1.metric(ui_text("category"), CATEGORY_LABELS.get(meta["category"], meta["category"]))
                m2.metric(ui_text("zone"), meta["zone"])
                m3.metric(ui_text("priority"), meta.get("priority", "—").title())

        st.divider()

        # ── Fetch full complaint detail (with history) ───────────────────
        _detail_error = None
        detail = None
        try:
            detail = load_complaint_detail(selected_id)
        except Exception as exc:
            _detail_error = str(exc)

        if _detail_error:
            st.error(f"Could not load complaint detail: {_detail_error}")
        elif detail is not None:
            current_status = detail.get("status", "filed")
            history = detail.get("history", [])
            # ── Amazon-style tracking timeline ──────────────────────
            def _build_timeline_html(current: str, history: list[dict]) -> str:
                status_times: dict[str, str] = {}
                status_notes: dict[str, str] = {}
                for h in history:
                    ns = h.get("new_status", "")
                    if ns and ns not in status_times:
                        ts = h.get("changed_at", "")[:16].replace("T", " ")
                        status_times[ns] = ts
                        if h.get("note"):
                            status_notes[ns] = h["note"]

                steps = STATUS_FLOW if current != "escalated" else ["filed", "assigned", "in_progress", "escalated"]
                try:
                    cur_idx = steps.index(current)
                except ValueError:
                    cur_idx = 0

                cells = ""
                n = len(steps)
                for i, st_key in enumerate(steps):
                    done = i <= cur_idx
                    active = st_key == current
                    color = STATUS_COLORS_HEX.get(st_key, "#6B7280")
                    icon = STATUS_ICONS.get(st_key, "●")
                    lbl = STATUS_LABELS.get(st_key, st_key)
                    ts = status_times.get(st_key, "Pending")
                    note = status_notes.get(st_key, "")
                    circle_bg = color if done else "#E2E8F0"
                    text_color = "#1e293b" if done else "#94a3b8"
                    ring = f"box-shadow:0 0 0 4px {color}33;" if active else ""
                    note_html = (
                        f'<div style="font-size:0.68rem;color:#64748b;margin-top:2px;'
                        f'max-width:110px;word-break:break-word;">{escape(note)}</div>'
                        if note else ""
                    )
                    line_color = color if i < cur_idx else "#E2E8F0"
                    connector_html = (
                        f'<div style="flex:1;height:3px;background:{line_color};'
                        f'align-self:flex-start;position:relative;top:24px;z-index:0;"></div>'
                        if i < n - 1 else ""
                    )
                    cells += f"""
                    <div style="display:flex;flex-direction:column;align-items:center;flex:1;z-index:1;">
                        <div style="width:48px;height:48px;border-radius:50%;
                                    background:{circle_bg};border:2.5px solid {color};
                                    display:flex;align-items:center;justify-content:center;
                                    font-size:1.3rem;{ring}">
                            {icon if done else "○"}
                        </div>
                        <div style="margin-top:8px;font-size:0.78rem;
                                    font-weight:{'700' if active else '600'};
                                    color:{text_color};text-align:center;">{escape(lbl)}</div>
                        <div style="font-size:0.68rem;color:#94a3b8;text-align:center;">{escape(ts)}</div>
                        {note_html}
                    </div>
                    {connector_html}
                    """
                return f"""
                <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;
                            padding:28px 24px 20px;">
                    <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                                letter-spacing:0.07em;color:#64748b;margin-bottom:20px;">
                        {bilingual_text("ದೂರು ಸ್ಥಿತಿ", "Complaint Status")} — {escape(selected_id)}
                    </div>
                    <div style="display:flex;align-items:flex-start;gap:0;position:relative;">
                        {cells}
                    </div>
                </div>
                """

            try:
                timeline_html = f"""
                <html>
                <head>
                    <meta charset="utf-8">
                    <style>
                        html, body {{
                            margin: 0;
                            padding: 0;
                            background: transparent;
                            font-family: Inter, Segoe UI, sans-serif;
                        }}
                    </style>
                </head>
                <body>
                    {_build_timeline_html(current_status, history)}
                </body>
                </html>
                """
                components.html(timeline_html, height=430, scrolling=False)
            except Exception as exc:
                st.info(bilingual_text("ಸಮಯರೇಖೆ ಈಗ ಲಭ್ಯವಿಲ್ಲ, ಆದರೆ ಕೆಳಗಿನ ದೂರು ವಿವರಗಳು ಲಭ್ಯವಿವೆ.", "Timeline preview is unavailable right now, but the complaint details below are still accessible."))
                st.caption(f"Timeline render error: {exc}")
            st.write("")

            # ── Complaint detail card ────────────────────────────────
            with st.container(border=True):
                d1, d2 = st.columns(2)
                with d1:
                    st.markdown(f"**{ui_text('category')}:** {CATEGORY_LABELS.get(detail['category'], detail['category'])}")
                    st.markdown(f"**ಉಪ-ವರ್ಗ (Sub-category):** {SUB_CATEGORY_LABELS.get(detail.get('sub_category',''), detail.get('sub_category',''))}")
                    st.markdown(f"**{ui_text('zone')}:** {detail.get('zone','—')}  |  **Ward:** {detail.get('ward') or '—'}")
                    st.markdown(f"**ಸಲ್ಲಿಸಿದ ಸಮಯ (Filed):** {detail['created_at'][:16].replace('T',' ')}")
                with d2:
                    st.markdown(f"**{ui_text('department')}:** {detail.get('assigned_department','—')}")
                    sla_icon = "🔴" if detail.get("sla_breached") else "🟢"
                    sla_txt = "Breached" if detail.get("sla_breached") else "On track"
                    st.markdown(f"**SLA Due:** {detail.get('sla_due_at','—')[:16].replace('T',' ')}  {sla_icon} {sla_txt}")
                    st.markdown(f"**{ui_text('priority')}:** {detail.get('priority','—').title()}")
                    esc = detail.get("escalation_level", 0)
                    if esc:
                        from lib.labels import ESCALATION_BADGE
                        st.markdown(f"**ಎಸ್ಕಲೇಟ್ ಮಾಡಲಾಗಿದೆ (Escalated to):** {ESCALATION_BADGE.get(esc, str(esc))}")
                st.markdown(f"**{ui_text('language')}:** {language_label(detail.get('language_code') or detail.get('language'))}")
                if detail.get("description"):
                    st.markdown(f"**ನಾಗರಿಕ ವರದಿ (Citizen report):** {detail.get('description_native') or detail['description']}")

            # ── Admin action panel ───────────────────────────────────
            next_statuses = STATUS_NEXT.get(current_status, [])
            if not next_statuses:
                st.success(bilingual_text("ಈ ದೂರು ಸಂಪೂರ್ಣ ಪರಿಹಾರವಾಗಿದೆ. ಇನ್ನಷ್ಟು ಕ್ರಮ ಅಗತ್ಯವಿಲ್ಲ.", "This complaint is fully resolved. No further actions required."), icon="✅")
            else:
                st.subheader(bilingual_text("ಆಡಳಿತ ಕ್ರಮಗಳು", "Admin Actions"))
                action_col, note_col = st.columns([1, 2])
                with note_col:
                    action_note = st.text_input(
                        bilingual_text("ಕೆಲಸದ ಟಿಪ್ಪಣಿ ಸೇರಿಸಿ (ಐಚ್ಛಿಕ)", "Add a work note (optional)"),
                        placeholder="e.g. Assigned to Zone North field team, work begins tomorrow",
                        key="tracker_note",
                    )
                with action_col:
                    for next_st in next_statuses:
                        lbl = STATUS_LABELS.get(next_st, next_st)
                        icon = STATUS_ICONS.get(next_st, "")
                        if next_st == "escalated":
                            if st.button(f"{icon} Escalate", key=f"btn_escalate_{selected_id}",
                                         use_container_width=True):
                                try:
                                    escalate_complaint(selected_id)
                                    st.cache_data.clear()
                                    st.success(bilingual_text("ದೂರು ಎಸ್ಕಲೇಟ್ ಮಾಡಲಾಗಿದೆ.", "Complaint escalated."))
                                    st.rerun()
                                except Exception as exc:
                                    st.error(str(exc))
                        else:
                            btn_label = {
                                "assigned":    bilingual_text("👤 ದೂರು ಹಂಚಿಕೆ", "Assign Complaint"),
                                "in_progress": bilingual_text("🔧 ಪ್ರಗತಿಯಲ್ಲಿದೆ ಎಂದು ಗುರುತು", "Mark In Progress"),
                                "resolved":    bilingual_text("✅ ಪರಿಹರಿಸಲಾಗಿದೆ ಎಂದು ಗುರುತು", "Mark Resolved"),
                            }.get(next_st, f"{icon} Move to {lbl}")
                            if st.button(btn_label, key=f"btn_{next_st}_{selected_id}",
                                         type="primary" if next_st == "resolved" else "secondary",
                                         use_container_width=True):
                                try:
                                    update_complaint_status(selected_id, next_st, action_note or None)
                                    st.cache_data.clear()
                                    st.success(bilingual_text(f"ಸ್ಥಿತಿ ನವೀಕರಿಸಲಾಗಿದೆ: **{lbl}**.", f"Status updated to **{lbl}**."))
                                    st.rerun()
                                except Exception as exc:
                                    st.error(str(exc))

            # ── Activity log ─────────────────────────────────────────
            if history:
                st.divider()
                st.subheader(bilingual_text("ಕ್ರಿಯೆಗಳ ಲಾಗ್", "Activity Log"))
                import pandas as _pd
                hist_rows = []
                for h in sorted(history, key=lambda x: x["changed_at"], reverse=True):
                    old = STATUS_LABELS.get(h.get("old_status", ""), h.get("old_status") or "—")
                    new = STATUS_LABELS.get(h.get("new_status", ""), h.get("new_status", ""))
                    hist_rows.append({
                        "Time": h.get("changed_at", "")[:16].replace("T", " "),
                        "From": old,
                        "To": new,
                        "Note": h.get("note") or "—",
                    })
                st.dataframe(_pd.DataFrame(hist_rows), use_container_width=True, hide_index=True)


# =====================================================================
# Tab 7: Complaint Table
# =====================================================================
with tab_table:
    st.header(ui_text("complaints_title"))
    st.caption(bilingual_text("ವ್ಯಕ್ತಿಗತ ದೂರು ವಿವರಗಳಿಗೆ ಇಳಿದು ನೋಡಿರಿ.", "Drill into individual complaints.") + " Filters apply on top of the zone filter in the sidebar, and native scripts are preserved.")

    # Additional per-tab filters (zone comes from sidebar)
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        cat_options = [ui_text("all_categories")] + [_ka(CATEGORY_LABELS[k]) for k in CATEGORIES]
        selected_cat_label: str = st.selectbox(ui_text("category"), cat_options)
        selected_cat: str | None = None
        if selected_cat_label != ui_text("all_categories"):
            # Reverse map label -> key
            selected_cat = next(
                (k for k, v in CATEGORY_LABELS.items() if v == selected_cat_label), None
            )

    with col_f2:
        status_options = [bilingual_text("ಎಲ್ಲಾ ಸ್ಥಿತಿಗಳು", "All Statuses")] + [_ka(STATUS_LABELS[s]) for s in STATUSES]
        selected_status_label: str = st.selectbox(ui_text("status"), status_options)
        selected_status: str | None = None
        if selected_status_label != bilingual_text("ಎಲ್ಲಾ ಸ್ಥಿತಿಗಳು", "All Statuses"):
            selected_status = next(
                (k for k, v in STATUS_LABELS.items() if v == selected_status_label), None
            )

    with col_f3:
        sort_options = ["Newest first", "Oldest first", "Priority (high first)"]
        sort_by: str = st.selectbox(bilingual_text("ಕ್ರಮಬದ್ಧಗೊಳಿಸಿ", "Sort by"), sort_options)

    with col_f4:
        table_lang_options = [bilingual_text("ಎಲ್ಲಾ ಭಾಷೆಗಳು", "All Languages"), bilingual_text("ಕನ್ನಡ", "Kannada"), bilingual_text("ತಮಿಳು", "Tamil"), bilingual_text("ಇಂಗ್ಲಿಷ್", "English")]
        selected_table_lang = st.selectbox(ui_text("language"), table_lang_options, key="table_language_filter")
        selected_table_language_code = None if selected_table_lang == bilingual_text("ಎಲ್ಲಾ ಭಾಷೆಗಳು", "All Languages") else normalize_language_code(next(
            (code for code, label in LANGUAGE_LABELS.items() if label == selected_table_lang), None
        ))

    try:
        raw = load_complaints(active_zone, active_category or selected_cat, selected_status)
    except (ConnectionError, RuntimeError, TimeoutError) as exc:
        st.error(f"Could not load complaints: {exc}")
        raw = []

    comp_df = complaints_to_df(raw)
    if selected_table_language_code:
        comp_df = comp_df[comp_df["language_code"] == selected_table_language_code]
    if comp_df.empty:
        st.info(bilingual_text("ಆಯ್ದ ಫಿಲ್ಟರ್‌ಗಳು ಮತ್ತು ಭಾಷೆಗೆ ದೂರುಗಳಿಲ್ಲ.", "No complaints match the selected filters and language."))
    else:
        # Sort
        if sort_by == "Newest first":
            comp_df = comp_df.sort_values("created_at", ascending=False)
        elif sort_by == "Oldest first":
            comp_df = comp_df.sort_values("created_at", ascending=True)
        elif sort_by == "Priority (high first)":
            comp_df = comp_df.sort_values(
                ["priority", "created_at"], ascending=[True, False]
            )  # "high" < "normal" alphabetically, so ascending=True puts high first

        st.caption(bilingual_text(f"{len(comp_df)} ದೂರುಗಳನ್ನು ತೋರಿಸಲಾಗುತ್ತಿದೆ", f"Showing {len(comp_df)} complaints"))

        display_cols = {
            "complaint_id": bilingual_text("ದೂರು ಐಡಿ", "Complaint ID"),
            "category_label": bilingual_text("ವರ್ಗ", "Category"),
            "sub_category_label": bilingual_text("ಉಪ-ವರ್ಗ", "Sub-category"),
            "zone": bilingual_text("ವಲಯ", "Zone"),
            "ward": "Ward",
            "language_label": bilingual_text("ಭಾಷೆ", "Language"),
            "description_native": bilingual_text("ನಾಗರಿಕ ವರದಿ", "Citizen Report"),
            "status_label": bilingual_text("ಸ್ಥಿತಿ", "Status"),
            "priority_label": bilingual_text("ಪ್ರಾಥಮ್ಯ", "Priority"),
            "created_date": bilingual_text("ಸಲ್ಲಿಸಿದ ದಿನಾಂಕ", "Filed On"),
            "sla_breached": bilingual_text("SLA ಮೀರಿದೆ", "SLA Breached"),
        }
        existing = {k: v for k, v in display_cols.items() if k in comp_df.columns}
        out_df = comp_df[list(existing.keys())].rename(columns=existing)

        if "SLA Breached" in out_df.columns:
            out_df["SLA Breached"] = out_df["SLA Breached"].map({True: "⚠ Yes", False: "No"})
        if "Urgency" in out_df.columns:
            out_df["Urgency"] = out_df["Urgency"].map({
                "Critical": "🚨 Critical",
                "High": "⚠ High",
                "Normal": "Normal",
            })

        st.dataframe(out_df, use_container_width=True, hide_index=True, height=500)
