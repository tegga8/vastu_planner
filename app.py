"""Flask server — single prompt endpoint. User types one prompt, AI does the rest."""

import os, json
from flask import Flask, request, jsonify, render_template
from vastu_engine import VastuEngine
from layout_generator import LayoutGenerator
from floorplan_renderer import FloorplanRenderer
from ai_adapter import AIAdapter, ImageRenderer

app = Flask(__name__)
engine = VastuEngine()
layout_gen = LayoutGenerator()
renderer = FloorplanRenderer()


def build_plan(user_data):
    """Generate complete plan from structured user data."""
    rooms_list = user_data.get("rooms_list", [])
    if not rooms_list:
        rooms_list = engine.build_rooms_list(user_data)

    facing = user_data.get("facing", "north")
    site_length = float(user_data.get("site_length", 60))
    site_width = float(user_data.get("site_width", 40))

    # Generate layout
    layout = layout_gen.generate(user_data, rooms_list)
    layout["user_name"] = "User"
    layout["site_length"] = site_length
    layout["site_width"] = site_width

    rooms = layout.get("rooms", [])

    # Scores
    scores = []
    for r in rooms:
        rname = r["name"]
        zone = r.get("zone", "center")
        sc = r.get("score", engine.get_room_zone_score(rname, zone))
        rule = engine.ROOM_RULES.get(rname, {})
        scores.append({
            "room": rname, "zone": zone,
            "zone_label": engine.ZONES.get(zone, {}).get("label", zone),
            "element": engine.ZONES.get(zone, {}).get("element", ""),
            "score": sc,
            "reason": f"Best in {rule.get('primary_zone', 'N/A')}" if sc >= 8 else
                      f"Alternative in {zone}" if sc >= 5 else f"Should avoid {zone}"
        })

    raw_avg = sum(s["score"] for s in scores) / max(len(scores), 1)
    low_penalty = sum(1 for s in scores if s["score"] < 5) * 0.5
    overall = max(1, raw_avg - low_penalty)

    # Render SVG
    svg = renderer.render(layout)
    elevation_svg = renderer.render_elevation(layout)

    # House concept image
    house_image_html = ""
    try:
        house_image_html = AIAdapter.generate_house_image({
            "rooms": rooms, "style": user_data.get("style", "Modern"),
            "facing": facing, "floors": int(user_data.get("floors", 1)),
            "site_length": site_length, "site_width": site_width
        })
    except Exception as e:
        print(f"Image error: {e}")

    # Suggestions
    suggestions = []
    for s in scores:
        if s["score"] < 6:
            suggestions.append({
                "room": s["room"], "current_zone": s["zone"],
                "score": s["score"],
                "suggestion": f"{s['room']} is in {s['zone']} (score: {s['score']}/10). {s['reason']}."
            })
    if not suggestions:
        suggestions.append({
            "room": "All Rooms", "current_zone": "", "score": 10,
            "suggestion": "All rooms are well-placed per Vastu principles! 🎉"
        })

    return {
        "layout": layout,
        "room_scores": scores,
        "overall_score": round(overall, 1),
        "rating": "Excellent" if overall >= 8 else "Good" if overall >= 6 else "Average",
        "rooms_list": rooms_list,
        "svg": svg,
        "elevation_svg": elevation_svg,
        "house_image_html": house_image_html,
        "suggestions": suggestions,
        "user_data": user_data
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Main endpoint: accepts either raw_prompt or structured user_data, returns full plan."""
    data = request.get_json() or {}
    raw_prompt = data.get("prompt", "").strip()

    if raw_prompt:
        # Try Gemini parsing first
        gemini_result = AIAdapter.parse_prompt_with_gemini(raw_prompt)
        if gemini_result and "extracted" in gemini_result and "layout" in gemini_result:
            user_data = gemini_result["extracted"]
            # Use Gemini's layout directly
            layout = gemini_result["layout"]
            # Continue with the plan using Gemini's layout
            result = _build_from_gemini_layout(layout, user_data)
            if result:
                result["source"] = "gemini-ai"
                return jsonify(result)

        # Fallback: keyword extraction
        user_data = AIAdapter.parse_prompt_keywords(raw_prompt)
        user_data["source"] = "keyword-extraction"
    else:
        # Direct structured data
        user_data = data
        user_data["rooms_list"] = data.get("rooms_list", [])
        user_data["source"] = "structured"

    result = build_plan(user_data)
    result["source"] = user_data.get("source", "algorithmic")
    result["parsed_from_prompt"] = raw_prompt if raw_prompt else ""
    return jsonify(result)


def _build_from_gemini_layout(layout_data, extracted):
    """Build complete plan from Gemini's layout output."""
    try:
        rooms = layout_data.get("rooms", [])
        site_length = float(extracted.get("site_length", 60))
        site_width = float(extracted.get("site_width", 40))
        facing = extracted.get("facing", "north")
        floors = int(extracted.get("floors", 1))
        style = extracted.get("style", "Modern")

        # Assign zones and scores
        for r in rooms:
            cx = (r["x"] + r["width"] / 2) / site_length
            cy = (r["y"] + r["height"] / 2) / site_width
            zone = VastuEngine.get_zone_for_point(cx, cy)
            r["zone"] = zone
            r["score"] = VastuEngine.get_room_zone_score(r["name"], zone)
            r["area_sqft"] = round(r["width"] * r["height"], 1)
            if "doors" not in r:
                r["doors"] = [{"side": "bottom", "position": 0.5}]
            if "windows" not in r:
                r["windows"] = [{"side": "top", "position": 0.5}]

        # Build walls
        from layout_generator import LayoutGenerator as LG
        walls = LG._build_walls(rooms, site_length, site_width)

        front_door = layout_data.get("front_door", {"x": site_length * 0.45, "y": 0, "facing": facing})
        stairs = layout_data.get("stairs")

        layout = {
            "rooms": rooms, "walls": walls, "front_door": front_door,
            "stairs": stairs, "corridors": [], "facing": facing,
            "site_length": site_length, "site_width": site_width,
            "floors": floors, "style": style, "source": "ai",
            "user_name": "User"
        }

        user_data = extracted
        user_data["rooms_list"] = [r["name"] for r in rooms]
        user_data["facing"] = facing
        user_data["site_length"] = site_length
        user_data["site_width"] = site_width
        user_data["floors"] = floors
        user_data["style"] = style

        # Use build_plan for rendering
        result = build_plan(user_data)
        result["layout"] = layout
        # Recalculate from the Gemini layout
        scores = []
        for r in rooms:
            zone = r.get("zone", "center")
            sc = r.get("score", 5)
            scores.append({
                "room": r["name"], "zone": zone,
                "zone_label": VastuEngine.ZONES.get(zone, {}).get("label", zone),
                "element": VastuEngine.ZONES.get(zone, {}).get("element", ""),
                "score": sc,
                "reason": f"Placed by AI in {zone}"
            })
        raw_avg = sum(s["score"] for s in scores) / max(len(scores), 1)
        low_penalty = sum(1 for s in scores if s["score"] < 5) * 0.5
        overall = max(1, raw_avg - low_penalty)

        svg = renderer.render(layout)
        elevation_svg = renderer.render_elevation(layout)

        house_image_html = ""
        try:
            house_image_html = AIAdapter.generate_house_image({
                "rooms": rooms, "style": style, "facing": facing,
                "floors": floors, "site_length": site_length, "site_width": site_width
            })
        except Exception:
            pass

        return {
            "layout": layout, "room_scores": scores,
            "overall_score": round(overall, 1),
            "rating": "Excellent" if overall >= 8 else "Good" if overall >= 6 else "Average",
            "rooms_list": [r["name"] for r in rooms],
            "svg": svg, "elevation_svg": elevation_svg,
            "house_image_html": house_image_html,
            "suggestions": [],
            "source": "gemini-ai"
        }
    except Exception as e:
        print(f"Gemini layout processing error: {e}")
        return None


@app.route("/api/vastu/zones", methods=["GET"])
def get_zones():
    return jsonify(VastuEngine.ZONES)


@app.route("/api/vastu/rooms", methods=["GET"])
def get_rooms():
    data = []
    for name, info in VastuEngine.ROOM_RULES.items():
        data.append({
            "name": name, "primary_zone": info["primary_zone"],
            "alt_zones": info.get("alt_zones", []),
            "avoid_zones": info.get("avoid_zones", []),
            "ideal_size": f"{info['standard_sizes']['ideal'][0]}' x {info['standard_sizes']['ideal'][1]}'"
        })
    return jsonify(data)


@app.route("/api/ai/status", methods=["GET"])
def ai_status():
    return jsonify(AIAdapter.ai_status())


if __name__ == "__main__":
    print("=" * 50)
    print("  VASTU PLANNER AI")
    print("=" * 50)
    s = AIAdapter.ai_status()
    for svc in s["configured_services"]:
        print(f"  {'✓' if svc != 'None configured' else '○'} {svc}")
    print(f"  Image: {'DeepAI' if AIAdapter.has_deepai() else 'SVG Concept (default)'}")
    print(f"  Server: http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=True)
