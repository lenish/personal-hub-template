"""Health data API routes — Whoop + Apple Health + Withings."""

import logging
import secrets
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.collectors.apple_health import AppleHealthCollector
from api.config import settings
from api.database import get_db
from api.models import DataItem, SyncState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["health"])

apple_health_collector = AppleHealthCollector()

WHOOP_SCOPES = "offline read:recovery read:cycles read:sleep read:workout read:profile read:body_measurement"
WITHINGS_SCOPES = "user.metrics,user.activity"


def _verify_health_token(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = auth[7:]
    if not settings.health_api_token or not secrets.compare_digest(token, settings.health_api_token):
        raise HTTPException(status_code=401, detail="Invalid token")


# ── Health Summary ────────────────────────────────────────────────


@router.get("/summary")
async def health_summary(
    days: int = Query(default=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get health summary for the last N days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(DataItem)
        .where(DataItem.category == "health", DataItem.created_at >= since)
        .order_by(DataItem.created_at.desc())
    )
    items = result.scalars().all()

    grouped: dict[str, list] = {}
    for item in items:
        grouped.setdefault(item.item_type, []).append({
            "date": item.created_at.isoformat(),
            "title": item.title,
            **item.metadata_,
        })

    return {"days": days, "data": grouped, "total_items": len(items)}


# ── Source-specific endpoints ─────────────────────────────────────


@router.get("/whoop")
async def whoop_data(
    item_type: str = Query(default=None, description="recovery, sleep, or workout"),
    days: int = Query(default=25, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get Whoop data."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(DataItem).where(
        DataItem.source == "whoop",
        DataItem.created_at >= since,
    )
    if item_type:
        query = query.where(DataItem.item_type == item_type)
    query = query.order_by(DataItem.created_at.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "source": "whoop",
        "count": len(items),
        "data": [
            {
                "id": str(item.id),
                "type": item.item_type,
                "date": item.created_at.isoformat(),
                "title": item.title,
                **item.metadata_,
            }
            for item in items
        ],
    }


@router.get("/apple")
async def apple_health_data(
    metric: str = Query(default=None, description="Metric name like step_count, heart_rate"),
    days: int = Query(default=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get Apple Health data."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(DataItem).where(
        DataItem.source == "apple_health",
        DataItem.created_at >= since,
    )
    if metric:
        query = query.where(DataItem.item_type == metric)
    query = query.order_by(DataItem.created_at.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "source": "apple_health",
        "count": len(items),
        "data": [
            {
                "id": str(item.id),
                "type": item.item_type,
                "date": item.created_at.isoformat(),
                "title": item.title,
                **item.metadata_,
            }
            for item in items
        ],
    }


@router.get("/withings")
async def withings_data(
    item_type: str = Query(default=None, description="body_composition, blood_pressure, or sleep"),
    days: int = Query(default=30, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get Withings data."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(DataItem).where(
        DataItem.source == "withings",
        DataItem.created_at >= since,
    )
    if item_type:
        query = query.where(DataItem.item_type == item_type)
    query = query.order_by(DataItem.created_at.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "source": "withings",
        "count": len(items),
        "data": [
            {
                "id": str(item.id),
                "type": item.item_type,
                "date": item.created_at.isoformat(),
                "title": item.title,
                **{k: v for k, v in item.metadata_.items() if k != "raw"},
            }
            for item in items
        ],
    }


# ── Apple Health Webhook ──────────────────────────────────────────


@router.post("/webhook")
async def receive_health_data(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive Apple Health data from Health Auto Export app."""
    _verify_health_token(request)

    payload = await request.json()
    if not payload or "data" not in payload:
        raise HTTPException(status_code=400, detail="No health data in payload")

    count = await apple_health_collector.process_webhook(db, payload)

    metrics_count = len(payload.get("data", {}).get("metrics", []))
    workouts_count = len(payload.get("data", {}).get("workouts", []))

    return {
        "success": True,
        "message": f"Processed {count} data items",
        "metrics_count": metrics_count,
        "workouts_count": workouts_count,
        "items_stored": count,
    }


# ── Whoop OAuth ───────────────────────────────────────────────────


@router.get("/whoop/authorize")
async def whoop_authorize():
    """Redirect to Whoop OAuth login."""
    state = secrets.token_urlsafe(16)
    params = urllib.parse.urlencode({
        "client_id": settings.whoop_client_id,
        "response_type": "code",
        "redirect_uri": settings.whoop_redirect_uri,
        "scope": WHOOP_SCOPES,
        "state": state,
    })
    return RedirectResponse(f"https://api.prod.whoop.com/oauth/oauth2/auth?{params}")


@router.get("/whoop/callback")
async def whoop_callback(
    code: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Exchange Whoop OAuth code for token, store in sync_state."""
    if error:
        raise HTTPException(status_code=400, detail=f"Whoop OAuth error: {error} - {error_description}")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.prod.whoop.com/oauth/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.whoop_client_id,
                "client_secret": settings.whoop_client_secret,
                "redirect_uri": settings.whoop_redirect_uri,
            },
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Whoop token exchange failed: {resp.text}")

    token_data = resp.json()
    token_data["_obtained_at"] = time.time()

    stmt = pg_insert(SyncState).values(source="whoop", cursor=token_data, status="idle")
    stmt = stmt.on_conflict_do_update(index_elements=["source"], set_={"cursor": token_data, "status": "idle"})
    await db.execute(stmt)
    await db.commit()

    return {"success": True, "message": "Whoop OAuth connected", "scopes": token_data.get("scope")}


# ── Withings OAuth ────────────────────────────────────────────────


@router.get("/withings/authorize")
async def withings_authorize():
    """Redirect to Withings OAuth login."""
    state = secrets.token_urlsafe(16)
    params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": settings.withings_client_id,
        "redirect_uri": settings.withings_redirect_uri,
        "scope": WITHINGS_SCOPES,
        "state": state,
    })
    return RedirectResponse(f"https://account.withings.com/oauth2_user/authorize2?{params}")


@router.get("/withings/callback")
async def withings_callback(
    code: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Exchange Withings OAuth code for token, store in sync_state."""
    if error:
        raise HTTPException(status_code=400, detail=f"Withings OAuth error: {error}")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://wbsapi.withings.net/v2/oauth2",
            data={
                "action": "requesttoken",
                "grant_type": "authorization_code",
                "client_id": settings.withings_client_id,
                "client_secret": settings.withings_client_secret,
                "code": code,
                "redirect_uri": settings.withings_redirect_uri,
            },
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Withings token exchange HTTP error: {resp.status_code}")

    data = resp.json()
    if data.get("status") != 0:
        raise HTTPException(status_code=502, detail=f"Withings token exchange failed: {data}")

    token_data = data.get("body", {})
    token_data["_obtained_at"] = time.time()

    stmt = pg_insert(SyncState).values(source="withings", cursor=token_data, status="idle")
    stmt = stmt.on_conflict_do_update(index_elements=["source"], set_={"cursor": token_data, "status": "idle"})
    await db.execute(stmt)
    await db.commit()

    return {"success": True, "message": "Withings OAuth connected", "userid": token_data.get("userid")}


# ── Sync Status ───────────────────────────────────────────────────


@router.get("/sync-status")
async def sync_status(db: AsyncSession = Depends(get_db)):
    """Get sync status for all health sources."""
    result = await db.execute(
        select(SyncState).where(SyncState.source.in_(["whoop", "apple_health", "withings"]))
    )
    states = result.scalars().all()

    return {
        source.source: {
            "last_sync": source.last_sync_at.isoformat() if source.last_sync_at else None,
            "status": source.status,
            "items_synced": source.items_synced,
            "error": source.error_message,
        }
        for source in states
    }
