"""CSV import provider — records arrive via upload."""
from typing import Any, Dict, List, Optional
from .base import BusinessDiscoveryProvider


class CSVImportProvider(BusinessDiscoveryProvider):
    name = "csv_import"
    display_name = "CSV Import"
    description = "Bulk import via CSV upload. Headers must match the standard business schema."
    requires_config = []
    supports_scheduling = False
    supports_run_now = False

    async def discover_businesses(self, limit: int = 10, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return []
