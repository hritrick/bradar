"""Provider registry — builds provider instances using settings + DB-stored config."""
import logging
from typing import Dict, List, Optional, Any
from .base import BusinessDiscoveryProvider
from .manual import ManualEntryProvider
from .csv_import import CSVImportProvider
from .opencorporates import OpenCorporatesProvider
from .mca import MCAProvider
from .google_business import GoogleBusinessProvider
from .indiamart import IndiaMARTProvider
from .justdial import JustdialProvider
from .synthetic import SyntheticProvider

log = logging.getLogger(__name__)

# Order matters for UI listing
PROVIDER_CLASSES = [
    ManualEntryProvider,
    CSVImportProvider,
    OpenCorporatesProvider,
    MCAProvider,
    GoogleBusinessProvider,
    IndiaMARTProvider,
    JustdialProvider,
    SyntheticProvider,
]


async def _load_settings_for_providers() -> Dict[str, str]:
    from settings_service import get_setting
    keys = [
        "opencorporates_api_token",
        "google_places_api_key",
        "indiamart_api_key",
        "justdial_api_key",
        "mca_credentials",
    ]
    out: Dict[str, str] = {}
    for k in keys:
        v = await get_setting(k)
        if v:
            out[k] = v
    return out


async def build_providers() -> Dict[str, BusinessDiscoveryProvider]:
    settings = await _load_settings_for_providers()
    out: Dict[str, BusinessDiscoveryProvider] = {}
    for cls in PROVIDER_CLASSES:
        cfg = {k: settings.get(k) for k in cls.requires_config}
        out[cls.name] = cls(config=cfg)
    return out


async def get_provider(name: str) -> Optional[BusinessDiscoveryProvider]:
    providers = await build_providers()
    return providers.get(name)


async def provider_metadata() -> List[Dict[str, Any]]:
    providers = await build_providers()
    return [p.to_metadata() for p in providers.values()]
