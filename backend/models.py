"""SQLAlchemy models for Business Radar AI."""
import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Date, Text, ForeignKey, Boolean, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(120), nullable=False)
    email = Column(String(160), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=True)
    oauth_provider = Column(String(40), nullable=True)
    oauth_provider_id = Column(String(200), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    role = Column(String(20), nullable=False, default="Subscriber")
    status = Column(String(20), nullable=False, default="Active")
    force_password_reset = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Business(Base):
    __tablename__ = "businesses"
    id = Column(String, primary_key=True, default=gen_uuid)
    business_name = Column(String(255), nullable=False, index=True)
    gst_number = Column(String(20), nullable=True, index=True)
    registration_date = Column(Date, nullable=True, index=True)
    company_type = Column(String(80))
    industry = Column(String(80), index=True)
    category = Column(String(120), index=True)
    sub_category = Column(String(120))
    website = Column(String(255), index=True)
    phone = Column(String(40), index=True)
    email = Column(String(160), index=True)
    linkedin_url = Column(String(300))
    director_name = Column(String(200))
    employee_estimate = Column(Integer)
    address = Column(Text)
    locality = Column(String(120), index=True)
    city = Column(String(80), index=True)
    district = Column(String(80))
    state = Column(String(80), index=True)
    country = Column(String(80), default="India")
    pincode = Column(String(15), index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    source = Column(String(80), index=True)
    source_url = Column(String(500))
    confidence_score = Column(Float, default=0.5)
    enrichment_status = Column(String(20), default="pending", index=True)  # pending / queued / enriched / failed
    extra = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    predictions = relationship("Prediction", back_populates="business", cascade="all, delete-orphan")
    lead_scores = relationship("LeadScore", back_populates="business", cascade="all, delete-orphan")


Index("ix_businesses_name_pincode", Business.business_name, Business.pincode)
Index("ix_businesses_industry_city", Business.industry, Business.city)


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(String, primary_key=True, default=gen_uuid)
    business_id = Column(String, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    predicted_need = Column(String(160), index=True)
    probability = Column(Float)
    reasoning = Column(Text)
    model_used = Column(String(80))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    business = relationship("Business", back_populates="predictions")


class LeadScore(Base):
    __tablename__ = "lead_scores"
    id = Column(String, primary_key=True, default=gen_uuid)
    business_id = Column(String, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Integer, index=True)
    lead_category = Column(String(20), index=True)
    scoring_reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    business = relationship("Business", back_populates="lead_scores")


class DailyReport(Base):
    __tablename__ = "daily_reports"
    id = Column(String, primary_key=True, default=gen_uuid)
    report_date = Column(Date, nullable=False, unique=True, index=True)
    report_json = Column(JSONB, default=dict)
    report_pdf = Column(String(500), nullable=True)
    filters_applied = Column(JSONB, default=dict)
    generated_by = Column(String(120), default="system")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Settings(Base):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(80), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=True)
    is_secret = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    user_email = Column(String(160), nullable=True)
    action = Column(String(80), nullable=False, index=True)
    entity_type = Column(String(60), index=True)
    entity_id = Column(String, index=True, nullable=True)
    before_value = Column(JSONB, nullable=True)
    after_value = Column(JSONB, nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class UserPreference(Base):
    __tablename__ = "user_preferences"
    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    daily_report_enabled = Column(Boolean, default=True)
    weekly_report_enabled = Column(Boolean, default=False)
    delivery_email = Column(String(160), nullable=True)
    filters_default = Column(JSONB, default=dict)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SavedSearch(Base):
    __tablename__ = "saved_searches"
    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    filter_json = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class SchedulerJobRun(Base):
    __tablename__ = "scheduler_runs"
    id = Column(String, primary_key=True, default=gen_uuid)
    job_name = Column(String(80), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(30), default="running")
    message = Column(Text, nullable=True)


class DiscoverySource(Base):
    __tablename__ = "discovery_sources"
    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String(80), nullable=False, unique=True, index=True)
    display_name = Column(String(120), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True, nullable=False)
    requires_config = Column(JSONB, default=list)
    schedule_cron = Column(String(40), nullable=True)  # e.g. "0 6 * * *"
    config = Column(JSONB, default=dict)
    last_run_at = Column(DateTime, nullable=True)
    last_run_status = Column(String(30), nullable=True)
    last_run_summary = Column(JSONB, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    runs = relationship("DiscoverySourceRun", back_populates="source", cascade="all, delete-orphan")


class DiscoverySourceRun(Base):
    __tablename__ = "discovery_source_runs"
    id = Column(String, primary_key=True, default=gen_uuid)
    source_id = Column(String, ForeignKey("discovery_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    source_name = Column(String(80), index=True)
    triggered_by = Column(String(160), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(30), default="running")  # running / success / failed
    records_found = Column(Integer, default=0)
    records_added = Column(Integer, default=0)
    duplicates_removed = Column(Integer, default=0)
    invalid_records = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    enrichment_queued = Column(Integer, default=0)
    errors = Column(JSONB, default=list)
    message = Column(Text, nullable=True)

    source = relationship("DiscoverySource", back_populates="runs")


class EnrichmentQueueItem(Base):
    __tablename__ = "enrichment_queue"
    id = Column(String, primary_key=True, default=gen_uuid)
    business_id = Column(String, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)
    status = Column(String(20), default="queued", nullable=False, index=True)  # queued / processing / done / failed
    attempts = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    queued_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
