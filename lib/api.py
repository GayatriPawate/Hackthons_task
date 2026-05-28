"""
API wrapper. Reads from mock_data when USE_MOCK_DATA=true (the default),
or calls Member A's FastAPI backend when USE_MOCK_DATA=false.

Set the API base URL with the API_BASE_URL env variable. Default is
http://localhost:8000 for local development.
"""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

_USE_MOCK: bool = os.getenv("USE_MOCK_DATA", "true").lower() in ("true", "1", "yes")
_API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

# Lazy import so that when running with the real API we don't load mock data
if _USE_MOCK:
    from lib import mock_data as _mock


def _real_get(path: str, params: dict | None = None) -> dict | list:
    import requests

    url = f"{_API_BASE_URL}{path}"
    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError as exc:
        raise ConnectionError(
            f"Cannot reach the backend API at {_API_BASE_URL}. "
            "Check that Member A's server is running, or set USE_MOCK_DATA=true."
        ) from exc
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(f"API returned an error: {exc.response.status_code} for {url}") from exc
    except requests.exceptions.Timeout as exc:
        raise TimeoutError(f"API request timed out for {url}") from exc


def get_summary(zone: Optional[str] = None, category: Optional[str] = None) -> dict:
    if _USE_MOCK:
        return _mock.get_summary(zone=zone, category=category)

    if zone or category:
        # Backend endpoints don't support these filters natively — compute client-side.
        from lib.transform import complaints_to_summary
        complaints = get_complaints(zone=zone, category=category)
        return complaints_to_summary(complaints)

    return _real_get("/analytics/summary")  # type: ignore[return-value]


def get_trends(days: int = 30, zone: Optional[str] = None, category: Optional[str] = None) -> dict:
    if _USE_MOCK:
        return _mock.get_trends(days=days, zone=zone, category=category)

    data = _real_get("/analytics/trends", params={"days": days})

    if zone or category:
        # Re-build trend series from filtered complaints client-side
        from datetime import datetime, timedelta
        from lib.labels import CATEGORIES

        complaints = get_complaints(zone=zone, category=category)
        now = datetime.utcnow()
        cutoff = now - timedelta(days=days)
        date_map: dict = {}
        for c in complaints:
            d = c["created_at"][:10]
            ts = datetime.fromisoformat(c["created_at"])
            if ts < cutoff:
                continue
            if d not in date_map:
                date_map[d] = {cat: 0 for cat in CATEGORIES}
            date_map[d][c["category"]] += 1

        series = []
        for i in range(days):
            d = (cutoff + timedelta(days=i + 1)).strftime("%Y-%m-%d")
            row = {"date": d}
            row.update(date_map.get(d, {cat: 0 for cat in CATEGORIES}))
            series.append(row)
        return {"days": days, "series": series}

    return data  # type: ignore[return-value]


def get_hotspots(zone: Optional[str] = None, category: Optional[str] = None) -> dict:
    if _USE_MOCK:
        return _mock.get_hotspots(zone=zone, category=category)

    data = _real_get("/analytics/hotspots")
    hotspots = data.get("hotspots", []) if isinstance(data, dict) else []

    # If backend returns no hotspots, compute from complaints using zone-based clustering
    if not hotspots:
        from lib.hotspot_ai import identify_chronic_hotspots
        all_c = get_complaints()
        ai_spots = identify_chronic_hotspots(all_c, days_window=60)
        hotspots = [
            {
                "category":       h["category"],
                "sub_category":   h["sub_category"],
                "latitude":       h["latitude"],
                "longitude":      h["longitude"],
                "complaint_count": h["complaint_count"],
                "zone":           h["zone"],
                "recommendation": h["recommendation"],
            }
            for h in ai_spots
        ]

    if zone:
        hotspots = [h for h in hotspots if h.get("zone") == zone]
    if category:
        hotspots = [h for h in hotspots if h.get("category") == category]

    return {"hotspots": hotspots}


def get_complaints(
    zone: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
) -> list[dict]:
    if _USE_MOCK:
        return _mock.get_complaints(zone=zone, category=category, status=status)

    params: dict[str, str] = {}
    if zone:
        params["zone"] = zone
    if category:
        params["category"] = category
    if status:
        params["status"] = status
    return _real_get("/complaints", params=params)  # type: ignore[return-value]


def get_complaint(complaint_id: str) -> dict:
    """Fetch a single complaint with full history from the /complaints list endpoint."""
    all_c = get_complaints()
    for c in all_c:
        if c["complaint_id"] == complaint_id:
            return c
    raise RuntimeError(f"Complaint {complaint_id} not found")


def update_complaint_status(complaint_id: str, new_status: str, note: str | None = None) -> dict:
    """PATCH /complaints/{id}/status — move complaint to a new status with an optional note."""
    import requests

    url = f"{_API_BASE_URL}/complaints/{complaint_id}/status"
    payload: dict = {"new_status": new_status}
    if note:
        payload["note"] = note
    try:
        resp = requests.patch(url, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(
            f"Status update failed ({exc.response.status_code}): {exc.response.text}"
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise ConnectionError(f"Cannot reach API at {_API_BASE_URL}") from exc


def escalate_complaint(complaint_id: str) -> dict:
    """POST /complaints/{id}/escalate."""
    import requests

    url = f"{_API_BASE_URL}/complaints/{complaint_id}/escalate"
    try:
        resp = requests.post(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(
            f"Escalation failed ({exc.response.status_code}): {exc.response.text}"
        ) from exc
    except requests.exceptions.ConnectionError as exc:
        raise ConnectionError(f"Cannot reach API at {_API_BASE_URL}") from exc


def is_mock_mode() -> bool:
    return _USE_MOCK


def api_base_url() -> str:
    return _API_BASE_URL
