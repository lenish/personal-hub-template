"""Google OAuth shared helper — multi-account token management for Gmail, Calendar, Drive."""

import logging
import time

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.models import SyncState

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Each Google account stores tokens as source="google:<account_key>"
# e.g. "google:personal", "google:work"
GOOGLE_SOURCE_PREFIX = "google:"


def google_source(account: str) -> str:
    return f"{GOOGLE_SOURCE_PREFIX}{account}"


async def list_google_accounts(session: AsyncSession) -> list[str]:
    """Return all registered Google account keys."""
    result = await session.execute(
        select(SyncState.source).where(SyncState.source.like(f"{GOOGLE_SOURCE_PREFIX}%"))
    )
    return [row[0].removeprefix(GOOGLE_SOURCE_PREFIX) for row in result.all()]


async def get_valid_google_token(
    session: AsyncSession, client: httpx.AsyncClient, account: str
) -> str | None:
    """Get a valid Google access token for a specific account, refreshing if expired."""
    source = google_source(account)
    result = await session.execute(
        select(SyncState.cursor).where(SyncState.source == source)
    )
    cursor = result.scalar_one_or_none() or {}

    if not cursor or "access_token" not in cursor:
        logger.warning(f"[google:{account}] No token stored. Run OAuth flow first.")
        return None

    obtained_at = cursor.get("_obtained_at", 0)
    expires_in = cursor.get("expires_in", 3600)

    if time.time() > obtained_at + expires_in - 300:
        token = await _refresh_google_token(session, client, cursor, account)
        return token

    return cursor.get("access_token")


async def _refresh_google_token(
    session: AsyncSession, client: httpx.AsyncClient, cursor: dict, account: str
) -> str | None:
    """Refresh Google OAuth token. Preserves existing refresh_token if not returned."""
    refresh_token = cursor.get("refresh_token")
    if not refresh_token:
        logger.error(f"[google:{account}] No refresh token available")
        return None

    resp = await client.post(
        GOOGLE_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
        },
    )
    if resp.status_code != 200:
        logger.error(f"[google:{account}] Token refresh failed: {resp.status_code} {resp.text[:200]}")
        return None

    token_data = resp.json()
    if "refresh_token" not in token_data:
        token_data["refresh_token"] = refresh_token
    token_data["_obtained_at"] = time.time()
    token_data["_account"] = account

    await save_google_token(session, token_data, account)
    return token_data.get("access_token")


async def save_google_token(session: AsyncSession, token_data: dict, account: str):
    """Upsert Google token into sync_state for a specific account."""
    source = google_source(account)
    stmt = pg_insert(SyncState).values(
        source=source, cursor=token_data, status="idle"
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["source"],
        set_={"cursor": token_data, "status": "idle"},
    )
    await session.execute(stmt)
    await session.commit()
