"""Professional CAD-style floor plan SVG renderer with real walls and dimensions."""

from vastu_engine import VastuEngine


class FloorplanRenderer:
    """Renders room layout data into a professional SVG floor plan."""

    @classmethod
    def render(cls, layout_data):
        """Main entry point: render full floor plan SVG."""
        rooms = layout_data.get("rooms", [])
        walls = layout_data.get("walls", [])
        site_length = layout_data.get("site_length", 60)
        site_width = layout_data.get("site_width", 40)
        facing = layout_data.get("facing", "north")
        front_door = layout_data.get("front_door", {})

        # SVG dimensions
        margin = 70
        title_h = 55
        bottom_h = 120
        drawing_w = 750
        drawing_h = 580
        avail_w = drawing_w - 2 * margin
        avail_h = drawing_h - 2 * margin - title_h - bottom_h

        scale = min(avail_w / site_length, avail_h / site_width)
        ox = margin
        oy = margin + title_h

        lines = []
        lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 720" width="100%" height="100%" font-family="Arial, Helvetica, sans-serif">')
        lines.append(f'<defs>{cls._defs()}</defs>')

        # Background
        lines.append(f'<rect x="0" y="0" width="1100" height="720" fill="#F0F2F5" rx="4"/>')

        # Title block
        lines.append(f'<rect x="20" y="10" width="1060" height="{title_h - 10}" fill="#2D3436" rx="4"/>')
        name = layout_data.get("user_name", "Client")
        style = layout_data.get("style", "Modern")
        floors = layout_data.get("floors", 1)
        source = layout_data.get("source", "ai")
        source_label = "AI-Generated" if source == "ai" else "Vastu Algorithmic"
        lines.append(f'<text x="36" y="36" font-size="17" font-weight="800" fill="#fff">VASTU ARCHITECTURAL FLOOR PLAN</text>')
        lines.append(f'<text x="36" y="52" font-size="11" fill="#B2BEC3">Client: {name} | Plot: {site_length}\' × {site_width}\' | Facing: {facing.upper()} | Style: {style} | {floors} Floor(s) | {source_label}</text>')

        # Status badge
        score = sum(r.get("score", 5) for r in rooms) / max(len(rooms), 1)
        rating = "EXCELLENT" if score >= 8 else "GOOD" if score >= 6 else "AVERAGE"
        color = "#00B894" if score >= 8 else "#FDCB6E" if score >= 6 else "#E17055"
        lines.append(f'<rect x="940" y="16" width="125" height="34" rx="4" fill="{color}"/>')
        lines.append(f'<text x="1002" y="37" text-anchor="middle" font-size="13" font-weight="800" fill="#fff">VASTU {rating}</text>')

        # === MAIN FLOOR PLAN ===
        lines.append(f'<g transform="translate({ox}, {oy})">')

        # Site boundary
        sw = site_length * scale
        sh = site_width * scale
        lines.append(f'<rect x="0" y="0" width="{sw}" height="{sh}" fill="#fff" stroke="#333" stroke-width="2"/>')

        # Zone color overlays
        for zname, zdata in VastuEngine.ZONES.items():
            xr = zdata["x_range"]
            yr = zdata["y_range"]
            zx = xr[0] * sw
            zy = yr[0] * sh
            zw = (xr[1] - xr[0]) * sw
            zh = (yr[1] - yr[0]) * sh
            lines.append(f'<rect x="{zx}" y="{zy}" width="{zw}" height="{zh}" fill="{zdata["color"]}" opacity="0.35" stroke="{zdata["border"]}" stroke-width="0.8" stroke-dasharray="4,3"/>')

        # Room fills (solid color)
        for r in rooms:
            rx = r["x"] * scale
            ry = r["y"] * scale
            rw = r["width"] * scale
            rh = r["height"] * scale
            zname = r.get("zone", "center")
            zdata = VastuEngine.ZONES.get(zname, {})
            fill = zdata.get("color", "#fff") + "99"
            lines.append(f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" fill="{fill}" stroke="none" rx="1"/>')

        # Walls
        for w in walls:
            x1 = w["x1"] * scale
            y1 = w["y1"] * scale
            x2 = w["x2"] * scale
            y2 = w["y2"] * scale
            wtype = w.get("type", "internal")
            sw_val = 5 if wtype == "external" else 3
            color = "#2D3436" if wtype == "external" else "#636E72"

            # Draw double line for external walls
            if wtype == "external":
                thick = 0.45 * scale  # 9 inches in scale
                lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw_val}" stroke-linecap="round"/>')
                # Second line offset
                if w["x1"] == w["x2"]:  # vertical
                    lines.append(f'<line x1="{x1 + thick}" y1="{y1}" x2="{x2 + thick}" y2="{y2}" stroke="{color}" stroke-width="{sw_val}" stroke-linecap="round"/>')
                else:  # horizontal
                    lines.append(f'<line x1="{x1}" y1="{y1 + thick}" x2="{x2}" y2="{y2 + thick}" stroke="{color}" stroke-width="{sw_val}" stroke-linecap="round"/>')
            else:
                lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw_val}" stroke-linecap="round"/>')

        # Room labels
        for r in rooms:
            rx = r["x"] * scale
            ry = r["y"] * scale
            rw = r["width"] * scale
            rh = r["height"] * scale
            cx = rx + rw / 2
            cy = ry + rh / 2
            score_val = r.get("score", 5)

            if rw > 30 and rh > 20:
                lines.append(f'<text x="{cx}" y="{cy - 5}" text-anchor="middle" font-size="11" font-weight="700" fill="#2D3436">{r["name"]}</text>')
                lines.append(f'<text x="{cx}" y="{cy + 10}" text-anchor="middle" font-size="9" fill="#636E72">{r["width"]:.0f}\' × {r["height"]:.0f}\' = {r.get("area_sqft", r["width"] * r["height"]):.0f} sqft</text>')
                # Score badge
                sc_color = "#00B894" if score_val >= 8 else "#FDCB6E" if score_val >= 5 else "#E17055"
                lines.append(f'<rect x="{cx + 20}" y="{cy - 12}" width="22" height="14" rx="3" fill="{sc_color}" opacity="0.9"/>')
                lines.append(f'<text x="{cx + 31}" y="{cy - 2}" text-anchor="middle" font-size="8" font-weight="700" fill="#fff">{score_val}</text>')
            elif rw > 20 and rh > 14:
                lines.append(f'<text x="{cx}" y="{cy + 3}" text-anchor="middle" font-size="9" font-weight="600" fill="#2D3436">{r["name"]}</text>')
            else:
                lines.append(f'<text x="{cx}" y="{cy + 3}" text-anchor="middle" font-size="7" fill="#2D3436">{r["name"]}</text>')

        # Front door indicator
        fd = front_door
        fd_facing = fd.get("facing", facing)
        door_size = 4 * scale
        if fd_facing == "north":
            fdx = fd.get("x", site_length / 2) * scale
            fdy = 0
            lines.append(f'<rect x="{fdx - door_size}" y="{fdy - 2}" width="{door_size * 2}" height="4" fill="#e63946" rx="1"/>')
            lines.append(f'<text x="{fdx}" y="{fdy - 8}" text-anchor="middle" font-size="8" font-weight="700" fill="#e63946">MAIN DOOR →</text>')
            lines.append(f'<path d="M {fdx},{fdy} Q {fdx + door_size * 2},{fdy + door_size * 2} {fdx},{fdy + door_size * 2}" fill="none" stroke="#e63946" stroke-width="1.5"/>')
        elif fd_facing == "south":
            fdx = fd.get("x", site_length / 2) * scale
            fdy = sh
            lines.append(f'<rect x="{fdx - door_size}" y="{fdy - 2}" width="{door_size * 2}" height="4" fill="#e63946" rx="1"/>')
            lines.append(f'<text x="{fdx}" y="{fdy + 16}" text-anchor="middle" font-size="8" font-weight="700" fill="#e63946">← MAIN DOOR</text>')

        # Dimension lines
        dim_y = -25
        lines.append(f'<line x1="0" y1="{dim_y}" x2="{sw}" y2="{dim_y}" stroke="#e63946" stroke-width="0.8"/>')
        lines.append(f'<line x1="0" y1="{dim_y - 5}" x2="0" y2="{dim_y + 5}" stroke="#e63946" stroke-width="0.8"/>')
        lines.append(f'<line x1="{sw}" y1="{dim_y - 5}" x2="{sw}" y2="{dim_y + 5}" stroke="#e63946" stroke-width="0.8"/>')
        lines.append(f'<text x="{sw / 2}" y="{dim_y - 6}" text-anchor="middle" font-size="10" font-weight="700" fill="#e63946">{site_length}\' - 0"</text>')

        dim_x = -30
        lines.append(f'<line x1="{dim_x}" y1="0" x2="{dim_x}" y2="{sh}" stroke="#e63946" stroke-width="0.8"/>')
        lines.append(f'<line x1="{dim_x - 5}" y1="0" x2="{dim_x + 5}" y2="0" stroke="#e63946" stroke-width="0.8"/>')
        lines.append(f'<line x1="{dim_x - 5}" y1="{sh}" x2="{dim_x + 5}" y2="{sh}" stroke="#e63946" stroke-width="0.8"/>')
        lines.append(f'<text x="{dim_x - 8}" y="{sh / 2}" text-anchor="middle" font-size="10" font-weight="700" fill="#e63946" transform="rotate(-90, {dim_x - 8}, {sh / 2})">{site_width}\' - 0"</text>')

        # North arrow
        lines.append(cls._north_arrow(sw + 30, 40, facing))

        # Scale bar
        lines.append(cls._scale_bar(10, sh + 20, scale))

        # Legend compact
        lx = sw + 20
        ly = 100
        lines.append(f'<rect x="{lx}" y="{ly}" width="185" height="200" fill="#fff" stroke="#ddd" stroke-width="1" rx="6" filter="url(#shadow)"/>')
        lines.append(f'<text x="{lx + 92}" y="{ly + 20}" text-anchor="middle" font-size="12" font-weight="700" fill="#2D3436">ZONE LEGEND</text>')
        zy = ly + 32
        for zname, zdata in VastuEngine.ZONES.items():
            lines.append(f'<rect x="{lx + 10}" y="{zy - 8}" width="12" height="12" fill="{zdata["color"]}" stroke="{zdata["border"]}" stroke-width="0.8" rx="2"/>')
            lines.append(f'<text x="{lx + 28}" y="{zy + 2}" font-size="9" fill="#444">{zdata["label"]}</text>')
            zy += 17

        lines.append(f'</g>')

        # === ROOM SCHEDULE TABLE (bottom) ===
        tx = 20
        ty = 620
        lines.append(f'<rect x="{tx}" y="{ty}" width="1060" height="85" fill="#fff" stroke="#ddd" rx="4"/>')
        lines.append(f'<text x="{tx + 12}" y="{ty + 18}" font-size="11" font-weight="700" fill="#2D3436">ROOM SCHEDULE</text>')
        lines.append(f'<line x1="{tx + 12}" y1="{ty + 24}" x2="{tx + 1048}" y2="{ty + 24}" stroke="#ddd" stroke-width="1"/>')

        headers = ["Room", "Width", "Length", "Area", "Zone", "Vastu Score", "Element", "Position"]
        hw_list = [120, 55, 55, 65, 90, 75, 80, "auto"]
        hx = tx + 12
        for i, h in enumerate(headers):
            w = 90 if hw_list[i] == "auto" else hw_list[i]
            lines.append(f'<text x="{hx}" y="{ty + 40}" font-size="9" font-weight="700" fill="#666">{h}</text>')
            hx += w

        hx = tx + 12
        row_y = ty + 54
        for i, r in enumerate(rooms[:7]):
            if row_y > ty + 75:
                break
            zname = r.get("zone", "center")
            zdata = VastuEngine.ZONES.get(zname, {})
            score_val = r.get("score", 5)
            vals = [
                r["name"], f"{r['width']:.0f}'", f"{r['height']:.0f}'",
                f"{r.get('area_sqft', r['width']*r['height']):.0f} ft²",
                zdata.get("label", zname)[:15],
                f"{score_val}/10",
                zdata.get("element", ""),
                zname.upper()
            ]
            hpos = tx + 12
            for j, v in enumerate(vals):
                w = 90 if hw_list[j] == "auto" else hw_list[j]
                clr = "#e63946" if j == 5 and score_val < 5 else "#444"
                lines.append(f'<text x="{hpos}" y="{row_y}" font-size="8.5" fill="{clr}">{v}</text>')
                hpos += w
            row_y += 16

        # Footer
        lines.append(f'<text x="540" y="712" text-anchor="middle" font-size="8" fill="#999">Vastu Planner AI v2.0 | Generated by AI Architecture Engine | All dimensions in feet | Scale: 1" = {1/scale:.1f}\'</text>')
        lines.append(f'</svg>')
        return "\n".join(lines)

    @staticmethod
    def _defs():
        return '''
        <filter id="shadow"><feDropShadow dx="1" dy="1" stdDeviation="1.5" flood-opacity="0.12"/></filter>
        <marker id="dot" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="4" markerHeight="4"><circle cx="5" cy="5" r="3" fill="#e63946"/></marker>
        '''

    @staticmethod
    def _north_arrow(x, y, facing):
        return f'''
        <g transform="translate({x}, {y})">
            <circle cx="0" cy="0" r="16" fill="#fff" stroke="#333" stroke-width="1.2"/>
            <polygon points="0,-12 -4,5 0,1 4,5" fill="#e63946"/>
            <polygon points="0,12 -4,-5 0,-1 4,-5" fill="#2D3436"/>
            <text x="0" y="-20" text-anchor="middle" font-size="11" font-weight="800" fill="#e63946">N</text>
            <text x="0" y="3" text-anchor="middle" font-size="7" font-weight="700" fill="#fff">N</text>
        </g>'''

    @staticmethod
    def _scale_bar(x, y, scale):
        length_10 = 10 * scale
        return f'''
        <g transform="translate({x}, {y})">
            <text x="0" y="-4" font-size="8" fill="#666">Scale: 10\'</text>
            <line x1="0" y1="4" x2="{length_10}" y2="4" stroke="#333" stroke-width="2"/>
            <line x1="0" y1="0" x2="0" y2="8" stroke="#333" stroke-width="1.5"/>
            <line x1="{length_10}" y1="0" x2="{length_10}" y2="8" stroke="#333" stroke-width="1.5"/>
            <line x1="{length_10 / 2}" y1="0" x2="{length_10 / 2}" y2="8" stroke="#333" stroke-width="1.5"/>
            <rect x="0" y="4" width="{length_10 / 2}" height="4" fill="#333"/>
            <text x="{length_10 / 4}" y="18" text-anchor="middle" font-size="7" fill="#666">5\'</text>
            <text x="{length_10 * 3 / 4}" y="18" text-anchor="middle" font-size="7" fill="#666">10\'</text>
        </g>'''

    @classmethod
    def render_elevation(cls, layout_data):
        """Generate a simple front elevation SVG."""
        floors = layout_data.get("floors", 1)
        site_length = layout_data.get("site_length", 60)
        facing = layout_data.get("facing", "north")
        style = layout_data.get("style", "Modern")
        rooms = layout_data.get("rooms", [])

        lines = []
        lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 520" width="100%" height="100%" font-family="Arial, sans-serif">')
        lines.append(f'<rect x="0" y="0" width="700" height="520" fill="#f8f9fa" rx="4"/>')
        lines.append(f'<text x="350" y="28" text-anchor="middle" font-size="16" font-weight="800" fill="#2D3436">FRONT ELEVATION — {facing.upper()} FACING — {style.upper()} STYLE</text>')

        # Building
        bw = 480
        bh_per_floor = 90
        total_h = bh_per_floor * floors + 25
        bx = 100
        by = 450 - total_h

        # Ground
        lines.append(f'<line x1="{bx - 20}" y1="450" x2="{bx + bw + 20}" y2="450" stroke="#2D3436" stroke-width="3"/>')
        lines.append(f'<rect x="{bx - 10}" y="450" width="{bw + 20}" height="15" fill="#95a5a6" rx="2"/>')
        lines.append(f'<text x="{bx + bw / 2}" y="480" text-anchor="middle" font-size="9" fill="#888">Ground Level</text>')

        # Building mass
        lines.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{total_h}" fill="#e8e8e8" stroke="#333" stroke-width="2" rx="1"/>')

        # Roof
        lines.append(f'<rect x="{bx - 8}" y="{by - 14}" width="{bw + 16}" height="15" fill="#7f8c8d" stroke="#333" stroke-width="1.5" rx="2"/>')
        if style.lower() in ["traditional", "contemporary"]:
            lines.append(f'<polygon points="{bx - 15},{by - 14} {bx + bw/2},{by - 45} {bx + bw + 15},{by - 14}" fill="#c0392b" stroke="#333" stroke-width="1.5"/>')

        # Floors
        for f in range(floors):
            fy = by + total_h - (f + 1) * bh_per_floor
            lines.append(f'<rect x="{bx + 15}" y="{fy + 12}" width="{bw - 30}" height="{bh_per_floor - 24}" fill="#fff" stroke="#ccc" stroke-width="1" rx="1"/>')

            if floors > 1:
                lines.append(f'<text x="{bx + bw / 2}" y="{fy + bh_per_floor / 2 + 4}" text-anchor="middle" font-size="12" font-weight="700" fill="#636E72">Floor {floors - f}</text>')

            # Windows
            wins = 4 if f == 0 else 3
            win_sp = (bw - 50) / (wins + 1)
            for w in range(wins):
                wx = bx + 25 + win_sp * (w + 1) - 18
                wy = fy + 22
                ww = 36
                wh = 44
                lines.append(f'<rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" fill="#74b9ff" stroke="#2980b9" stroke-width="1.5" rx="2" opacity="0.8"/>')
                lines.append(f'<line x1="{wx + ww / 2}" y1="{wy}" x2="{wx + ww / 2}" y2="{wy + wh}" stroke="#2980b9" stroke-width="0.8"/>')
                lines.append(f'<line x1="{wx}" y1="{wy + wh / 2}" x2="{wx + ww}" y2="{wy + wh / 2}" stroke="#2980b9" stroke-width="0.8"/>')
                lines.append(f'<rect x="{wx + 2}" y="{wy + 2}" width="{ww / 2 - 2}" height="{wh / 2 - 2}" fill="#fff" opacity="0.2"/>')

            # Floor separator line
            if f < floors - 1:
                lines.append(f'<line x1="{bx}" y1="{fy + bh_per_floor}" x2="{bx + bw}" y2="{fy + bh_per_floor}" stroke="#95a5a6" stroke-width="1.5" stroke-dasharray="6,3"/>')

        # Main door on ground floor
        door_w = 28
        door_h = 50
        dx = bx + bw / 2 - door_w / 2
        dy = 450 - door_h
        lines.append(f'<rect x="{dx}" y="{dy}" width="{door_w}" height="{door_h}" fill="#8B4513" stroke="#5D3A1A" stroke-width="1.5" rx="2"/>')
        lines.append(f'<rect x="{dx + 2}" y="{dy + 2}" width="{door_w / 2 - 2}" height="{door_h - 4}" fill="#A0522D"/>')
        lines.append(f'<rect x="{dx + door_w / 2}" y="{dy + 2}" width="{door_w / 2 - 2}" height="{door_h - 4}" fill="#A0522D"/>')
        lines.append(f'<circle cx="{dx + door_w * 0.65}" cy="{dy + door_h / 2}" r="2" fill="#FFD700"/>')

        # Height dimension
        hx = bx - 25
        lines.append(f'<line x1="{hx}" y1="{by}" x2="{hx}" y2="450" stroke="#e63946" stroke-width="0.8"/>')
        lines.append(f'<line x1="{hx - 5}" y1="{by}" x2="{hx + 5}" y2="{by}" stroke="#e63946" stroke-width="0.8"/>')
        lines.append(f'<line x1="{hx - 5}" y1="450" x2="{hx + 5}" y2="450" stroke="#e63946" stroke-width="0.8"/>')
        lines.append(f'<text x="{hx - 10}" y="{450 - total_h / 2}" text-anchor="middle" font-size="9" fill="#e63946" font-weight="700" transform="rotate(-90, {hx - 10}, {450 - total_h / 2})">{total_h * 0.7:.0f}\'</text>')

        lines.append(f'<text x="350" y="510" text-anchor="middle" font-size="9" fill="#999">Illustrative front elevation · Not to exact scale</text>')
        lines.append(f'</svg>')
        return "\n".join(lines)
