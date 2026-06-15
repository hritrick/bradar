"""AI service: enrichment + prediction + scoring via optional hosted LLM integration.

All outbound LLM calls are retried with exponential backoff on transient errors.
"""
import json
import logging
import os
import uuid
from typing import Optional
from dotenv import load_dotenv
from pathlib import Path
import httpx
import asyncio
from retry_util import retry_async

try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
except ImportError:
    LlmChat = None
    UserMessage = None

load_dotenv(Path(__file__).parent / ".env")
LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
log = logging.getLogger(__name__)

LLM_RETRYABLE = (
    asyncio.TimeoutError,
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    httpx.ReadTimeout,
    ConnectionError,
)


@retry_async(max_attempts=3, base_delay=0.7, max_delay=6.0, retryable=LLM_RETRYABLE)
async def _llm_call(system: str, user: str) -> str:
    if not LlmChat or not UserMessage or not LLM_KEY:
        raise RuntimeError("Hosted LLM integration is not configured")
    session_id = f"radar-{uuid.uuid4()}"
    chat = (
        LlmChat(api_key=LLM_KEY, session_id=session_id, system_message=system)
        .with_model(LLM_PROVIDER, LLM_MODEL)
    )
    return await chat.send_message(UserMessage(text=user + "\n\nRespond with ONLY a valid JSON object. No prose, no markdown fences."))


async def _llm_json(system: str, user: str) -> dict:
    raw = await _llm_call(system, user)
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON found in LLM response: {raw[:200]}")
    return json.loads(text[start : end + 1])


async def enrich_business(b: dict) -> dict:
    if not LLM_KEY or not LlmChat:
        return {
            "category": b.get("category") or b.get("industry") or "General Services",
            "sub_category": b.get("sub_category") or "Unclassified",
            "company_type": b.get("company_type") or "Private Limited",
            "employee_estimate": int(b.get("employee_estimate") or 10),
            "confidence_score": float(b.get("confidence_score") or 0.35),
        }
    system = (
        "You are an expert business data enrichment analyst for the Indian B2B market. "
        "Given partial business data, infer realistic missing fields without hallucinating proprietary data. "
        "Be conservative with employee counts."
    )
    user = (
        "Enrich the business below. Output strict JSON with these EXACT keys: "
        "category (string), sub_category (string), company_type (string e.g. 'Private Limited' / 'LLP' / 'Sole Proprietorship' / 'Partnership'), "
        "employee_estimate (integer 1-10000), confidence_score (float 0..1). "
        f"\nBusiness data: {json.dumps(b, default=str)}"
    )
    return await _llm_json(system, user)


async def predict_needs(b: dict) -> dict:
    if not LLM_KEY or not LlmChat:
        industry = (b.get("industry") or "").lower()
        predicted_need = "Digital Marketing"
        if "manufact" in industry:
            predicted_need = "ERP Software"
        elif "logistic" in industry:
            predicted_need = "Logistics Tech"
        elif "health" in industry:
            predicted_need = "Compliance"
        elif "real estate" in industry:
            predicted_need = "Legal & Trademark"
        return {
            "predicted_need": predicted_need,
            "probability": 0.58,
            "reasoning": "Local fallback prediction used because hosted LLM credentials are not configured.",
        }
    system = (
        "You are a B2B service-needs prediction expert focused on Indian companies. "
        "Based on a business profile (industry, recency, size), pick the SINGLE most likely service need they will require in the next 6 months."
    )
    user = (
        "Output strict JSON with EXACT keys: "
        "predicted_need (string short label, e.g. 'Accounting & Compliance', 'Digital Marketing', 'GST Registration', 'Logistics Tech', 'HR & Payroll', 'Cloud Hosting', 'Legal & Trademark', 'Office Lease', 'IT Infrastructure', 'Branding & Web'), "
        "probability (float 0..1), "
        "reasoning (string 1-2 sentences). "
        f"\nBusiness: {json.dumps(b, default=str)}"
    )
    return await _llm_json(system, user)


async def score_lead(b: dict) -> dict:
    if not LLM_KEY or not LlmChat:
        size = int(b.get("employee_estimate") or 0)
        completeness = sum(1 for key in ("phone", "email", "website", "city", "industry") if b.get(key))
        score = min(95, 35 + min(size, 40) + completeness * 5)
        return {
            "score": score,
            "lead_category": "HOT" if score >= 75 else "WARM" if score >= 50 else "COLD",
            "scoring_reason": "Local fallback scoring used because hosted LLM credentials are not configured.",
        }
    system = (
        "You are a lead quality scoring expert for Indian B2B service providers. "
        "Score the lead 0-100 considering: size signals, data completeness, recency, category attractiveness for outbound, and contactability."
    )
    user = (
        "Output strict JSON with EXACT keys: "
        "score (integer 0..100), "
        "lead_category (string: 'HOT' if score>=75 else 'WARM' if score>=50 else 'COLD'), "
        "scoring_reason (string 1-2 sentences). "
        f"\nBusiness: {json.dumps(b, default=str)}"
    )
    return await _llm_json(system, user)


async def run_full_ai_pipeline(b: dict) -> dict:
    result = {"enrich": None, "predict": None, "score": None, "errors": []}
    try:
        result["enrich"] = await enrich_business(b)
    except Exception as e:
        log.warning(f"enrich failed: {e}")
        result["errors"].append(f"enrich: {e}")
    merged = {**b, **(result["enrich"] or {})}
    try:
        result["predict"] = await predict_needs(merged)
    except Exception as e:
        log.warning(f"predict failed: {e}")
        result["errors"].append(f"predict: {e}")
    try:
        result["score"] = await score_lead(merged)
    except Exception as e:
        log.warning(f"score failed: {e}")
        result["errors"].append(f"score: {e}")
    return result
