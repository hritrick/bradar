"""IndiaMART discovery provider — documented placeholder."""
import logging
from typing import Any, Dict, List, Optional
from .base import BusinessDiscoveryProvider

log = logging.getLogger(__name__)


class IndiaMARTProvider(BusinessDiscoveryProvider):
    name = "indiamart"
    display_name = "IndiaMART"
    description = "Bulk supplier/buyer leads from IndiaMART. Requires CRM Lead Manager API key (paid)."
    documentation_url = "https://seller.indiamart.com/"
    requires_config = ["indiamart_api_key"]
    supports_scheduling = True
    supports_run_now = True

    async def discover_businesses(self, limit: int = 10, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.configured:
            log.info("IndiaMARTProvider not configured — returning empty.")
            return []
        log.info("IndiaMARTProvider placeholder — real implementation requires partner integration.")
        return []
