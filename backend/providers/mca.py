"""MCA discovery provider — documented placeholder."""
import logging
from typing import Any, Dict, List, Optional
from .base import BusinessDiscoveryProvider

log = logging.getLogger(__name__)


class MCAProvider(BusinessDiscoveryProvider):
    name = "mca"
    display_name = "MCA Portal"
    description = "Newly incorporated Indian companies from the Ministry of Corporate Affairs. Requires captcha/login; placeholder until a compliant integration is approved."
    documentation_url = "https://www.mca.gov.in/"
    requires_config = ["mca_credentials"]
    supports_scheduling = True
    supports_run_now = True

    async def discover_businesses(self, limit: int = 10, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        log.info("MCAProvider placeholder — returning empty.")
        return []
