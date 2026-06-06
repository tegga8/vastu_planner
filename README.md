# Vastu Planner

AI-powered Vastu-compliant house plan generator. Type a natural language description of your dream home and get a complete floor plan, elevation, and concept image — all aligned with Vastu Shastra principles.

## How It Works

You type one sentence:

> *"I want a modern 3BHK house on a 60×45 plot facing north with a big kitchen, pooja room, study, garden, and parking"*

The system parses it, generates room layout respecting Vastu zones, and renders:

- **Floor plan** (CAD-style SVG with dimensions, scale, north arrow)
- **Elevation** (front-view SVG)
- **Concept image** (SVG house render)
- **Vastu analysis** (per-room scores with reasoning)

## Quick Start

```powershell
pip install flask
cd vastu_planner
python app.py
```

Open **http://localhost:5000** in your browser. Type your prompt and hit generate.

## API Keys (Optional)

Set these environment variables to unlock AI features:

| Key | Effect |
|-----|--------|
| `GEMINI_API_KEY` | AI parsing of prompts + AI room layout generation |
| `DEEPAI_API_KEY` | Photorealistic AI house concept images |

```powershell
$env:GEMINI_API_KEY = "your_key_here"
$env:DEEPAI_API_KEY = "your_key_here"
python app.py
```

Without any keys, the system uses keyword extraction + algorithmic layout + built-in SVG concept images — fully functional.

## Vastu Engine

The 9-zone Vastu mandala is oriented correctly:

```
┌──────────┬──────────┬──────────┐
│   NW     │   N      │   NE     │
│ Bathroom │ Parking  │ Pooja    │
├──────────┼──────────┼──────────┤
│   W      │   C      │   E      │
│ Bedroom  │ Living   │ Study    │
├──────────┼──────────┼──────────┤
│   SW     │   S      │   SE     │
│ Master   │ Bedroom  │ Kitchen  │
└──────────┴──────────┴──────────┘
```

Each room is scored on placement (zone), orientation, and size.

## File Structure

```
vastu_planner/
├── app.py                 # Flask server + routes
├── ai_adapter.py          # Gemini prompt parsing + image gen + keyword fallback
├── layout_generator.py    # Algorithmic room layout (zone packing)
├── vastu_engine.py        # Vastu zone definitions, room rules, scoring
├── floorplan_renderer.py  # SVG floor plan + elevation renderer
├── templates/index.html   # Single-page frontend
└── static/
    ├── css/style.css
    └── js/app.js
```

## API

### `POST /api/generate`

**Body:** `{ "prompt": "your house description" }`

**Response:**
```json
{
  "svg": "<floor plan SVG>",
  "elevation_svg": "<elevation SVG>",
  "house_image_html": "<concept image HTML>",
  "layout": { "rooms": [...], "walls": [...] },
  "overall_score": 7.3,
  "rating": "Good",
  "rooms_list": ["Master Bedroom", ...],
  "room_scores": [{ "room": "...", "score": 8, ... }],
  "suggestions": [{ "room": "...", "suggestion": "..." }]
}
```

## Requirements

- Python 3.8+
- Flask
- json (stdlib)
- re (stdlib)

Gemini integration uses `google-generativeai` if `GEMINI_API_KEY` is set.
