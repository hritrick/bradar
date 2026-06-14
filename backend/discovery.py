"""Discovery source interface + connectors."""
import logging
import random
from datetime import date, timedelta
from typing import List, Dict, Any, Protocol
from abc import ABC, abstractmethod

log = logging.getLogger(__name__)


class IDiscoverySource(ABC):
    """Pluggable discovery source. Implementations: fetch -> validate -> normalize -> dedup (dedup is done by pipeline.ingest_business)."""

    name: str = "base"
    description: str = ""
    configured: bool = False
    requires_config: List[str] = []

    @abstractmethod
    async def fetch_businesses(self, limit: int = 10, query: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        ...

    def validate(self, row: Dict[str, Any]) -> bool:
        return bool(row.get("business_name"))

    def normalize(self, row: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(row)
        out["source"] = self.name
        return out


class ManualEntryConnector(IDiscoverySource):
    name = "manual"
    description = "Records entered manually via the dashboard form."
    configured = True
    requires_config = []

    async def fetch_businesses(self, limit: int = 10, query: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        return []


class CSVUploadConnector(IDiscoverySource):
    name = "csv_upload"
    description = "Bulk-upload businesses via CSV. Accepts headers matching the businesses table."
    configured = True
    requires_config = []

    async def fetch_businesses(self, limit: int = 10, query: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        return []


class OpenCorporatesConnector(IDiscoverySource):
    name = "opencorporates"
    description = "Fetches recently incorporated companies from the OpenCorporates public API."
    requires_config = ["opencorporates_api_token"]

    def __init__(self, api_token: str | None = None):
        self.api_token = api_token
        self.configured = bool(api_token)

    async def fetch_businesses(self, limit: int = 10, query: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        if not self.configured:
            log.info("OpenCorporatesConnector not configured; returning empty.")
            return []
        # Placeholder for real OpenCorporates integration; left unimplemented to avoid hitting paid endpoints without explicit user key.
        log.info("OpenCorporates connector configured but real fetch is a placeholder; returning empty.")
        return []


class MCAConnector(IDiscoverySource):
    name = "mca"
    description = "Fetches newly incorporated companies from the MCA portal (placeholder — requires captcha/credentials)."
    configured = False
    requires_config = ["mca_credentials"]

    async def fetch_businesses(self, limit: int = 10, query: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        log.info("MCAConnector placeholder; returning empty.")
        return []


class SampleSeedConnector(IDiscoverySource):
    """Built-in connector that yields a small batch of realistic-looking newly-registered Indian businesses (Mumbai/Thane/Navi Mumbai)."""
    name = "sample_seed"
    description = "Built-in synthetic seed of recent Mumbai/Thane/Navi Mumbai businesses for demo + testing."
    configured = True
    requires_config = []

    INDUSTRIES = [
        ("Technology", "SaaS"),
        ("Technology", "E-commerce"),
        ("Technology", "Fintech"),
        ("Logistics", "Last-mile Delivery"),
        ("Healthcare", "Diagnostics"),
        ("Healthcare", "Telemedicine"),
        ("Manufacturing", "Electronics"),
        ("Manufacturing", "Textiles"),
        ("Education", "EdTech"),
        ("Real Estate", "PropTech"),
        ("Hospitality", "Cloud Kitchen"),
        ("Retail", "D2C"),
        ("Media", "Content & Marketing"),
        ("Finance", "NBFC Services"),
    ]
    CITY_PINS = [
        ("Mumbai", "Maharashtra", "Mumbai City", "400001"),
        ("Mumbai", "Maharashtra", "Mumbai City", "400052"),
        ("Mumbai", "Maharashtra", "Mumbai City", "400072"),
        ("Thane", "Maharashtra", "Thane", "400601"),
        ("Thane", "Maharashtra", "Thane", "400607"),
        ("Navi Mumbai", "Maharashtra", "Thane", "400703"),
        ("Navi Mumbai", "Maharashtra", "Thane", "400706"),
        ("Navi Mumbai", "Maharashtra", "Thane", "400614"),
    ]
    COMPANY_TYPES = ["Private Limited", "LLP", "Partnership", "Sole Proprietorship"]
    FIRST_NAMES = ["Aarav", "Vihaan", "Aditya", "Saanvi", "Anaya", "Ishaan", "Priya", "Rohan", "Kabir", "Meera", "Neel", "Diya", "Rishi", "Ananya"]
    LAST_NAMES = ["Sharma", "Patel", "Mehta", "Iyer", "Reddy", "Singh", "Kulkarni", "Joshi", "Nair", "Shah", "Desai", "Verma"]
    PREFIXES = ["Aether", "Zenith", "Nova", "Lumin", "Vyom", "Atrium", "Origin", "Krio", "Pluto", "Halo", "Verve", "Stellar", "Quantum", "Civic"]
    SUFFIXES = ["Labs", "Works", "Networks", "Holdings", "Systems", "Logistics", "Care", "Foods", "Mobility", "Studios", "Capital", "Cloud"]

    async def fetch_businesses(self, limit: int = 10, query: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        out = []
        today = date.today()
        for i in range(limit):
            ind, sub = random.choice(self.INDUSTRIES)
            city, state, district, pincode = random.choice(self.CITY_PINS)
            ctype = random.choice(self.COMPANY_TYPES)
            name = f"{random.choice(self.PREFIXES)}{random.choice(self.SUFFIXES)} {random.choice(['Pvt Ltd','LLP','Solutions','Technologies'])}"
            director = f"{random.choice(self.FIRST_NAMES)} {random.choice(self.LAST_NAMES)}"
            reg = today - timedelta(days=random.randint(0, 21))
            domain = name.lower().replace(' ', '').replace('pvtltd','').replace('llp','').replace('solutions','').replace('technologies','')[:14]
            row = {
                "business_name": name,
                "registration_date": reg,
                "company_type": ctype,
                "category": ind,
                "sub_category": sub,
                "website": f"https://{domain}.in",
                "phone": f"+91-9{random.randint(100000000, 999999999)}",
                "email": f"hello@{domain}.in",
                "linkedin_url": f"https://linkedin.com/company/{domain}",
                "director_name": director,
                "employee_estimate": random.choice([5, 12, 25, 40, 80, 150, 320]),
                "address": f"{random.randint(1,999)}, {random.choice(['Wadala','Andheri','Powai','Vashi','Belapur','Ghatkopar','Worli','Lower Parel'])}",
                "locality": random.choice(["Andheri","Powai","Vashi","Belapur","Ghatkopar","Worli","Lower Parel","Bandra"]),
                "city": city,
                "district": district,
                "state": state,
                "country": "India",
                "pincode": pincode,
                "source": self.name,
                "source_url": "",
            }
            out.append(self.normalize(row))
        return out


async def build_connectors_from_settings(get_setting_async) -> Dict[str, IDiscoverySource]:
    opc_key = await get_setting_async("opencorporates_api_token")
    return {
        "manual": ManualEntryConnector(),
        "csv_upload": CSVUploadConnector(),
        "opencorporates": OpenCorporatesConnector(api_token=opc_key),
        "mca": MCAConnector(),
        "sample_seed": SampleSeedConnector(),
    }
