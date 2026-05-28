"""Pandas helpers that convert raw API JSON into chart-ready DataFrames."""

from __future__ import annotations

import pandas as pd

from lib.labels import (
    CATEGORY_COLORS,
    CATEGORY_LABELS,
    STATUS_COLORS,
    STATUS_LABELS,
    LANGUAGE_LABELS,
    SUB_CATEGORY_LABELS,
    PRIORITY_LABELS,
)
from lib.sarvam_text import enrich_complaint_record


def summary_to_category_df(summary: dict) -> pd.DataFrame:
    data = summary["by_category"]
    df = pd.DataFrame(
        {
            "Category": [CATEGORY_LABELS.get(k, k) for k in data],
            "Complaints": list(data.values()),
            "key": list(data.keys()),
            "color": [CATEGORY_COLORS.get(k, "#6B7280") for k in data],
        }
    )
    return df.sort_values("Complaints", ascending=True)


def summary_to_zone_df(summary: dict) -> pd.DataFrame:
    data = summary["by_zone"]
    df = pd.DataFrame(
        {
            "Zone": list(data.keys()),
            "Complaints": list(data.values()),
        }
    )
    return df.sort_values("Complaints", ascending=True)


def summary_to_status_df(summary: dict) -> pd.DataFrame:
    data = summary["by_status"]
    df = pd.DataFrame(
        {
            "Status": [STATUS_LABELS.get(k, k) for k in data],
            "Count": list(data.values()),
            "key": list(data.keys()),
            "color": [STATUS_COLORS.get(k, "#6B7280") for k in data],
        }
    )
    return df.sort_values("Count", ascending=True)


def trends_to_df(trends: dict) -> pd.DataFrame:
    """Returns a DataFrame indexed by date with one column per category."""
    series = trends.get("series", [])
    if not series:
        return pd.DataFrame()
    df = pd.DataFrame(series)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()

    # Rename category keys to human labels
    rename_map = {k: CATEGORY_LABELS.get(k, k) for k in df.columns}
    df = df.rename(columns=rename_map)
    return df


def hotspots_to_df(hotspots: dict) -> pd.DataFrame:
    data = hotspots.get("hotspots", [])
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df["category_label"] = df["category"].map(lambda k: CATEGORY_LABELS.get(k, k))
    df["sub_category_label"] = df["sub_category"].map(
        lambda k: SUB_CATEGORY_LABELS.get(k, k)
    )
    return df.sort_values("complaint_count", ascending=False).reset_index(drop=True)


def complaints_to_df(complaints: list[dict]) -> pd.DataFrame:
    if not complaints:
        return pd.DataFrame()
    df = pd.DataFrame([enrich_complaint_record(c) for c in complaints])
    df["category_label"] = df["category"].map(lambda k: CATEGORY_LABELS.get(k, k))
    df["sub_category_label"] = df["sub_category"].map(
        lambda k: SUB_CATEGORY_LABELS.get(k, k)
    )
    df["status_label"] = df["status"].map(lambda k: STATUS_LABELS.get(k, k))
    df["priority_label"] = df["priority"].map(lambda k: PRIORITY_LABELS.get(k, k))
    df["language_label"] = df["language_code"].map(lambda k: LANGUAGE_LABELS.get(k, k or "Unknown"))
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["created_date"] = df["created_at"].dt.strftime("%Y-%m-%d")
    return df


def complaints_to_summary(complaints: list[dict]) -> dict:
    """Compute a /analytics/summary-shaped dict from a list of complaint rows.

    Used by the real-API path when a zone/category filter is active.
    """
    from lib.labels import CATEGORIES, STATUSES

    by_category: dict[str, int] = {cat: 0 for cat in CATEGORIES}
    by_status: dict[str, int] = {s: 0 for s in STATUSES}
    by_zone: dict[str, int] = {}
    sla_breached_count = 0

    for c in complaints:
        by_category[c.get("category", "")] = by_category.get(c.get("category", ""), 0) + 1
        by_status[c.get("status", "")] = by_status.get(c.get("status", ""), 0) + 1
        by_zone[c.get("zone", "")] = by_zone.get(c.get("zone", ""), 0) + 1
        if c.get("sla_breached"):
            sla_breached_count += 1

    return {
        "total_complaints": len(complaints),
        "by_category": by_category,
        "by_status": by_status,
        "by_zone": by_zone,
        "sla_breached_count": sla_breached_count,
    }
