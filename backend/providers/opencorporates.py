"""OpenCorporates discovery provider with retry on transient HTTP errors."""
import logging
from typing import Any, Dict, List, Optional
import httpx
from .base import BusinessDiscoveryProvider
from retry_util import retry_async

log = logging.getLogger(__name__)

HTTP_RETRYABLE = (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError, httpx.ReadTimeout)


class OpenCorporatesProvider(BusinessDiscoveryProvider):
    name = "opencorporates"
    display_name = "OpenCorporates"
    description = "Public company registry API (global). Configure your API token to enable real fetches."
    documentation_url = "https://api.opencorporates.com/"
    requires_config = ["opencorporates_api_token"]
    supports_scheduling = True
    supports_run_now = True

    @retry_async(max_attempts=3, base_delay=0.5, max_delay=4.0, retryable=HTTP_RETRYABLE)
    async def _fetch(self, params: dict) -> dict:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get("https://api.opencorporates.com/v0.4.7/companies/search", params=params)
            if r.status_code >= 500:
                raise httpx.RemoteProtocolError(f"OpenCorporates HTTP {r.status_code}", request=r.request)
            return {"status": r.status_code, "json": r.json() if r.status_code == 200 else None, "text": r.text[:300] if r.status_code != 200 else ""}

    async def discover_businesses(self, limit: int = 10, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.configured:
            log.info("OpenCorporatesProvider not configured — returning empty.")
            return []
        token = self._config.get("opencorporates_api_token")
        try:
            params = {
                "q": (query or {}).get("q") or "new",
                "jurisdiction_code": (query or {}).get("jurisdiction") or "in",
                "per_page": min(50, limit),
                "api_token": token,
            }
            r = await self._fetch(params)
            if r["status"] != 200:
                log.warning(f"OpenCorporates returned {r['status']}: {r['text']}")
                return []
            companies = (r["json"].get("results") or {}).get("companies") or []
            return [c.get("company", {}) for c in companies][:limit]
        except Exception as e:
            log.warning(f"OpenCorporates fetch failed: {e}")
            return []

    def normalize_data(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "business_name": raw.get("name"),
            "company_type": raw.get("company_type"),
            "registration_date": raw.get("incorporation_date"),
            "address": (raw.get("registered_address_in_full") or None),
            "country": (raw.get("jurisdiction_code") or "in").upper() if raw.get("jurisdiction_code") == "in" else None,
            "source": self.name,
            "source_url": raw.get("opencorporates_url"),
            "confidence_score": 0.7,
        }
