"""Generates room layouts using AI (Gemini) or algorithmic Vastu-aware packing."""

import json
import math
from vastu_engine import VastuEngine
from ai_adapter import AIAdapter


class LayoutGenerator:
    """Generates room layouts with real rectangular coordinates, no grid cells."""

    CORRIDOR_WIDTH = 4  # feet

    @classmethod
    def generate(cls, user_data, rooms_list):
        """Generate a complete room layout. Try AI first, fall back to algorithmic."""
        site_length = float(user_data.get("site_length", 60))
        site_width = float(user_data.get("site_width", 40))
        facing = user_data.get("facing", "north")

        # Try Gemini AI if available
        if AIAdapter.has_gemini():
            prompt = AIAdapter.build_ai_prompt(user_data)
            ai_result = AIAdapter.call_gemini(prompt)
            if ai_result and cls.validate_layout(ai_result, site_length, site_width, rooms_list):
                return cls._process_ai_result(ai_result, user_data, rooms_list)

        # Fall back to algorithmic layout
        return cls._algorithmic_layout(rooms_list, site_length, site_width, facing, user_data)

    @classmethod
    def validate_layout(cls, data, max_x, max_y, expected_rooms):
        """Validate AI-generated layout is usable."""
        if not data or "rooms" not in data:
            return False
        rooms = data["rooms"]
        if len(rooms) < len(expected_rooms) // 2:
            return False
        for r in rooms:
            if not all(k in r for k in ["name", "x", "y", "width", "height"]):
                return False
            if r["x"] < 0 or r["y"] < 0:
                return False
            if r["x"] + r["width"] > max_x or r["y"] + r["height"] > max_y:
                return False
        # Check for overlaps
        for i, a in enumerate(rooms):
            for b in rooms[i + 1:]:
                if cls._rects_overlap(a, b):
                    if a.get("allow_overlap") or b.get("allow_overlap"):
                        continue
                    return False
        return True

    @staticmethod
    def _rects_overlap(a, b, margin=0.5):
        return not (
            a["x"] + a["width"] + margin <= b["x"] or
            b["x"] + b["width"] + margin <= a["x"] or
            a["y"] + a["height"] + margin <= b["y"] or
            b["y"] + b["height"] + margin <= a["y"]
        )

    @classmethod
    def _process_ai_result(cls, data, user_data, rooms_list):
        """Process AI result into standard format."""
        facing = user_data.get("facing", "north")
        site_length = float(user_data.get("site_length", 60))
        site_width = float(user_data.get("site_width", 40))
        floors = int(user_data.get("floors", 1))

        rooms_data = data.get("rooms", [])
        result_rooms = []
        for r in rooms_data:
            zone = VastuEngine.get_zone_for_point(
                (r["x"] + r["width"] / 2) / site_length,
                (r["y"] + r["height"] / 2) / site_length
            )
            score = VastuEngine.get_room_zone_score(r["name"], zone)
            result_rooms.append({
                "name": r["name"],
                "x": r["x"], "y": r["y"],
                "width": r["width"], "height": r["height"],
                "zone": zone, "score": score,
                "doors": r.get("doors", [{"side": "bottom", "position": 0.5}]),
                "windows": r.get("windows", [{"side": "top", "position": 0.5}]),
                "area_sqft": round(r["width"] * r["height"], 1)
            })

        # Build walls from room boundaries
        walls = cls._build_walls(result_rooms, site_length, site_width)

        return {
            "rooms": result_rooms,
            "walls": walls,
            "front_door": data.get("front_door", {"x": site_length * 0.5, "y": 0, "facing": facing}),
            "stairs": data.get("stairs"),
            "corridors": data.get("corridors", []),
            "facing": facing,
            "site_length": site_length,
            "site_width": site_width,
            "floors": floors,
            "style": user_data.get("style", "Modern"),
            "source": "ai"
        }

    @classmethod
    def _algorithmic_layout(cls, rooms_list, site_length, site_width, facing, user_data):
        """Generate room layout using Vastu-aware zone packing."""
        floors = int(user_data.get("floors", 1))
        style = user_data.get("style", "Modern")

        # 1. Assign rooms to zones
        zone_assignments = cls._assign_zones(rooms_list)
        # 2. Calculate available area per zone
        zone_areas = cls._get_zone_areas(site_length, site_width)
        # 3. Generate room rectangles within zones
        rooms = cls._pack_rooms_in_zones(zone_assignments, zone_areas, site_length, site_width)
        # 4. Add corridor space
        rooms = cls._add_corridors(rooms, site_length, site_width)
        # 5. Calculate scores
        for r in rooms:
            cx = (r["x"] + r["width"] / 2) / site_length
            cy = (r["y"] + r["height"] / 2) / site_width
            zone = VastuEngine.get_zone_for_point(cx, cy)
            r["zone"] = zone
            r["score"] = VastuEngine.get_room_zone_score(r["name"], zone)

        # 6. Build walls
        walls = cls._build_walls(rooms, site_length, site_width)

        # 7. Place front door
        door_pos = cls._place_front_door(facing, site_length, site_width, rooms)

        # 8. Add doors and windows to rooms
        for r in rooms:
            if not r.get("doors"):
                r["doors"] = [cls._find_door_position(r, rooms, walls, site_length, site_width)]
            if not r.get("windows"):
                r["windows"] = [{"side": "top", "position": 0.5}]
            r["area_sqft"] = round(r["width"] * r["height"], 1)

        return {
            "rooms": rooms,
            "walls": walls,
            "front_door": door_pos,
            "stairs": cls._place_stairs(rooms, site_length, site_width) if floors > 1 else None,
            "corridors": [],
            "facing": facing,
            "site_length": site_length,
            "site_width": site_width,
            "floors": floors,
            "style": style,
            "source": "algorithmic"
        }

    @classmethod
    def _assign_zones(cls, rooms):
        """Assign each room to its best available Vastu zone."""
        assignments = {}  # zone -> [room_names]
        used_zones = set()

        sorted_rooms = sorted(rooms, key=lambda r: {
            "Pooja Room": 0, "Kitchen": 1, "Master Bedroom": 2,
            "Living Room": 3, "Dining Room": 4, "Study": 5,
            "Bedroom": 6, "Guest Room": 7, "Bathroom": 8,
            "Store Room": 9, "Parking": 10, "Staircase": 11
        }.get(r, 99))

        for room in sorted_rooms:
            rules = VastuEngine.ROOM_RULES.get(room, {})
            best = rules.get("primary_zone", "center")
            alts = rules.get("alt_zones", [])
            avoid = rules.get("avoid_zones", [])

            placed = False
            for z in [best] + alts:
                if z not in used_zones and z not in avoid:
                    if z not in assignments:
                        assignments[z] = []
                    assignments[z].append(room)
                    used_zones.add(z)
                    placed = True
                    break

            if not placed:
                for z in VastuEngine.ZONES:
                    if z not in used_zones and z not in avoid:
                        if z not in assignments:
                            assignments[z] = []
                        assignments[z].append(room)
                        used_zones.add(z)
                        placed = True
                        break

            if not placed:
                for z in VastuEngine.ZONES:
                    if z not in used_zones:
                        if z not in assignments:
                            assignments[z] = []
                        assignments[z].append(room)
                        used_zones.add(z)
                        break

        return assignments

    @classmethod
    def _get_zone_areas(cls, site_length, site_width):
        """Get pixel coordinates for each zone."""
        areas = {}
        for zname, zdata in VastuEngine.ZONES.items():
            xr = zdata["x_range"]
            yr = zdata["y_range"]
            areas[zname] = {
                "x": xr[0] * site_length,
                "y": yr[0] * site_width,
                "w": (xr[1] - xr[0]) * site_length,
                "h": (yr[1] - yr[0]) * site_width
            }
        return areas

    @classmethod
    def _pack_rooms_in_zones(cls, assignments, zone_areas, site_length, site_width):
        """Pack rooms into their assigned zones with proper dimensions."""
        rooms = []
        for zone, room_names in assignments.items():
            za = zone_areas.get(zone, {"x": 0, "y": 0, "w": site_length / 3, "h": site_width / 3})
            zone_w = za["w"]
            zone_h = za["h"]
            zone_x = za["x"]
            zone_y = za["y"]
            n = len(room_names)

            if n == 0:
                continue
            elif n == 1:
                rname = room_names[0]
                size = VastuEngine.get_room_size(rname)
                ideal_w = min(size[0], zone_w * 0.85)
                ideal_h = min(size[1], zone_h * 0.85)
                # Scale to fit zone
                scale = min(zone_w * 0.85 / ideal_w, zone_h * 0.85 / ideal_h, 1.5)
                rw = min(ideal_w * scale, zone_w * 0.9)
                rh = min(ideal_h * scale, zone_h * 0.9)
                rooms.append({
                    "name": rname,
                    "x": zone_x + (zone_w - rw) / 2,
                    "y": zone_y + (zone_h - rh) / 2,
                    "width": round(rw, 1),
                    "height": round(rh, 1)
                })
            else:
                # Multiple rooms in one zone - split vertically or horizontally
                cols = math.ceil(math.sqrt(n))
                rows = math.ceil(n / cols)
                cell_w = zone_w / cols
                cell_h = zone_h / rows

                for i, rname in enumerate(room_names):
                    col = i % cols
                    row = i // cols
                    size = VastuEngine.get_room_size(rname)
                    rw = min(size[0], cell_w * 0.85)
                    rh = min(size[1], cell_h * 0.85)
                    # Center in cell
                    rx = zone_x + col * cell_w + (cell_w - rw) / 2
                    ry = zone_y + row * cell_h + (cell_h - rh) / 2
                    rooms.append({
                        "name": rname,
                        "x": round(rx, 1),
                        "y": round(ry, 1),
                        "width": round(rw, 1),
                        "height": round(rh, 1)
                    })

        # Adjust rooms that might overlap zone boundaries
        for r in rooms:
            r["x"] = max(0, min(r["x"], site_length - r["width"]))
            r["y"] = max(0, min(r["y"], site_width - r["height"]))

        return rooms

    @classmethod
    def _add_corridors(cls, rooms, site_length, site_width):
        """Add corridor space by adjusting room positions."""
        # Reduce room sizes slightly to account for circulation
        for r in rooms:
            r["width"] = max(r["width"] * 0.92, 6)
            r["height"] = max(r["height"] * 0.92, 4)
        return rooms

    @classmethod
    def _build_walls(cls, rooms, site_length, site_width):
        """Generate wall segments from room boundaries."""
        walls = []
        # Add tolerance for shared walls
        EPS = 0.3

        all_rects = rooms[:]

        # External walls (site boundary)
        walls.append({"x1": 0, "y1": 0, "x2": site_length, "y2": 0, "type": "external"})
        walls.append({"x1": site_length, "y1": 0, "x2": site_length, "y2": site_width, "type": "external"})
        walls.append({"x1": site_length, "y1": site_width, "x2": 0, "y2": site_width, "type": "external"})
        walls.append({"x1": 0, "y1": site_width, "x2": 0, "y2": 0, "type": "external"})

        # Internal walls - for each room wall, check if it's shared
        for r in all_rects:
            room_walls = [
                {"x1": r["x"], "y1": r["y"], "x2": r["x"] + r["width"], "y2": r["y"], "side": "top"},
                {"x1": r["x"] + r["width"], "y1": r["y"], "x2": r["x"] + r["width"], "y2": r["y"] + r["height"], "side": "right"},
                {"x1": r["x"] + r["width"], "y1": r["y"] + r["height"], "x2": r["x"], "y2": r["y"] + r["height"], "side": "bottom"},
                {"x1": r["x"], "y1": r["y"] + r["height"], "x2": r["x"], "y2": r["y"], "side": "left"}
            ]

            for rw in room_walls:
                # Check if this wall segment is on the site boundary
                is_boundary = (
                    (rw["y1"] == 0 and rw["y2"] == 0) or
                    (rw["y1"] == site_width and rw["y2"] == site_width) or
                    (rw["x1"] == 0 and rw["x2"] == 0) or
                    (rw["x1"] == site_length and rw["x2"] == site_length)
                )

                if is_boundary:
                    continue  # Already added as external

                # Check if shared with another room
                shared = False
                for other in all_rects:
                    if other is r:
                        continue
                    if cls._walls_match(rw, other, EPS):
                        shared = True
                        break

                wtype = "internal"
                if not shared:
                    wtype = "external"

                walls.append({**rw, "type": wtype})

        # Remove duplicate/overlapping walls (same line, same type)
        unique_walls = []
        for w in walls:
            is_dup = False
            for uw in unique_walls:
                if cls._walls_same(w, uw, EPS):
                    is_dup = True
                    break
            if not is_dup:
                unique_walls.append(w)

        return unique_walls

    @staticmethod
    def _walls_match(w1, other_rect, eps):
        """Check if a wall segment aligns with a room's opposite wall."""
        # Check if wall is on other's boundary within tolerance
        # Top wall
        if abs(w1["y1"] - other_rect["y"]) < eps and abs(w1["y2"] - other_rect["y"]) < eps:
            if w1["x1"] < other_rect["x"] + other_rect["width"] + eps and w1["x2"] > other_rect["x"] - eps:
                return True
        # Bottom wall
        if abs(w1["y1"] - (other_rect["y"] + other_rect["height"])) < eps and abs(w1["y2"] - (other_rect["y"] + other_rect["height"])) < eps:
            if w1["x1"] < other_rect["x"] + other_rect["width"] + eps and w1["x2"] > other_rect["x"] - eps:
                return True
        # Left wall
        if abs(w1["x1"] - other_rect["x"]) < eps and abs(w1["x2"] - other_rect["x"]) < eps:
            if w1["y1"] < other_rect["y"] + other_rect["height"] + eps and w1["y2"] > other_rect["y"] - eps:
                return True
        # Right wall
        if abs(w1["x1"] - (other_rect["x"] + other_rect["width"])) < eps and abs(w1["x2"] - (other_rect["x"] + other_rect["width"])) < eps:
            if w1["y1"] < other_rect["y"] + other_rect["height"] + eps and w1["y2"] > other_rect["y"] - eps:
                return True
        return False

    @staticmethod
    def _walls_same(w1, w2, eps):
        """Check if two wall definitions describe the same wall."""
        return (abs(w1["x1"] - w2["x1"]) < eps and abs(w1["y1"] - w2["y1"]) < eps and
                abs(w1["x2"] - w2["x2"]) < eps and abs(w1["y2"] - w2["y2"]) < eps and
                w1["type"] == w2["type"])

    @staticmethod
    def _place_front_door(facing, site_length, site_width, rooms):
        """Determine front door position based on facing direction."""
        if facing == "north":
            return {"x": site_length * 0.45, "y": 0, "facing": "north"}
        elif facing == "south":
            return {"x": site_length * 0.45, "y": site_width, "facing": "south"}
        elif facing == "east":
            return {"x": site_length, "y": site_width * 0.45, "facing": "east"}
        elif facing == "west":
            return {"x": 0, "y": site_width * 0.45, "facing": "west"}
        elif facing == "northeast":
            return {"x": site_length * 0.55, "y": 0, "facing": "north"}
        return {"x": site_length * 0.5, "y": 0, "facing": "north"}

    @staticmethod
    def _place_stairs(rooms, site_length, site_width):
        """Place staircase if multi-floor."""
        sw_rooms = [r for r in rooms if r["x"] < site_length * 0.4 and r["y"] > site_width * 0.6]
        if sw_rooms:
            # Place stairs near SW corner
            return {"x": site_length * 0.05, "y": site_width * 0.7, "width": 12, "height": 6}
        return {"x": 5, "y": site_width * 0.6, "width": 12, "height": 6}

    @staticmethod
    def _find_door_position(room, all_rooms, walls, site_length, site_width):
        """Find a suitable door position for a room."""
        # Try bottom side first (toward corridor)
        return {"side": "bottom", "position": 0.5}
