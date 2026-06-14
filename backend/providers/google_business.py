"""Google Business discovery provider — uses Google Places API if configured."""
import logging
from typing import Any, Dict, List, Optional
import httpx
from .base import BusinessDiscoveryProvider

log = logging.getLogger(__name__)


class GoogleBusinessProvider(BusinessDiscoveryProvider):
    name = "google_business"
    display_name = "Google Business"
    description = "Discover businesses via Google Places API (Text Search). Provide google_places_api_key in Admin Settings."
    documentation_url = "https://developers.google.com/maps/documentation/places/web-service/text-search"
    requires_config = ["google_places_api_key"]
    supports_scheduling = True
    supports_run_now = True

    async def discover_businesses(self, limit: int = 10, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.configured:
            log.info("GoogleBusinessProvider not configured — returning empty.")
            return []
        key = self._config.get("google_places_api_key")
        q = (query or {}).get("q") or "new businesses in Mumbai"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    "https://maps.googleapis.com/maps/api/place/textsearch/json",
                    params={"query": q, "key": key, "region": "in"},
                )
            if r.status_code != 200:
                log.warning(f"Google Places returned {r.status_code}")
                return []
            data = r.json()
            return (data.get("results") or [])[:limit]
        except Exception as e:
            log.warning(f"GoogleBusiness fetch failed: {e}")
            return []

    def normalize_data(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        loc = (raw.get("geometry") or {}).get("location") or {}
        return {
            "business_name": raw.get("name"),
            "address": raw.get("formatted_address"),
            "latitude": loc.get("lat"),
            "longitude": loc.get("lng"),
            "category": (raw.get("types") or [None])[0],
            "source": self.name,
            "source_url": f"https://www.google.com/maps/place/?q=place_id:{raw.get('place_id')}" if raw.get("place_id") else None,
            "confidence_score": 0.65,
        }
