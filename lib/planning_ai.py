"""
Sarvam-powered preventive planning insights.

Uses Sarvam chat completions to turn the deterministic planning signals into a
polished executive summary and action list for city officials.
"""

from __future__ import annotations

import json
import os
import re
import ast
from typing import Optional

import requests


SARVAM_API_URL = "https://api.sarvam.ai/v1/chat/completions"


def _extract_json_text(raw_text: str) -> str:
    json_text = raw_text.strip()
    if json_text.startswith("```"):
        parts = json_text.split("```")
        if len(parts) >= 2:
            json_text = parts[1].strip()
            if json_text.startswith("json"):
                json_text = json_text[4:].strip()
    if not json_text.startswith("{"):
        match = re.search(r"\{.*\}", json_text, flags=re.S)
        if match:
            json_text = match.group(0).strip()
    return json_text


def _parse_loose_json(raw_text: str) -> dict:
    json_text = _extract_json_text(raw_text)
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        pass

    # Try to recover from single-quoted or Python-dict-style responses.
    python_like = json_text.replace("true", "True").replace("false", "False").replace("null", "None")
    try:
        parsed = ast.literal_eval(python_like)
        if isinstance(parsed, dict):
            return parsed
    except Exception:  # noqa: BLE001
        pass

    # As a last resort, try to isolate the outermost JSON object.
    start = json_text.find("{")
    end = json_text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = json_text[start : end + 1]
        return json.loads(candidate)

    raise json.JSONDecodeError("Could not parse Sarvam JSON", json_text, 0)


def _summarize_response(raw_text: str) -> dict:
    parsed = _parse_loose_json(raw_text)
    parsed["ok"] = True
    parsed["error"] = None
    parsed["raw_text"] = raw_text
    return parsed


def _build_fallback_report(hotspots: list[dict], summary: dict, zone: Optional[str], category: Optional[str], reason: str) -> dict:
    total = summary.get("total_complaints", 0)
    resolution_rate = round(summary.get("by_status", {}).get("resolved", 0) / total * 100, 1) if total else 0
    top_hotspots = sorted(hotspots, key=lambda h: h.get("priority_score", h.get("complaint_count", 0)), reverse=True)[:5]

    priority_investments = []
    for index, h in enumerate(top_hotspots, 1):
        area = f"{h.get('zone', 'Unknown')} / {h.get('category', 'unknown')} / {h.get('sub_category', 'unknown')}"
        priority_investments.append(
            {
                "rank": index,
                "area": area,
                "action": h.get("action") or "Investigate and dispatch a maintenance team.",
                "rationale": (
                    f"{h.get('complaint_count', 0)} complaints in this cluster with "
                    f"{int((h.get('sla_breach_rate') or 0) * 100)}% SLA breaches and "
                    f"{int((h.get('unresolved_rate') or 0) * 100)}% unresolved."
                ),
                "urgency": h.get("risk", "Medium"),
                "estimated_impact": "Reduce repeat complaints and stabilize the affected locality.",
            }
        )

    zone_focus = []
    by_zone = summary.get("by_zone", {})
    for zone_name, count in sorted(by_zone.items(), key=lambda item: item[1], reverse=True)[:5]:
        relevant = next((h for h in top_hotspots if h.get("zone") == zone_name), None)
        zone_focus.append(
            {
                "zone": zone_name,
                "risk_level": "High" if count >= max(by_zone.values() or [0]) else "Medium",
                "key_issue": relevant.get("sub_category", "repeat complaints") if relevant else "repeat complaints",
                "recommendation": relevant.get("action", "Inspect the dominant complaint cluster and assign a field team.") if relevant else "Inspect the dominant complaint cluster and assign a field team.",
            }
        )

    quick_wins = [h.get("action") for h in top_hotspots[:3] if h.get("action")]
    if not quick_wins:
        quick_wins = [
            "Dispatch field inspection to the highest volume complaint clusters.",
            "Clear immediate backlog in the dominant zone.",
            "Shortlist repeat hotspots for rapid maintenance intervention.",
        ]

    long_term = [
        "Prioritize drainage, road, and pipeline upgrades in the recurrent hotspots.",
        "Use the zone-level risk ranking to plan preventive capital works.",
        "Track repeat complaints monthly and reallocate resources where recurrence stays high.",
    ]

    return {
        "ok": True,
        "error": None,
        "executive_summary": (
            f"The dashboard currently shows {total} complaints with a {resolution_rate}% resolution rate across "
            f"{len(by_zone)} zones."
        ),
        "priority_investments": priority_investments,
        "zone_focus": zone_focus,
        "quick_wins": quick_wins[:5],
        "long_term": long_term[:5],
        "raw_text": reason,
        "model_used": os.getenv("SARVAM_MODEL", "sarvam-30b"),
        "source": "fallback",
    }


def _sarvam_chat_json(system_prompt: str, user_prompt: str, model: str, api_key: str) -> tuple[dict | None, str, str | None]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 1800,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(SARVAM_API_URL, headers=headers, json=payload, timeout=25)
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices") or []
    if not choices:
        return None, data.get("model", model), "Sarvam response did not include choices."

    message = choices[0].get("message", {})
    raw_text = message.get("content") or message.get("reasoning_content") or data.get("output_text") or ""
    if not raw_text:
        return None, data.get("model", model), "Sarvam response content was empty."

    return {"raw_text": raw_text, "data": data}, data.get("model", model), None


def _build_context(hotspots: list[dict], summary: dict, zone: Optional[str], category: Optional[str]) -> dict:
    total = summary.get("total_complaints", 0)
    resolved = summary.get("by_status", {}).get("resolved", 0)
    sla_breached = summary.get("sla_breached_count", 0)
    by_cat = summary.get("by_category", {})
    by_zone = summary.get("by_zone", {})

    condensed_hotspots = []
    for h in hotspots[:12]:
        condensed_hotspots.append(
            {
                "category": h.get("category"),
                "sub_category": h.get("sub_category"),
                "zone": h.get("zone"),
                "complaint_count": h.get("complaint_count"),
                "unique_days": h.get("unique_days"),
                "sla_breach_rate": h.get("sla_breach_rate"),
                "unresolved_rate": h.get("unresolved_rate"),
                "risk": h.get("risk"),
                "priority_score": h.get("priority_score"),
                "action": h.get("action"),
            }
        )

    return {
        "scope": {
            "zone": zone or "All Zones",
            "category": category or "All Categories",
        },
        "summary": {
            "total_complaints": total,
            "resolved": resolved,
            "sla_breached": sla_breached,
            "resolution_rate_pct": round(resolved / total * 100, 1) if total else 0,
            "by_category": by_cat,
            "by_zone": by_zone,
        },
        "hotspots": condensed_hotspots,
    }


def generate_planning_insights(
    hotspots: list[dict],
    summary: dict,
    zone: Optional[str] = None,
    category: Optional[str] = None,
) -> dict:
    """
    Call Sarvam to turn the planning signals into a structured report.

    Returns:
        ok, error, executive_summary, priority_investments, zone_focus,
        quick_wins, long_term, raw_text, model_used
    """
    api_key = os.getenv("SARVAM_API_KEY", "")
    if not api_key:
        return {
            "ok": False,
            "error": "SARVAM_API_KEY not set. Add it to your .env file to enable AI insights.",
        }

    model = os.getenv("SARVAM_MODEL", "sarvam-30b")
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a senior urban infrastructure analyst advising the Municipal "
                    "Commissioner of Karnataka on preventive infrastructure investment. "
                    "Your recommendations are data-driven, specific, and directly actionable. "
                    "Respond ONLY with valid JSON matching the schema described in the user message."
                ),
            },
            {
                "role": "user",
                "content": f"""Analyse the municipal complaint data below and produce a preventive planning report.

DATA:
{json.dumps(_build_context(hotspots, summary, zone, category), indent=2)}

Return a JSON object with exactly these keys:
{{
  "executive_summary": "<2-3 sentence overview of the key infrastructure risks and investment priorities>",
  "priority_investments": [
    {{
      "rank": 1,
      "area": "<category / sub-category / zone>",
      "action": "<specific infrastructure action>",
      "rationale": "<why this is the top priority - cite numbers from the data>",
      "urgency": "Critical" | "High" | "Medium",
      "estimated_impact": "<expected reduction in complaints or improvement>"
    }}
  ],
  "zone_focus": [
    {{
      "zone": "<zone name>",
      "risk_level": "High" | "Medium" | "Low",
      "key_issue": "<dominant complaint type>",
      "recommendation": "<one targeted action for this zone>"
    }}
  ],
  "quick_wins": [
    "<action completable within 2 weeks with high impact>"
  ],
  "long_term": [
    "<structural investment needed over 3-12 months>"
  ]
}}

Use actual numbers from the data. Be specific about zones, categories, and sub-categories.
Do not include any text outside the JSON object.""",
            },
        ],
        "temperature": 0.2,
        "max_tokens": 2000,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(SARVAM_API_URL, headers=headers, json=payload, timeout=25)
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        return {"ok": False, "error": f"Sarvam request timed out: {exc}"}
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        body = exc.response.text if exc.response is not None else ""
        return {"ok": False, "error": f"Sarvam API error ({status}): {body}"}
    except requests.exceptions.RequestException as exc:
        return {"ok": False, "error": f"Sarvam request failed: {exc}"}

    try:
        data = response.json()
    except Exception as exc:  # noqa: BLE001
        return _build_fallback_report(hotspots, summary, zone, category, f"Could not decode Sarvam JSON response: {exc}")

    choices = data.get("choices") or []
    if not choices:
        return _build_fallback_report(hotspots, summary, zone, category, "Sarvam response did not include choices.")

    message = choices[0].get("message", {})
    raw_text = (
        message.get("content")
        or data.get("output_text")
        or message.get("reasoning_content")
        or ""
    )
    if not raw_text:
        return _build_fallback_report(hotspots, summary, zone, category, "Sarvam response content was empty.")

    try:
        parsed = _summarize_response(raw_text)
        parsed["model_used"] = data.get("model", model)
        return parsed
    except Exception as exc:  # noqa: BLE001
        return _build_fallback_report(hotspots, summary, zone, category, f"Could not parse Sarvam response: {exc}")


def generate_urgent_alert_digest(complaints: list[dict]) -> dict:
    """Generate a short Sarvam-backed alert digest for critical / SLA-breached complaints."""
    api_key = os.getenv("SARVAM_API_KEY", "")
    if not api_key:
        return {
            "ok": False,
            "error": "SARVAM_API_KEY not set.",
        }

    model = os.getenv("SARVAM_MODEL", "sarvam-30b")
    urgent = []
    for c in complaints[:8]:
        urgent.append(
            {
                "complaint_id": c.get("complaint_id"),
                "category": c.get("category"),
                "sub_category": c.get("sub_category"),
                "zone": c.get("zone"),
                "status": c.get("status"),
                "priority": c.get("priority"),
                "sla_breached": c.get("sla_breached"),
                "description": c.get("description"),
                "language": c.get("language"),
            }
        )

    if not urgent:
        return {
            "ok": True,
            "source": "fallback",
            "model_used": "deterministic-summary",
            "headline": "No urgent complaints detected right now.",
            "summary": "No critical or SLA-breached complaints are currently in the selected scope.",
            "alerts": [],
            "recommended_action": "Keep monitoring the dashboard and refresh after new complaints arrive.",
        }

    system_prompt = (
        "You are a municipal operations alerting assistant. "
        "You produce very short, actionable urgent alerts. "
        "Return only valid JSON."
    )
    user_prompt = f"""Create an alert digest for critical and SLA-breached complaints.

DATA:
{json.dumps(urgent, indent=2)}

Return exactly this JSON shape:
{{
  "headline": "One short headline for the dashboard",
  "summary": "One short paragraph (1-2 sentences) with the key issue and immediate action",
  "alerts": [
    {{"complaint_id": "ID", "message": "one sentence alert", "severity": "Critical" | "SLA Breach"}}
  ],
  "recommended_action": "One immediate operational action"
}}

Do not include any text outside the JSON object. Keep all complaint IDs unchanged."""

    try:
        result, model_used, error = _sarvam_chat_json(system_prompt, user_prompt, model, api_key)
        if error:
            raise RuntimeError(error)
        raw_text = result["raw_text"] if result else ""
        parsed = _summarize_response(raw_text)
        parsed["model_used"] = model_used
        parsed["source"] = "sarvam"
        return parsed
    except Exception as exc:  # noqa: BLE001
        critical_count = sum(1 for c in urgent if c.get("priority") == "high" or c.get("status") == "escalated")
        sla_count = sum(1 for c in urgent if c.get("sla_breached"))
        top = urgent[0]
        return {
            "ok": True,
            "source": "fallback",
            "model_used": "deterministic-summary",
            "headline": f"{critical_count} critical and {sla_count} SLA-breached complaints need attention",
            "summary": (
                f"{top.get('complaint_id')} in {top.get('zone')} remains urgent. "
                f"Review the highest-risk complaints first and dispatch the field team immediately."
            ),
            "alerts": [
                {
                    "complaint_id": item.get("complaint_id"),
                    "message": f"{item.get('zone')} / {item.get('category')} requires immediate review.",
                    "severity": "Critical" if item.get("priority") == "high" or item.get("status") == "escalated" else "SLA Breach",
                }
                for item in urgent[:5]
            ],
            "recommended_action": "Dispatch the field team and notify the zonal officer now.",
            "error": str(exc),
        }
