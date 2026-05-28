# Karnataka Urban Analytics Dashboard

Official-facing analytics dashboard for the Karnataka Civic Complaint platform.
Built in Streamlit for the Municipal Commissioner and Zonal Officers.

## What it does

- **Overview** - headline metrics: total complaints, resolution rate, SLA breaches, escalations.
- **Analytics** - bar charts by category and zone, 30-day trend lines per category.
- **Hotspot Map** - folium map with markers sized by complaint count. Click a marker for the recommendation.
- **Preventive Planning** - ranked list of chronic problem locations with AI-generated action recommendations.
- **Complaints** - filterable table of all complaint records.
- **Language-aware tracking** - Kannada and Tamil complaints stay in native script, with Sarvam transliteration for romanized text.

A **zone filter** in the sidebar narrows every tab to a single municipal zone simultaneously.

---

## Quick start

### 1. Install Python dependencies

```bash
cd dashboard
pip install -r requirements.txt
```

Requires Python 3.10 or later.

### 2. Configure environment

```bash
cp .env.example .env
```

Leave `USE_MOCK_DATA=true` for development. The app uses realistic seeded fake
data and does not require Member A's backend to be running.

If you want the Planning tab's AI summary, set `SARVAM_API_KEY` in `.env`
and leave `SARVAM_MODEL=sarvam-30b` unless you want a different Sarvam model.

### 3. Run the dashboard

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501` by default.

---

## Project layout

```
dashboard/
  app.py                # main Streamlit app (tabs, charts, map)
  lib/
    api.py              # calls Member A's API or falls back to mock_data
    mock_data.py        # seeded fake data in the exact Section 3 shapes
    labels.py           # human-readable labels and colors for all keys
    transform.py        # pandas helpers: API JSON to chart-ready DataFrames
  requirements.txt
  .env.example          # template - copy to .env, never commit .env
  .gitignore
  README.md
```

---

## Switching to the real API

When Member A's backend is running locally:

```
# .env
USE_MOCK_DATA=false
API_BASE_URL=http://localhost:8000
```

Then restart the app. Every chart and panel reads from Member A's live seeded data.

The mock data module stays available as a fallback for demos when the backend is offline.

---

## Integration checklist (Section 10)

- Reads only from `/analytics/summary`, `/analytics/trends`, `/analytics/hotspots`, `GET /complaints`. Never writes.
- Category and sub-category keys rendered with human labels from `labels.py`, matching Section 5 exactly.
- Zone filter narrows every tab simultaneously.
- Hotspot map and preventive planning panel both show the `recommendation` text from the API.
- No API keys. Free OpenStreetMap tiles via folium.
- Sarvam powers the AI planning narrative when `SARVAM_API_KEY` is set.
- Complaint tracking preserves Kannada/Tamil script and adds a language filter in the tracker and complaints table.
- `.env` is git-ignored. `.env.example` has blank values.
