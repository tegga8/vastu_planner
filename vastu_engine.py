"""Vastu Shastra zone definitions and compatibility rules."""

class VastuEngine:
    """Vastu zone definitions and room-zone compatibility scoring."""

    # 9-zone Vastu Purusha Mandala with plot layout (North at top)
    # NW    N    NE
    #   W   C   E
    # SW    S    SE
    ZONES = {
        "northeast": {
            "label": "North-East (Ishanya)", "element": "Water",
            "color": "#C8E6C9", "border": "#4CAF50",
            "suitable": ["Pooja Room", "Meditation Room", "Study"],
            "unsuitable": ["Kitchen", "Master Bedroom", "Bathroom", "Store Room"],
            "x_range": (0.66, 1.0), "y_range": (0.0, 0.33)
        },
        "north": {
            "label": "North (Kubera)", "element": "Water",
            "color": "#BBDEFB", "border": "#2196F3",
            "suitable": ["Living Room", "Study", "Main Door"],
            "unsuitable": ["Master Bedroom", "Kitchen", "Bathroom"],
            "x_range": (0.33, 0.66), "y_range": (0.0, 0.33)
        },
        "northwest": {
            "label": "North-West (Vayu)", "element": "Air",
            "color": "#E1BEE7", "border": "#9C27B0",
            "suitable": ["Guest Room", "Store Room", "Bathroom", "Parking"],
            "unsuitable": ["Pooja Room", "Kitchen", "Master Bedroom"],
            "x_range": (0.0, 0.33), "y_range": (0.0, 0.33)
        },
        "east": {
            "label": "East (Indra)", "element": "Fire",
            "color": "#FFE0B2", "border": "#FF9800",
            "suitable": ["Living Room", "Study", "Bathroom", "Verandah"],
            "unsuitable": ["Master Bedroom", "Store Room", "Kitchen"],
            "x_range": (0.66, 1.0), "y_range": (0.33, 0.66)
        },
        "center": {
            "label": "Center (Brahma)", "element": "Space",
            "color": "#F0F4C3", "border": "#CDDC39",
            "suitable": ["Open Courtyard", "Living Room", "Foyer"],
            "unsuitable": ["Kitchen", "Bedroom", "Bathroom", "Store Room"],
            "x_range": (0.33, 0.66), "y_range": (0.33, 0.66)
        },
        "west": {
            "label": "West (Varuna)", "element": "Water",
            "color": "#F8BBD0", "border": "#E91E63",
            "suitable": ["Dining Room", "Store Room", "Bedroom"],
            "unsuitable": ["Pooja Room", "Kitchen", "Main Door"],
            "x_range": (0.0, 0.33), "y_range": (0.33, 0.66)
        },
        "southeast": {
            "label": "South-East (Agni)", "element": "Fire",
            "color": "#FFF9C4", "border": "#FFC107",
            "suitable": ["Kitchen", "Dining Room"],
            "unsuitable": ["Pooja Room", "Master Bedroom", "Bathroom"],
            "x_range": (0.66, 1.0), "y_range": (0.66, 1.0)
        },
        "south": {
            "label": "South (Yama)", "element": "Earth",
            "color": "#FFCDD2", "border": "#F44336",
            "suitable": ["Bedroom", "Master Bedroom"],
            "unsuitable": ["Pooja Room", "Kitchen", "Living Room", "Main Door"],
            "x_range": (0.33, 0.66), "y_range": (0.66, 1.0)
        },
        "southwest": {
            "label": "South-West (Nairutya)", "element": "Earth",
            "color": "#C5CAE9", "border": "#3F51B5",
            "suitable": ["Master Bedroom", "Store Room"],
            "unsuitable": ["Pooja Room", "Kitchen", "Bathroom", "Main Door"],
            "x_range": (0.0, 0.33), "y_range": (0.66, 1.0)
        }
    }

    ROOM_RULES = {
        "Master Bedroom": {
            "primary_zone": "southwest", "score": 10,
            "alt_zones": ["south"],
            "avoid_zones": ["northeast", "north", "east", "center"],
            "standard_sizes": {"min": [14, 12], "ideal": [16, 14], "max": [22, 18]},
            "direction": "Head towards East while sleeping"
        },
        "Bedroom": {
            "primary_zone": "southwest", "score": 9,
            "alt_zones": ["south", "west"],
            "avoid_zones": ["northeast", "north", "center"],
            "standard_sizes": {"min": [12, 10], "ideal": [14, 12], "max": [18, 14]},
            "direction": "Children in West, guests in NW"
        },
        "Kitchen": {
            "primary_zone": "southeast", "score": 10,
            "alt_zones": ["northwest"],
            "avoid_zones": ["northeast", "southwest", "north", "center"],
            "standard_sizes": {"min": [10, 8], "ideal": [12, 10], "max": [16, 12]},
            "direction": "Cook facing East"
        },
        "Living Room": {
            "primary_zone": "north", "score": 10,
            "alt_zones": ["east", "northeast"],
            "avoid_zones": ["southwest", "south", "southeast"],
            "standard_sizes": {"min": [16, 12], "ideal": [20, 16], "max": [28, 22]},
            "direction": "Furniture along South/West walls"
        },
        "Dining Room": {
            "primary_zone": "west", "score": 9,
            "alt_zones": ["southeast", "east"],
            "avoid_zones": ["northeast", "south", "center"],
            "standard_sizes": {"min": [12, 10], "ideal": [14, 12], "max": [18, 14]},
            "direction": "West wall preferred"
        },
        "Pooja Room": {
            "primary_zone": "northeast", "score": 10,
            "alt_zones": ["east", "north"],
            "avoid_zones": ["south", "southwest", "southeast", "west"],
            "standard_sizes": {"min": [6, 5], "ideal": [8, 6], "max": [12, 10]},
            "direction": "Face East while praying"
        },
        "Study": {
            "primary_zone": "northeast", "score": 9,
            "alt_zones": ["east", "north"],
            "avoid_zones": ["southwest", "south"],
            "standard_sizes": {"min": [8, 6], "ideal": [10, 8], "max": [14, 12]},
            "direction": "Desk facing East or North"
        },
        "Guest Room": {
            "primary_zone": "northwest", "score": 9,
            "alt_zones": ["west"],
            "avoid_zones": ["southwest", "northeast"],
            "standard_sizes": {"min": [10, 10], "ideal": [12, 12], "max": [16, 14]},
            "direction": "NW corner"
        },
        "Bathroom": {
            "primary_zone": "northwest", "score": 8,
            "alt_zones": ["west", "south"],
            "avoid_zones": ["northeast", "southeast", "center"],
            "standard_sizes": {"min": [6, 4], "ideal": [8, 5], "max": [10, 8]},
            "direction": "NW/W preferred"
        },
        "Store Room": {
            "primary_zone": "southwest", "score": 9,
            "alt_zones": ["northwest", "west"],
            "avoid_zones": ["northeast", "center", "east"],
            "standard_sizes": {"min": [6, 4], "ideal": [8, 6], "max": [12, 10]},
            "direction": "Heavy items in SW"
        },
        "Parking": {
            "primary_zone": "northwest", "score": 8,
            "alt_zones": ["southeast", "west"],
            "avoid_zones": ["northeast", "center", "southwest"],
            "standard_sizes": {"min": [16, 10], "ideal": [18, 12], "max": [22, 14]},
            "direction": "NW corner"
        },
        "Staircase": {
            "primary_zone": "southwest", "score": 8,
            "alt_zones": ["south", "west"],
            "avoid_zones": ["northeast", "center", "east"],
            "standard_sizes": {"min": [10, 5], "ideal": [12, 6], "max": [14, 8]},
            "direction": "Clockwise ascent"
        }
    }

    @staticmethod
    def get_zone_for_point(x_norm, y_norm):
        """Get zone name for a normalized point (0-1) on the plot."""
        for zname, zdata in VastuEngine.ZONES.items():
            xr, yr = zdata["x_range"], zdata["y_range"]
            if xr[0] <= x_norm <= xr[1] and yr[0] <= y_norm <= yr[1]:
                return zname
        return "center"

    @staticmethod
    def get_room_zone_score(room, zone):
        rules = VastuEngine.ROOM_RULES.get(room)
        if not rules:
            return 5
        if zone == rules["primary_zone"]:
            return 10
        if zone in rules["alt_zones"]:
            return 7
        if zone in rules["avoid_zones"]:
            return 1
        return 4

    @staticmethod
    def get_best_zone(room):
        return VastuEngine.ROOM_RULES.get(room, {}).get("primary_zone", "center")

    @staticmethod
    def get_room_size(room):
        return VastuEngine.ROOM_RULES.get(room, {}).get("standard_sizes", {"ideal": [10, 8]})["ideal"]

    @staticmethod
    def build_rooms_list(user_data):
        rooms = []
        bedrooms = int(user_data.get("bedrooms", 1))
        for i in range(bedrooms):
            rooms.append("Master Bedroom" if i == 0 else "Bedroom")
        yes_rooms = ["living_room", "kitchen", "dining", "pooja", "study", "guest", "store", "parking"]
        yes_map = {
            "living_room": "Living Room", "kitchen": "Kitchen", "dining": "Dining Room",
            "pooja": "Pooja Room", "study": "Study", "guest": "Guest Room",
            "store": "Store Room", "parking": "Parking"
        }
        for key, name in yes_map.items():
            val = user_data.get(key)
            if val in [True, "yes", "y", "true", "1"]:
                rooms.append(name)
        bathrooms = int(user_data.get("bathrooms", 0))
        for _ in range(bathrooms):
            rooms.append("Bathroom")
        if user_data.get("garden") in [True, "yes", "y", "true", "1"]:
            rooms.append("Garden")
        if not rooms:
            rooms = ["Living Room", "Kitchen", "Master Bedroom", "Bathroom"]
        return rooms

    @staticmethod
    def get_conversation_flow():
        return [
            {"id": "name", "question": "Namaste! 🙏 I'm your Vastu AI Architect. What's your name?", "field": "name", "type": "text"},
            {"id": "site_length", "question": "What is the length of your plot (in feet)?", "field": "site_length", "type": "number"},
            {"id": "site_width", "question": "What is the width of your plot (in feet)?", "field": "site_width", "type": "number"},
            {"id": "facing", "question": "Which direction does your plot face?", "field": "facing", "type": "choice", "options": ["North", "East", "South", "West", "North-East"]},
            {"id": "style", "question": "What architectural style do you prefer?", "field": "style", "type": "choice", "options": ["Modern", "Traditional", "Contemporary", "Minimalist"]},
            {"id": "floors", "question": "How many floors do you want (including ground)?", "field": "floors", "type": "number"},
            {"id": "bedrooms", "question": "How many bedrooms?", "field": "bedrooms", "type": "number"},
            {"id": "living_room", "question": "Separate Living Room?", "field": "living_room", "type": "boolean"},
            {"id": "kitchen", "question": "Kitchen?", "field": "kitchen", "type": "boolean"},
            {"id": "dining", "question": "Separate Dining Room?", "field": "dining", "type": "boolean"},
            {"id": "pooja", "question": "Pooja / Meditation Room?", "field": "pooja", "type": "boolean"},
            {"id": "study", "question": "Study / Home Office?", "field": "study", "type": "boolean"},
            {"id": "guest", "question": "Guest Room?", "field": "guest", "type": "boolean"},
            {"id": "store", "question": "Store Room?", "field": "store", "type": "boolean"},
            {"id": "bathrooms", "question": "How many bathrooms?", "field": "bathrooms", "type": "number"},
            {"id": "parking", "question": "Covered Parking?", "field": "parking", "type": "boolean"},
            {"id": "garden", "question": "Garden / Open Courtyard?", "field": "garden", "type": "boolean"},
            {"id": "confirm", "question": "All set! Shall I generate your complete Vastu-compliant plan now? 🏠", "field": "confirm", "type": "boolean"}
        ]
