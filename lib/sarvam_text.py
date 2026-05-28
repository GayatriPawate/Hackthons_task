"""Sarvam-backed text helpers for complaint language handling."""

from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import Optional

import requests

from lib.labels import LANGUAGE_LABELS

SARVAM_TEXT_LID_URL = "https://api.sarvam.ai/text-lid"
SARVAM_TRANSLITERATE_URL = "https://api.sarvam.ai/transliterate"
SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate"

KANADA_RANGE = re.compile(r"[\u0C80-\u0CFF]")
TAMIL_RANGE = re.compile(r"[\u0B80-\u0BFF]")
LATIN_RANGE = re.compile(r"[A-Za-z]")

TARGET_LANGUAGE_CODES = {"kn": "kn-IN", "ta": "ta-IN", "en": "en-IN"}
TARGET_SCRIPT_FOR_LANGUAGE = {"kn-IN": "Kannada", "ta-IN": "Tamil", "en-IN": "Latin"}


def _api_key() -> str:
    return os.getenv("SARVAM_API_KEY", "")


def _headers() -> dict[str, str]:
    return {
        "api-subscription-key": _api_key(),
        "Content-Type": "application/json",
    }


def normalize_language_code(language_code: str | None) -> str | None:
    if not language_code:
        return None
    code = language_code.strip()
    if code in {"kn", "ta", "en"}:
        return TARGET_LANGUAGE_CODES.get(code)
    if code in TARGET_LANGUAGE_CODES.values():
        return code
    return None


def language_label(language_code: str | None) -> str:
    if not language_code:
        return "Unknown"
    return LANGUAGE_LABELS.get(language_code, LANGUAGE_LABELS.get(normalize_language_code(language_code) or "", language_code))


def _contains_kannada(text: str) -> bool:
    return bool(KANADA_RANGE.search(text))


def _contains_tamil(text: str) -> bool:
    return bool(TAMIL_RANGE.search(text))


def _contains_latin(text: str) -> bool:
    return bool(LATIN_RANGE.search(text))


@lru_cache(maxsize=2048)
def detect_language(text: str) -> dict[str, str] | None:
    if not text or not _api_key():
        return None
    try:
        response = requests.post(
            SARVAM_TEXT_LID_URL,
            headers=_headers(),
            json={"input": text[:1000]},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return {
            "language_code": data.get("language_code", ""),
            "script_code": data.get("script_code", ""),
        }
    except Exception:
        return None


@lru_cache(maxsize=4096)
def transliterate_text(text: str, source_language_code: str, target_language_code: str) -> str | None:
    if not text or not _api_key():
        return None
    try:
        response = requests.post(
            SARVAM_TRANSLITERATE_URL,
            headers=_headers(),
            json={
                "input": text[:1000],
                "source_language_code": source_language_code,
                "target_language_code": target_language_code,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("transliterated_text")
    except Exception:
        return None


@lru_cache(maxsize=4096)
def translate_text(text: str, source_language_code: str = "en-IN", target_language_code: str = "kn-IN") -> str | None:
    """Translate text with Sarvam and return None on any failure."""
    if not text or not _api_key():
        return None
    try:
        response = requests.post(
            SARVAM_TRANSLATE_URL,
            headers=_headers(),
            json={
                "input": text[:1000],
                "source_language_code": source_language_code,
                "target_language_code": target_language_code,
            },
            timeout=12,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("translated_text") or data.get("output_text")
    except Exception:
        return None


def bilingual_text(kannada_text: str, english_text: str) -> str:
    """Compose a Kannada-first label with English fallback in parentheses."""
    if not kannada_text:
        return english_text
    if not english_text:
        return kannada_text
    return f"{kannada_text} ({english_text})"


def normalize_complaint_text(text: str, complaint_language: str | None) -> str:
    """Return complaint text in its native script when Sarvam can help."""
    if not text:
        return text

    target_code = normalize_language_code(complaint_language)
    if target_code not in {"kn-IN", "ta-IN"}:
        return text

    # Keep native-script text as-is.
    if target_code == "kn-IN" and _contains_kannada(text):
        return text
    if target_code == "ta-IN" and _contains_tamil(text):
        return text

    detected = detect_language(text)
    source_code = (detected or {}).get("language_code", "en-IN")
    source_script = (detected or {}).get("script_code", "")

    # Sarvam transliteration works best for Latin/English or detected matching scripts.
    if source_code in {"en-IN", target_code} or source_script == "Latn" or _contains_latin(text):
        localized = transliterate_text(text, source_code if source_code != target_code else "en-IN", target_code)
        if localized:
            return localized

    return text


def enrich_complaint_record(record: dict) -> dict:
    enriched = dict(record)
    enriched["language_code"] = normalize_language_code(enriched.get("language")) or enriched.get("language")
    enriched["language_label"] = language_label(enriched.get("language_code"))
    enriched["description_native"] = normalize_complaint_text(
        str(enriched.get("description", "")),
        enriched.get("language_code"),
    )
    return enriched
