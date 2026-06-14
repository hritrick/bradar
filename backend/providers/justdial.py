"""Justdial discovery provider — documented placeholder."""
import logging
from typing import Any, Dict, List, Optional
from .base import BusinessDiscoveryProvider

log = logging.getLogger(__name__)


class JustdialProvider(BusinessDiscoveryProvider):
    name = "justdial"
    display_name = "Justdial"
    description = "Discover local Indian businesses listed on Justdial. Requires partner API access."
    documentation_url = "https://www.justdial.com/"
    requires_config = ["justdial_api_key"]
    supports_scheduling = True
    supports_run_now = True

    async def discover_businesses(self, limit: int = 10, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.configured:
            log.info("JustdialProvider not configured — returning empty.")
            return []
        log.info("JustdialProvider placeholder — real implementation requires partner integration.")
        return []
