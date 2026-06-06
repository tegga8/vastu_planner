"""AI integration: Gemini for prompt parsing & layout, DeepAI for images, SVG fallback."""

import json
import os
import urllib.request
import urllib.parse
import re

try:
    from vastu_engine import VastuEngine
except ImportError:
    VastuEngine = None


class ImageRenderer:
    """Generates a concept house SVG image from floor plan data — no API key needed."""

    @staticmethod
    def generate_concept_svg(house_data):
        rooms = house_data.get("rooms", [])
        style = house_data.get("style", "Modern")
        facing = house_data.get("facing", "north")
        floors = int(house_data.get("floors", 1))
        site_length = float(house_data.get("site_length", 60))
        site_width = float(house_data.get("site_width", 40))

        total_area = sum(
            float(r.get("width", 0)) * float(r.get("height", 0))
            for r in rooms if isinstance(r, dict)
        )

        palettes = {
            "modern": {"wall": "#E8ECEF", "roof": "#7F8C8D", "trim": "#2C3E50",
                       "glass": "#85C1E9", "door": "#8B4513", "ground": "#A9DFBF",
                       "accent": "#E74C3C", "name": "Modern"},
            "traditional": {"wall": "#F5E6CC", "roof": "#C0392B", "trim": "#5D4037",
                            "glass": "#81C784", "door": "#6D4C41", "ground": "#C8E6C9",
                            "accent": "#FF8A65", "name": "Traditional"},
            "contemporary": {"wall": "#ECEFF1", "roof": "#546E7A", "trim": "#37474F",
                             "glass": "#4FC3F7", "door": "#5D4037", "ground": "#B2DFDB",
                             "accent": "#FF7043", "name": "Contemporary"},
            "minimalist": {"wall": "#FAFAFA", "roof": "#90A4AE", "trim": "#455A64",
                           "glass": "#B0BEC5", "door": "#795548", "ground": "#C8E6C9",
                           "accent": "#607D8B", "name": "Minimalist"}
        }
        pal = palettes.get(style.lower(), palettes["modern"])
        svg_w, svg_h = 800, 550

        lines = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" font-family="Arial, sans-serif">']
        lines.append(f'<defs><linearGradient id="sky" x1="0%" y1="0%" x2="0%" y2="100%"><stop offset="0%" stop-color="#85C1E9"/><stop offset="100%" stop-color="#D4E6F1"/></linearGradient></defs>')
        lines.append(f'<rect width="{svg_w}" height="{svg_h}" fill="#ECEFF1" rx="8"/>')
        lines.append(f'<rect width="{svg_w}" height="{svg_h * 0.65}" fill="url(#sky)" opacity="0.3"/>')
        lines.append(f'<rect x="0" y="{svg_h * 0.7}" width="{svg_w}" height="{svg_h * 0.3}" fill="{pal["ground"]}"/>')
        lines.append(f'<ellipse cx="{svg_w/2}" cy="{svg_h * 0.7}" rx="{svg_w/2 + 50}" ry="20" fill="{pal["ground"]}"/>')

        bw = 320
        bh = 200 + (floors - 1) * 70
        bx = (svg_w - bw) / 2
        by = svg_h * 0.7 - bh

        lines.append(f'<rect x="{bx + 8}" y="{by + 8}" width="{bw}" height="{bh}" fill="rgba(0,0,0,0.08)" rx="3"/>')
        lines.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="{pal["wall"]}" stroke="{pal["trim"]}" stroke-width="2" rx="2"/>')

        if style.lower() in ["traditional"]:
            roof_h = 55
            lines.append(f'<polygon points="{bx - 15},{by} {bx + bw/2},{by - roof_h} {bx + bw + 15},{by}" fill="{pal["roof"]}" stroke="{pal["trim"]}" stroke-width="2"/>')
        else:
            lines.append(f'<rect x="{bx - 8}" y="{by - 12}" width="{bw + 16}" height="14" fill="{pal["roof"]}" stroke="{pal["trim"]}" stroke-width="1.5" rx="3"/>')

        for f in range(floors):
            fy = by + bh - (f + 1) * (bh / floors)
            fh = bh / floors
            if f > 0:
                lines.append(f'<line x1="{bx + 10}" y1="{fy}" x2="{bx + bw - 10}" y2="{fy}" stroke="#BDC3C7" stroke-width="1" stroke-dasharray="4,2"/>')
            wins = 4 if f == floors - 1 else 3
            sp = bw / (wins + 1)
            for w in range(wins):
                wx = bx + sp * (w + 1) - 18
                wy = fy + fh * 0.15
                ww, wh = 36, fh * 0.5
                lines.append(f'<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" fill="{pal["glass"]}" stroke="{pal["trim"]}" stroke-width="1.5" rx="2" opacity="0.85"/>')
                lines.append(f'<line x1="{wx + ww/2}" y1="{wy}" x2="{wx + ww/2}" y2="{wy + wh}" stroke="{pal["trim"]}" stroke-width="0.8"/>')
                lines.append(f'<line x1="{wx}" y1="{wy + wh/2}" x2="{wx + ww}" y2="{wy + wh/2}" stroke="{pal["trim"]}" stroke-width="0.8"/>')

        dw, dh = 28, 50
        dx = bx + bw / 2 - dw / 2
        dy = svg_h * 0.7 - dh
        lines.append(f'<rect x="{dx}" y="{dy}" width="{dw}" height="{dh}" fill="{pal["door"]}" stroke="{pal["trim"]}" stroke-width="1.5" rx="2"/>')
        lines.append(f'<rect x="{dx + 3}" y="{dy + 3}" width="{dw/2 - 4}" height="{dh - 6}" fill="#A0522D" stroke="{pal["trim"]}" stroke-width="0.5" rx="1"/>')
        lines.append(f'<rect x="{dx + dw/2 + 1}" y="{dy + 3}" width="{dw/2 - 4}" height="{dh - 6}" fill="#A0522D" stroke="{pal["trim"]}" stroke-width="0.5" rx="1"/>')
        lines.append(f'<circle cx="{dx + dw * 0.7}" cy="{dy + dh/2}" r="3" fill="#FFD700" stroke="#B8860B" stroke-width="0.5"/>')
        steps_y = svg_h * 0.7
        for s in range(3):
            sw = dw + 12 + s * 4
            lines.append(f'<rect x="{dx - 6 - s * 2}" y="{steps_y}" width="{sw}" height="5" fill="#BDC3C7" stroke="{pal["trim"]}" stroke-width="0.5" rx="1"/>')
            steps_y += 5

        for tx, ty, tr, th in [(bx-50, svg_h*0.7, 25, 40), (bx+bw+30, svg_h*0.7, 30, 45)]:
            lines.append(f'<rect x="{tx-3}" y="{ty-th+5}" width="6" height="{th-5}" fill="#8D6E63" rx="2"/>')
            lines.append(f'<circle cx="{tx}" cy="{ty-th}" r="{tr}" fill="#4CAF50" opacity="0.8"/>')
            lines.append(f'<circle cx="{tx-8}" cy="{ty-th+5}" r="{tr*0.7}" fill="#66BB6A" opacity="0.7"/>')
            lines.append(f'<circle cx="{tx+8}" cy="{ty-th+5}" r="{tr*0.7}" fill="#43A047" opacity="0.7"/>')

        pw = 40
        lines.append(f'<rect x="{bx + bw/2 - pw/2}" y="{svg_h * 0.7}" width="{pw}" height="50" fill="#D7CCC8" stroke="#A1887F" stroke-width="1" rx="2" opacity="0.7"/>')

        rnames = [r.get("name", "") for r in rooms if isinstance(r, dict)]
        rl = ", ".join(rnames[:6])
        if len(rnames) > 6: rl += f" +{len(rnames) - 6} more"

        lines.append(f'<text x="{svg_w/2}" y="35" text-anchor="middle" font-size="20" font-weight="800" fill="#2C3E50">CONCEPT VIEW — {pal["name"].upper()} STYLE</text>')
        lines.append(f'<text x="{svg_w/2}" y="55" text-anchor="middle" font-size="12" fill="#7F8C8D">{floors} Floor(s) · {total_area:.0f} sqft · Facing {facing.upper()}</text>')
        lines.append(f'<text x="{svg_w/2}" y="75" text-anchor="middle" font-size="11" fill="#95A5A6">{rl}</text>')
        lines.append(f'<text x="{svg_w/2}" y="{svg_h - 10}" text-anchor="middle" font-size="9" fill="#BDC3C9">Generated by Vastu Planner AI · SVG Concept</text>')
        lines.append(f'</svg>')
        return "\n".join(lines)


class AIAdapter:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    DEEPAI_API_KEY = os.environ.get("DEEPAI_API_KEY", "")

    @classmethod
    def has_gemini(cls):
        return bool(cls.GEMINI_API_KEY)

    @classmethod
    def has_deepai(cls):
        return bool(cls.DEEPAI_API_KEY)

    @classmethod
    def parse_prompt_with_gemini(cls, user_prompt):
        """Use Gemini to parse a natural language prompt into structured data + floor plan."""
        if not cls.GEMINI_API_KEY:
            return None

        system_prompt = f"""You are a Vastu Shastra AI architect. Parse the user's home design request and generate a complete JSON floor plan.

VASTU ZONES (normalized 0-1 coordinates, origin top-left):
- northeast (0.66-1.0, 0.0-0.33): Pooja, Study, Meditation
- north (0.33-0.66, 0.0-0.33): Living Room, Study, Main Door  
- northwest (0.0-0.33, 0.0-0.33): Guest Room, Bathroom, Parking
- east (0.66-1.0, 0.33-0.66): Living Room, Study, Bathroom
- center (0.33-0.66, 0.33-0.66): Open Courtyard, Foyer
- west (0.0-0.33, 0.33-0.66): Dining Room, Store Room, Bedroom
- southeast (0.66-1.0, 0.66-1.0): Kitchen, Dining
- south (0.33-0.66, 0.66-1.0): Bedroom, Master Bedroom
- southwest (0.0-0.33, 0.66-1.0): Master Bedroom, Store Room

ROOM SIZES (min-ideal-max in feet):
- Master Bedroom: 14x12 - 16x14 - 22x18
- Bedroom: 12x10 - 14x12 - 18x14
- Kitchen: 10x8 - 12x10 - 16x12
- Living Room: 16x12 - 20x16 - 28x22
- Dining Room: 12x10 - 14x12 - 18x14
- Pooja Room: 6x5 - 8x6 - 12x10
- Study: 8x6 - 10x8 - 14x12
- Guest Room: 10x10 - 12x12 - 16x14
- Bathroom: 6x4 - 8x5 - 10x8
- Store Room: 6x4 - 8x6 - 12x10
- Parking: 16x10 - 18x12 - 22x14
- Garden: any remaining space

First, extract from the user's prompt:
{{
  "site_length": <in feet, default 60>,
  "site_width": <in feet, default 40>,
  "facing": "<north/east/south/west, default north>",
  "floors": <1-3, default 1>,
  "style": "<Modern/Traditional/Contemporary/Minimalist, default Modern>",
  "rooms": <list of room names>
}}

Then generate the floor plan with rooms placed in their correct Vastu zones.
Rooms MUST NOT overlap. Leave 3-4ft corridors. All coordinates in feet.
Main entrance on the facing side.

Return ONLY valid JSON with this structure:
{{
  "extracted": {{ ... }},
  "layout": {{
    "rooms": [
      {{"name": "...", "x": ..., "y": ..., "width": ..., "height": ..., "zone": "...",
        "doors": [{{"side": "bottom", "position": 0.5}}],
        "windows": [{{"side": "top", "position": 0.5}}]}}
    ],
    "front_door": {{"x": ..., "y": ..., "facing": "..."}},
    "stairs": {{"x": ..., "y": ..., "width": 12, "height": 6}} (if floors > 1)
  }}
}}

User prompt: {user_prompt}"""

        return cls._call_gemini_raw(system_prompt)

    @classmethod
    def _call_gemini_raw(cls, prompt):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={cls.GEMINI_API_KEY}"
        body = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 8192}
        }).encode()
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as resp:
                d = json.loads(resp.read())
            text = d.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            jstart = text.find("{")
            jend = text.rfind("}") + 1
            if jstart >= 0 and jend > jstart:
                return json.loads(text[jstart:jend])
        except Exception as e:
            print(f"Gemini error: {e}")
        return None

    @staticmethod
    def parse_prompt_keywords(user_prompt):
        """Fallback: extract requirements from prompt using keywords (no API key needed)."""
        p = user_prompt.lower()

        # Site dimensions
        dims = re.findall(r'(\d+)\s*[xX*]\s*(\d+)', p)
        site_length, site_width = 60, 40
        if dims:
            site_length, site_width = int(dims[0][0]), int(dims[0][1])

        # Facing
        facing = "north"
        for d in ["north", "south", "east", "west"]:
            if d in p:
                facing = d
                break

        # Style
        style = "Modern"
        for s, variants in [("Modern", ["modern", "contemporary"]),
                            ("Traditional", ["traditional", "classic", "indian"]),
                            ("Minimalist", ["minimalist", "minimal", "simple"])]:
            if any(v in p for v in variants):
                style = s
                break

        # Floors
        floors = 1
        floor_matches = re.findall(r'(\d+)\s*(floor|story|storey)', p)
        if floor_matches:
            floors = int(floor_matches[0][0])
        elif re.search(r'duplex|two.?floor|2.?floor|double.?floor', p):
            floors = 2
        elif re.search(r'three.?floor|3.?floor|triplex', p):
            floors = 3

        # Bedrooms
        bedrooms = 2
        brm = re.findall(r'(\d+)\s*(bhk|bed|bedroom|br)', p)
        if brm:
            bedrooms = int(brm[0][0])
        elif re.search(r'1.?bhk|one.?bed', p):
            bedrooms = 1
        elif re.search(r'3.?bhk|three.?bed', p):
            bedrooms = 3
        elif re.search(r'4.?bhk|four.?bed', p):
            bedrooms = 4

        # Room requirements
        rooms_list = []
        for i in range(bedrooms):
            rooms_list.append("Master Bedroom" if i == 0 else "Bedroom")

        room_keywords = [
            ("living", "Living Room"), ("kitchen", "Kitchen"), ("dining", "Dining Room"),
            ("pooja", "Pooja Room"), ("puja", "Pooja Room"), ("temple", "Pooja Room"),
            ("meditation", "Pooja Room"), ("study", "Study"), ("office", "Study"),
            ("guest", "Guest Room"), ("store", "Store Room"), ("storage", "Store Room"),
            ("parking", "Parking"), ("garage", "Parking"), ("garden", "Garden"),
            ("courtyard", "Garden"), ("lawn", "Garden")
        ]
        for kw, rname in room_keywords:
            if kw in p and rname not in rooms_list:
                rooms_list.append(rname)

        # Bathrooms
        bathrooms = 1
        bm = re.findall(r'(\d+)\s*(bath|washroom|toilet)', p)
        if bm:
            bathrooms = int(bm[0][0])
        elif re.search(r'2\s*bath|two\s*bath', p):
            bathrooms = 2

        for _ in range(bathrooms):
            rooms_list.append("Bathroom")

        if not rooms_list:
            rooms_list = ["Living Room", "Kitchen", "Master Bedroom", "Bathroom"]

        return {
            "site_length": site_length,
            "site_width": site_width,
            "facing": facing,
            "floors": floors,
            "style": style,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "rooms_list": rooms_list,
            "raw_prompt": user_prompt
        }

    @staticmethod
    def generate_house_image(house_data):
        """Generate house concept image. DeepAI (if configured) → SVG fallback."""
        if AIAdapter.has_deepai():
            try:
                prompt = _build_image_prompt(house_data)
                data = urllib.parse.urlencode({"text": prompt}).encode()
                req = urllib.request.Request(
                    "https://api.deepai.org/api/text2img",
                    data=data,
                    headers={"api-key": AIAdapter.DEEPAI_API_KEY}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read())
                url = result.get("output_url", "")
                if url:
                    return f'<img src="{url}" alt="AI Generated House" style="max-width:100%;max-height:500px;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,0.15);" />'
            except Exception as e:
                print(f"DeepAI error: {e}")
        svg = ImageRenderer.generate_concept_svg(house_data)
        return svg

    @staticmethod
    def ai_status():
        services = []
        if AIAdapter.has_gemini(): services.append("Gemini AI")
        if AIAdapter.has_deepai(): services.append("DeepAI")
        if not services: services.append("None configured")
        return {
            "gemini_available": AIAdapter.has_gemini(),
            "deepai_available": AIAdapter.has_deepai(),
            "configured_services": services,
            "note": "Set GEMINI_API_KEY for AI layout, DEEPAI_API_KEY for AI images. Works without both (algorithmic + SVG)."
        }


def _build_image_prompt(house_data):
    rooms = house_data.get("rooms", [])
    style = house_data.get("style", "Modern")
    facing = house_data.get("facing", "north")
    floors = int(house_data.get("floors", 1))
    rnames = [r.get("name", "") for r in rooms if isinstance(r, dict)]
    rl = ", ".join(rnames[:5])
    return f"A {style} residential house, {floors} floor(s), front view facing {facing}, {rl}, well-lit exterior, professional real estate photo quality"
