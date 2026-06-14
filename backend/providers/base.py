"""BusinessDiscoveryProvider — abstract base + standard data contract."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional, Tuple


# Standard schema (mirrors the businesses table fields the providers should fill)
STANDARD_FIELDS = [
    "business_name", "gst_number", "address", "locality", "city", "district", "state", "country", "pincode",
    "website", "phone", "email", "linkedin_url", "director_name", "registration_date",
    "company_type", "industry", "category", "sub_category", "employee_estimate",
    "latitude", "longitude", "source", "source_url", "confidence_score",
]


@dataclass
class StandardBusiness:
    """Standard normalized business schema returned by all providers."""
    business_name: str
    source: str
    gst_number: Optional[str] = None
    address: Optional[str] = None
    locality: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    pincode: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    director_name: Optional[str] = None
    registration_date: Optional[date] = None
    company_type: Optional[str] = None
    industry: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    employee_estimate: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source_url: Optional[str] = None
    confidence_score: float = 0.5
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in STANDARD_FIELDS if hasattr(self, k)}


@dataclass
class ValidationResult:
    valid: bool
    reason: Optional[str] = None


class BusinessDiscoveryProvider(ABC):
    """Abstract base for all discovery sources.

    Implementations must define methods:
      - get_source_name
      - discover_businesses
      - normalize_data
      - validate
      - deduplicate

    Source metadata fields:
      - name (machine-readable)
      - display_name (human-readable)
      - description
      - requires_config
      - configured (runtime)
    """

    name: str = "base"
    display_name: str = "Base Provider"
    description: str = "Abstract base provider — should not be used directly."
    requires_config: List[str] = []
    documentation_url: Optional[str] = None
    supports_scheduling: bool = False
    supports_run_now: bool = True

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        self.configured: bool = self._compute_configured()

    # ----- Required overrides -----

    def get_source_name(self) -> str:
        return self.name

    @abstractmethod
    async def discover_businesses(self, limit: int = 10, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Returns a list of raw provider-specific dicts."""

    def normalize_data(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Map a raw provider row to the standard schema. Default: identity + source stamp."""
        out = {k: raw.get(k) for k in STANDARD_FIELDS}
        out["source"] = self.name
        return out

    def validate(self, row: Dict[str, Any]) -> ValidationResult:
        if not row.get("business_name"):
            return ValidationResult(False, "Missing business_name")
        # GST is optional but if present, must be 15 chars
        gst = row.get("gst_number")
        if gst and len(gst) not in (0, 15):
            return ValidationResult(False, "Invalid GST length")
        return ValidationResult(True)

    async def deduplicate(self, candidates: List[Dict[str, Any]], find_dup_fn) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Default deduplication using the provided find_dup_fn(candidate) -> existing|None."""
        unique, dups = [], []
        seen_keys = set()
        for c in candidates:
            # In-batch dedup keys
            key_candidates = [
                ("gst", (c.get("gst_number") or "").strip().upper()),
                ("web", (c.get("website") or "").strip().lower()),
                ("phn", (c.get("phone") or "").strip()),
                ("npc", f"{(c.get('business_name') or '').lower().strip()}|{(c.get('pincode') or '').strip()}"),
            ]
            in_batch_dup = False
            for kind, val in key_candidates:
                if val and val != "" and (kind, val) in seen_keys:
                    in_batch_dup = True
                    break
            if in_batch_dup:
                dups.append(c)
                continue
            existing = await find_dup_fn(c)
            if existing:
                dups.append(c)
                continue
            for kind, val in key_candidates:
                if val and val != "":
                    seen_keys.add((kind, val))
            unique.append(c)
        return unique, dups

    # ----- Helpers -----

    def _compute_configured(self) -> bool:
        for k in self.requires_config:
            if not self._config.get(k):
                return False
        return True

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "requires_config": self.requires_config,
            "configured": self.configured,
            "documentation_url": self.documentation_url,
            "supports_scheduling": self.supports_scheduling,
            "supports_run_now": self.supports_run_now,
        }
