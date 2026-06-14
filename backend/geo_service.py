"""Geo intelligence: enrich businesses with latitude/longitude from city + pincode."""
import logging
from typing import Dict, Optional, Tuple

log = logging.getLogger(__name__)

# Approximate centroids — sufficient for clustering + maps; precise enough for India dashboards.
CITY_CENTROIDS: Dict[str, Tuple[float, float]] = {
    "Mumbai": (19.0760, 72.8777),
    "Thane": (19.2183, 72.9781),
    "Navi Mumbai": (19.0330, 73.0297),
    "Pune": (18.5204, 73.8567),
    "Bengaluru": (12.9716, 77.5946),
    "Delhi": (28.6139, 77.2090),
    "Chennai": (13.0827, 80.2707),
    "Hyderabad": (17.3850, 78.4867),
    "Kolkata": (22.5726, 88.3639),
}

PINCODE_HINTS: Dict[str, Tuple[float, float]] = {
    "400001": (18.9388, 72.8354),
    "400052": (19.0596, 72.8295),
    "400072": (19.1136, 72.8697),
    "400601": (19.2183, 72.9781),
    "400607": (19.1972, 72.9722),
    "400703": (19.0760, 73.0157),
    "400706": (19.0330, 73.0297),
    "400614": (19.0411, 73.0282),
}


def enrich_geo(row: dict) -> dict:
    """Fill latitude/longitude if missing, based on pincode then city."""
    if (row.get("latitude") in (None, 0, 0.0)) or (row.get("longitude") in (None, 0, 0.0)):
        pincode = (row.get("pincode") or "").strip()
        if pincode in PINCODE_HINTS:
            lat, lng = PINCODE_HINTS[pincode]
        else:
            city = (row.get("city") or "").strip()
            if city in CITY_CENTROIDS:
                lat, lng = CITY_CENTROIDS[city]
            else:
                return row
        row["latitude"] = lat
        row["longitude"] = lng
    return row
