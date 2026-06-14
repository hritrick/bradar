"""Startup configuration validation — fail-fast on insecure prod settings."""
import logging
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
log = logging.getLogger(__name__)

WEAK_JWT_SECRETS = {
    "", "change-me", "secret", "changeme",
    "business-radar-ai-secret-change-in-prod-2025",
}


class InsecureConfigError(RuntimeError):
    """Raised at startup if the configuration would be unsafe in production."""


def validate_config() -> dict:
    """Returns a dict summarising effective config; raises InsecureConfigError when prod + unsafe."""
    app_env = (os.environ.get("APP_ENV") or "development").lower()
    jwt_secret = os.environ.get("JWT_SECRET") or ""
    cors = os.environ.get("CORS_ORIGINS") or ""
    cors_list = [o.strip() for o in cors.split(",") if o.strip()]

    issues = []

    # JWT secret validation
    if jwt_secret in WEAK_JWT_SECRETS:
        issues.append("JWT_SECRET is empty or matches a well-known/default value.")
    if len(jwt_secret) < 32:
        issues.append(f"JWT_SECRET is too short ({len(jwt_secret)} chars). Require >=32.")

    # CORS validation
    if "*" in cors_list and (os.environ.get("ALLOW_CREDENTIALS", "true").lower() == "true"):
        issues.append("CORS_ORIGINS='*' combined with credentialed requests is unsafe.")
    if app_env == "production" and (not cors_list or "*" in cors_list):
        issues.append("CORS_ORIGINS must be an explicit allow-list in production.")

    # Database
    if not (os.environ.get("DATABASE_URL") or "").strip():
        issues.append("DATABASE_URL is missing.")

    if issues:
        msg = "Configuration issues detected:\n  - " + "\n  - ".join(issues)
        if app_env == "production":
            raise InsecureConfigError(msg)
        log.warning("[non-prod] %s", msg)

    summary = {
        "app_env": app_env,
        "jwt_secret_len": len(jwt_secret),
        "cors_origins": cors_list,
        "storage_provider": (os.environ.get("STORAGE_PROVIDER") or "local").lower(),
        "login_rate_per_min": int(os.environ.get("LOGIN_RATE_LIMIT_PER_MIN") or 10),
        "login_rate_burst": int(os.environ.get("LOGIN_RATE_LIMIT_BURST") or 5),
    }
    log.info("Config summary: %s", summary)
    return summary


def suggest_jwt_secret() -> str:
    """Helper for ops to generate a strong replacement."""
    return secrets.token_urlsafe(48)
