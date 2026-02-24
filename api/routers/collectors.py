"""Data collectors API — Google OAuth (multi-account), Spotify OAuth, and generic data queries."""

import base64
import json
import logging
import secrets
import time
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import Integer, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.collectors.google_auth import GOOGLE_SOURCE_PREFIX, list_google_accounts, save_google_token
from api.collectors.tldv import TldvCollector
from api.config import settings
from api.database import get_db
from api.models import DataItem, SyncState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/collectors", tags=["collectors"])

GOOGLE_SCOPES = " ".join([
    "https://www.googleapis.com/auth/calendar.readonly",
])

ALL_SOURCES = ["google_calendar", "spotify", "tldv"]


# ── Google OAuth ──────────────────────────────────────────────────


@router.get("/google/authorize")
async def google_authorize(
    account: str = Query(description="Account key, e.g. 'personal' or 'work'"),
    login_hint: str = Query(default=None, description="Email hint for Google login"),
):
    """Redirect to Google OAuth consent screen for a specific account."""
    state_data = json.dumps({"nonce": secrets.token_urlsafe(16), "account": account})
    params: dict[str, str] = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": GOOGLE_SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": state_data,
    }
    if login_hint:
        params["login_hint"] = login_hint
    return RedirectResponse(
        f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    )


@router.get("/google/callback")
async def google_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Exchange Google OAuth code for tokens, store in sync_state per account."""
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")

    # Extract account from state
    account = "default"
    if state:
        try:
            state_data = json.loads(state)
            account = state_data.get("account", "default")
        except (json.JSONDecodeError, TypeError):
            pass

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
            },
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Google token exchange failed: {resp.text[:300]}",
        )

    token_data = resp.json()
    token_data["_obtained_at"] = time.time()
    token_data["_account"] = account

    await save_google_token(db, token_data, account)

    return {
        "success": True,
        "message": f"Google OAuth connected for '{account}'",
        "account": account,
        "scopes": token_data.get("scope"),
    }


@router.get("/google/accounts")
async def google_accounts(db: AsyncSession = Depends(get_db)):
    """List registered Google accounts."""
    accounts = await list_google_accounts(db)
    return {"accounts": accounts}


# ── Spotify OAuth ─────────────────────────────────────────────────


SPOTIFY_SCOPES = "user-read-recently-played user-top-read user-read-currently-playing user-library-read playlist-read-private playlist-read-collaborative"


@router.get("/spotify/authorize")
async def spotify_authorize():
    """Redirect to Spotify OAuth consent screen."""
    if not settings.spotify_client_id:
        raise HTTPException(status_code=500, detail="Spotify client ID not configured")

    state = secrets.token_urlsafe(16)
    params = urllib.parse.urlencode({
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "scope": SPOTIFY_SCOPES,
        "state": state,
    })
    return RedirectResponse(f"https://accounts.spotify.com/authorize?{params}")


@router.get("/spotify/callback")
async def spotify_callback(
    code: str | None = None,
    error: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Exchange Spotify OAuth code for tokens."""
    if error:
        raise HTTPException(status_code=400, detail=f"Spotify OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    creds = f"{settings.spotify_client_id}:{settings.spotify_client_secret}"
    basic_auth = "Basic " + base64.b64encode(creds.encode()).decode()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://accounts.spotify.com/api/token",
            headers={
                "Authorization": basic_auth,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.spotify_redirect_uri,
            },
        )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Spotify token exchange failed: {resp.text[:300]}",
        )

    token_data = resp.json()
    token_data["_obtained_at"] = time.time()

    now = datetime.now(timezone.utc)
    stmt = pg_insert(SyncState).values(
        source="spotify", last_sync_at=now, status="idle",
        cursor=token_data, items_synced=0,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["source"],
        set_={"cursor": token_data, "last_sync_at": now, "status": "idle"},
    )
    await db.execute(stmt)
    await db.commit()

    return {
        "success": True,
        "message": "Spotify connected",
        "scopes": token_data.get("scope"),
    }


# ── Spotify Data ──────────────────────────────────────────────────


@router.get("/spotify/playlists/{playlist_id}/tracks")
async def spotify_playlist_tracks(
    playlist_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get all tracks for a specific Spotify playlist."""
    query = select(DataItem).where(
        DataItem.source == "spotify",
        DataItem.item_type == "playlist_track",
        DataItem.metadata_.op("->>")(
            "playlist_id"
        ) == playlist_id,
    ).order_by(
        DataItem.metadata_.op("->>")(
            "position"
        ).cast(Integer)
    )

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "source": "spotify",
        "playlist_id": playlist_id,
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


# ── Sync Status ───────────────────────────────────────────────────


@router.get("/sync-status")
async def collectors_sync_status(db: AsyncSession = Depends(get_db)):
    """Get sync status for all collector sources (including per-account Google tokens)."""
    result = await db.execute(
        select(SyncState).where(
            SyncState.source.in_(ALL_SOURCES)
            | SyncState.source.like(f"{GOOGLE_SOURCE_PREFIX}%")
        )
    )
    states = result.scalars().all()

    return {
        s.source: {
            "last_sync": s.last_sync_at.isoformat() if s.last_sync_at else None,
            "status": s.status,
            "items_synced": s.items_synced,
            "error": s.error_message,
        }
        for s in states
    }


# ── Generic Data Query ────────────────────────────────────────────


# ── tldv (Meeting Recordings) ───────────────────────────────────


@router.post("/tldv/sync")
async def tldv_sync(db: AsyncSession = Depends(get_db)):
    """Manually trigger tldv meetings sync."""
    if not settings.tldv_api_key:
        raise HTTPException(status_code=400, detail="tldv API key not configured")

    collector = TldvCollector()
    try:
        count = await collector.collect(db)
        return {"success": True, "items_synced": count}
    except Exception as e:
        logger.exception("[tldv] Sync failed")
        raise HTTPException(status_code=500, detail=str(e))


# ── Generic Data Query ────────────────────────────────────────────


@router.get("/{source}")
async def collector_data(
    source: str,
    days: int = Query(default=7, le=3650),
    item_type: str = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Get collected data for any source."""
    if source not in ALL_SOURCES:
        raise HTTPException(status_code=404, detail=f"Unknown source: {source}")

    since = datetime.now(timezone.utc) - timedelta(days=days)
    query = select(DataItem).where(
        DataItem.source == source,
        DataItem.created_at >= since,
    )
    if item_type:
        query = query.where(DataItem.item_type == item_type)
    query = query.order_by(DataItem.created_at.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "source": source,
        "count": len(items),
        "data": [
            {
                "id": str(item.id),
                "type": item.item_type,
                "date": item.created_at.isoformat(),
                "title": item.title,
                "content": item.content[:200] if item.content else None,
                **{k: v for k, v in item.metadata_.items() if k != "raw"},
            }
            for item in items
        ],
    }
