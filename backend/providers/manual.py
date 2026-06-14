"""Manual entry provider — records arrive via UI form."""
from typing import Any, Dict, List, Optional
from .base import BusinessDiscoveryProvider


class ManualEntryProvider(BusinessDiscoveryProvider):
    name = "manual"
    display_name = "Manual Entry"
    description = "Records added by users via the dashboard form. No external API."
    requires_config = []
    supports_scheduling = False
    supports_run_now = False

    async def discover_businesses(self, limit: int = 10, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return []
