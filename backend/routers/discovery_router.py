"""Discovery + connectors routes."""
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models import User
from schemas import DiscoveryRunRequest, DiscoveryRunResponse
from deps import require_roles
from audit import write_audit
from discovery import build_connectors_from_settings
from pipeline import ingest_business
from settings_service import get_setting

router = APIRouter(prefix="/discovery", tags=["discovery"])
ANALYST_OR_ADMIN = require_roles(["Admin", "Analyst"])


@router.get("/connectors")
async def list_connectors(_: User = Depends(require_roles(["Admin", "Analyst", "Subscriber"]))):
    connectors = await build_connectors_from_settings(get_setting)
    return [
        {
            "name": c.name,
            "description": c.description,
            "configured": c.configured,
            "requires_config": c.requires_config,
        }
        for c in connectors.values()
    ]


@router.post("/run", response_model=DiscoveryRunResponse)
async def run_discovery(body: DiscoveryRunRequest, request: Request,
                       db: AsyncSession = Depends(get_db), me: User = Depends(ANALYST_OR_ADMIN)):
    connectors = await build_connectors_from_settings(get_setting)
    c = connectors.get(body.source)
    if not c:
        raise HTTPException(400, f"Unknown source: {body.source}")
    if not c.configured:
        raise HTTPException(400, f"Source '{body.source}' is not configured.")
    rows = await c.fetch_businesses(limit=body.limit, query=body.query)
    inserted = 0
    duplicates = 0
    enriched = 0
    errors = []
    for r in rows:
        if not c.validate(r):
            continue
        try:
            biz, created = await ingest_business(db, c.normalize(r), run_ai=True)
            if created:
                inserted += 1
            else:
                duplicates += 1
            if biz.enrichment_status == "enriched":
                enriched += 1
        except Exception as e:
            errors.append(str(e)[:200])
    await write_audit(db, user_id=me.id, user_email=me.email, action="discovery_run",
                      entity_type="discovery", entity_id=body.source,
                      after_value={"fetched": len(rows), "inserted": inserted, "duplicates": duplicates, "enriched": enriched},
                      ip_address=request.client.host if request.client else None,
                      user_agent=request.headers.get("user-agent"))
    return DiscoveryRunResponse(source=body.source, fetched=len(rows), inserted=inserted,
                                duplicates=duplicates, enriched=enriched, errors=errors)
