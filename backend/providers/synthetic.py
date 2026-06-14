"""Synthetic provider — always-on built-in source that generates realistic Mumbai/Thane/Navi Mumbai businesses."""
import random
import string
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from .base import BusinessDiscoveryProvider

INDUSTRIES = [
    "Real Estate", "Manufacturing", "Logistics", "Retail", "IT Services", "Healthcare",
]

SUB_CATEGORIES = {
    "Real Estate": ["Residential Development", "Commercial Leasing", "PropTech", "Brokerage", "Co-working"],
    "Manufacturing": ["Electronics", "Textiles", "Pharma", "Engineering Goods", "FMCG"],
    "Logistics": ["Last-Mile Delivery", "Freight Forwarding", "Warehousing", "3PL", "Cold Chain"],
    "Retail": ["D2C", "Apparel", "Grocery", "Electronics Retail", "Beauty & Wellness"],
    "IT Services": ["SaaS", "Custom Software", "Cloud Hosting", "Cybersecurity", "AI/ML"],
    "Healthcare": ["Diagnostics", "Telemedicine", "Clinics", "Pharma Retail", "MedTech"],
}

INDUSTRY_PREFIXES = {
    "Real Estate": ["Habitat", "Skyline", "Urban", "Trinity", "Prime", "Aether", "Stellar", "Civic"],
    "Manufacturing": ["Krio", "Nova", "Verve", "Atrium", "Origin", "Pluto", "Lumin", "Vyom"],
    "Logistics": ["Swift", "Aether", "Halo", "Cargo", "Origin", "Zenith", "Stellar", "Quantum"],
    "Retail": ["Nova", "Verve", "Lumin", "Halo", "Civic", "Prime", "Krio", "Origin"],
    "IT Services": ["Aether", "Nova", "Zenith", "Lumin", "Krio", "Quantum", "Vyom", "Origin"],
    "Healthcare": ["Halo", "Pluto", "Civic", "Aether", "Prime", "Lumin", "Trinity", "Stellar"],
}

INDUSTRY_SUFFIXES = {
    "Real Estate": ["Realty", "Estates", "Holdings", "Properties", "Developers"],
    "Manufacturing": ["Industries", "Works", "Manufacturing", "Mfg", "Engineering"],
    "Logistics": ["Logistics", "Cargo", "Movers", "Express", "Transport"],
    "Retail": ["Retail", "Stores", "Mart", "Bazaar", "Foods"],
    "IT Services": ["Technologies", "Systems", "Software", "Labs", "Cloud"],
    "Healthcare": ["Healthcare", "Medical", "Care", "Clinic", "Diagnostics"],
}

COMPANY_TYPES = ["Private Limited", "LLP", "Partnership", "Sole Proprietorship", "OPC"]
COMPANY_TYPE_WEIGHTS = [0.55, 0.18, 0.12, 0.10, 0.05]

CITY_PINS = {
    "Mumbai": [
        ("Mumbai City", "Mumbai City", "400001", 18.9388, 72.8354),
        ("Mumbai City", "Mumbai City", "400052", 19.0596, 72.8295),
        ("Mumbai Suburban", "Mumbai Suburban", "400072", 19.1136, 72.8697),
        ("Mumbai Suburban", "Mumbai Suburban", "400049", 19.1197, 72.8298),
        ("Mumbai Suburban", "Mumbai Suburban", "400070", 19.0728, 72.8826),
        ("Mumbai Suburban", "Mumbai Suburban", "400025", 19.0050, 72.8290),
        ("Mumbai Suburban", "Mumbai Suburban", "400013", 18.9956, 72.8302),
    ],
    "Thane": [
        ("Thane", "Thane", "400601", 19.2183, 72.9781),
        ("Thane", "Thane", "400607", 19.1972, 72.9722),
        ("Thane", "Thane", "400606", 19.2426, 72.9783),
        ("Thane", "Thane", "400612", 19.2543, 72.9819),
    ],
    "Navi Mumbai": [
        ("Thane", "Thane", "400703", 19.0760, 73.0157),
        ("Thane", "Thane", "400706", 19.0330, 73.0297),
        ("Thane", "Thane", "400614", 19.0411, 73.0282),
        ("Raigad", "Raigad", "410210", 19.0176, 73.1224),
    ],
}
CITY_WEIGHTS = {"Mumbai": 0.50, "Thane": 0.25, "Navi Mumbai": 0.25}

LOCALITIES = ["Andheri", "Powai", "Vashi", "Belapur", "Ghatkopar", "Worli", "Lower Parel", "Bandra",
              "Borivali", "Wadala", "Goregaon", "Hiranandani", "Kalyan", "Mulund", "Vikhroli"]
FIRST_NAMES = ["Aarav", "Vihaan", "Aditya", "Saanvi", "Anaya", "Ishaan", "Priya", "Rohan", "Kabir",
               "Meera", "Neel", "Diya", "Rishi", "Ananya", "Aanya", "Krish", "Tanvi", "Yash"]
LAST_NAMES = ["Sharma", "Patel", "Mehta", "Iyer", "Reddy", "Singh", "Kulkarni", "Joshi",
              "Nair", "Shah", "Desai", "Verma", "Bose", "Khanna", "Chopra", "Saxena"]

PAN_LETTERS = string.ascii_uppercase


def _generate_gst(state_code: str = "27") -> str:
    pan_first = ''.join(random.choices(PAN_LETTERS, k=5))
    pan_digits = ''.join(random.choices(string.digits, k=4))
    pan_check = random.choice(PAN_LETTERS)
    pan = f"{pan_first}{pan_digits}{pan_check}"
    entity_num = random.choice(string.digits)
    return f"{state_code}{pan}{entity_num}Z{random.choice(string.ascii_uppercase + string.digits)}"


def _weighted_choice(weights: Dict[str, float]) -> str:
    keys = list(weights.keys())
    vals = [weights[k] for k in keys]
    return random.choices(keys, weights=vals, k=1)[0]


def _generate_one(industry: Optional[str] = None, today: Optional[date] = None) -> Dict[str, Any]:
    industry = industry or random.choice(INDUSTRIES)
    sub = random.choice(SUB_CATEGORIES[industry])
    prefix = random.choice(INDUSTRY_PREFIXES[industry])
    suffix = random.choice(INDUSTRY_SUFFIXES[industry])
    name = f"{prefix}{suffix} {random.choice(['Pvt Ltd', 'LLP', 'Solutions', 'Group', 'Holdings'])}"
    company_type = random.choices(COMPANY_TYPES, weights=COMPANY_TYPE_WEIGHTS, k=1)[0]

    city = _weighted_choice(CITY_WEIGHTS)
    district, district2, pincode, lat, lng = random.choice(CITY_PINS[city])
    # jitter lat/lng slightly
    lat += random.uniform(-0.01, 0.01)
    lng += random.uniform(-0.01, 0.01)

    director = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    domain_root = (prefix + suffix).lower().replace(" ", "")
    domain = f"{domain_root}{random.randint(0, 99)}".strip()
    today = today or date.today()
    reg_age = random.randint(0, 90)
    reg_date = today - timedelta(days=reg_age)

    return {
        "business_name": name,
        "gst_number": _generate_gst(),
        "registration_date": reg_date,
        "company_type": company_type,
        "industry": industry,
        "category": industry,
        "sub_category": sub,
        "website": f"https://{domain}.in",
        "phone": f"+91-9{random.randint(100000000, 999999999)}",
        "email": f"hello@{domain}.in",
        "linkedin_url": f"https://linkedin.com/company/{domain}",
        "director_name": director,
        "employee_estimate": random.choices([5, 12, 25, 40, 80, 150, 320, 600], weights=[20, 25, 20, 15, 10, 5, 3, 2], k=1)[0],
        "address": f"{random.randint(1, 999)}, {random.choice(LOCALITIES)}",
        "locality": random.choice(LOCALITIES),
        "city": city,
        "district": district,
        "state": "Maharashtra",
        "country": "India",
        "pincode": pincode,
        "latitude": round(lat, 6),
        "longitude": round(lng, 6),
        "source": "synthetic",
        "source_url": "",
        "confidence_score": round(random.uniform(0.55, 0.92), 2),
    }


class SyntheticProvider(BusinessDiscoveryProvider):
    """Always configured. Generates realistic India-Maharashtra businesses for demo/testing."""

    name = "synthetic"
    display_name = "Synthetic Generator"
    description = "Built-in demo source. Generates realistic Mumbai/Thane/Navi Mumbai businesses across 6 industries. Safe to disable in production."
    requires_config = []
    supports_scheduling = True
    supports_run_now = True

    async def discover_businesses(self, limit: int = 10, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        industry = (query or {}).get("industry")
        out = []
        for _ in range(limit):
            out.append(_generate_one(industry=industry if industry in INDUSTRIES else None))
        return out

    def normalize_data(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        # Synthetic rows are already in standard schema.
        raw["source"] = self.name
        return raw


def generate_synthetic_batch(n: int, today: Optional[date] = None) -> List[Dict[str, Any]]:
    """Standalone helper used by the 10k seeder — returns already-normalized rows."""
    return [_generate_one(today=today) for _ in range(n)]
