"""Pydantic schemas (request/response)."""
from datetime import date, datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    force_password_reset: bool = False
    user: "UserOut"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserCreateRequest(BaseModel):
    name: str
    email: EmailStr
    password: Optional[str] = None
    role: str = "Subscriber"


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class PasswordResetRequest(BaseModel):
    current_password: str
    new_password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    email: str
    role: str
    status: str
    avatar_url: Optional[str] = None
    force_password_reset: bool = False
    last_login_at: Optional[datetime] = None
    created_at: datetime


class BusinessBase(BaseModel):
    business_name: str
    registration_date: Optional[date] = None
    company_type: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    director_name: Optional[str] = None
    employee_estimate: Optional[int] = None
    address: Optional[str] = None
    locality: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "India"
    pincode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: Optional[str] = "manual"
    source_url: Optional[str] = None


class BusinessCreate(BusinessBase):
    pass


class BusinessUpdate(BaseModel):
    business_name: Optional[str] = None
    company_type: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    director_name: Optional[str] = None
    employee_estimate: Optional[int] = None
    address: Optional[str] = None
    locality: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    predicted_need: Optional[str]
    probability: Optional[float]
    reasoning: Optional[str]
    model_used: Optional[str]
    created_at: datetime


class LeadScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    score: Optional[int]
    lead_category: Optional[str]
    scoring_reason: Optional[str]
    created_at: datetime


class BusinessOut(BusinessBase):
    model_config = ConfigDict(from_attributes=True)
    id: str
    confidence_score: Optional[float] = None
    enrichment_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    predictions: List[PredictionOut] = []
    lead_scores: List[LeadScoreOut] = []


class BusinessListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    business_name: str
    city: Optional[str] = None
    state: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    registration_date: Optional[date] = None
    pincode: Optional[str] = None
    director_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    source: Optional[str] = None
    enrichment_status: Optional[str] = None
    confidence_score: Optional[float] = None
    latest_score: Optional[int] = None
    latest_lead_category: Optional[str] = None
    latest_predicted_need: Optional[str] = None
    created_at: datetime


class BusinessListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[BusinessListItem]


class FilterParams(BaseModel):
    search: Optional[str] = None
    city: Optional[List[str]] = None
    state: Optional[List[str]] = None
    category: Optional[List[str]] = None
    pincode: Optional[str] = None
    predicted_need: Optional[List[str]] = None
    lead_category: Optional[List[str]] = None
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    registered_after: Optional[date] = None
    registered_before: Optional[date] = None
    source: Optional[List[str]] = None
    page: int = 1
    page_size: int = 25
    sort: Optional[str] = "created_at"  # field name optionally prefixed by '-' for desc


class SettingItem(BaseModel):
    key: str
    value: Optional[str] = None
    is_secret: bool = False


class SettingsUpdate(BaseModel):
    settings: Dict[str, Optional[str]]


class DailyReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    report_date: date
    report_json: Dict[str, Any]
    generated_by: Optional[str]
    created_at: datetime


class DailyReportListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    report_date: date
    generated_by: Optional[str]
    created_at: datetime


class GenerateReportRequest(BaseModel):
    report_date: Optional[date] = None
    filters: Optional[Dict[str, Any]] = None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_email: Optional[str]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    before_value: Optional[Dict[str, Any]] = None
    after_value: Optional[Dict[str, Any]] = None
    ip_address: Optional[str]
    created_at: datetime


class UserPreferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    daily_report_enabled: bool
    weekly_report_enabled: bool
    delivery_email: Optional[str]
    filters_default: Optional[Dict[str, Any]] = None


class UserPreferenceUpdate(BaseModel):
    daily_report_enabled: Optional[bool] = None
    weekly_report_enabled: Optional[bool] = None
    delivery_email: Optional[str] = None
    filters_default: Optional[Dict[str, Any]] = None


class DiscoveryRunRequest(BaseModel):
    source: str  # opencorporates / mca / sample
    limit: int = 10
    query: Optional[Dict[str, Any]] = None


class DiscoveryRunResponse(BaseModel):
    source: str
    fetched: int
    inserted: int
    duplicates: int
    enriched: int
    errors: List[str] = []


Token.model_rebuild()
