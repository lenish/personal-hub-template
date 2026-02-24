"""Withings API collector — body composition, weight, blood pressure, sleep."""

import hashlib
import hmac
import logging
import time
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from api.collectors.base import BaseCollector
from api.config import settings

logger = logging.getLogger(__name__)

WITHINGS_API_BASE = "https://wbsapi.withings.net"
WITHINGS_TOKEN_URL = f"{WITHINGS_API_BASE}/v2/oauth2"

# Measurement type codes
MEAS_TYPES = {
    1: ("weight", "kg"),
    4: ("height", "m"),
    5: ("fat_free_mass", "kg"),
    6: ("fat_ratio", "%"),
    8: ("fat_mass_weight", "kg"),
    9: ("diastolic_bp", "mmHg"),
    10: ("systolic_bp", "mmHg"),
    11: ("heart_pulse", "bpm"),
    76: ("muscle_mass", "kg"),
    77: ("hydration", "kg"),
    88: ("bone_mass", "kg"),
}


def _compute_signature(params: dict, client_secret: str) -> str:
    """Compute HMAC-SHA256 signature for Withings API.

    Sort params by key alphabetically, join values with comma, then HMAC.
    """
    sorted_keys = sorted(params.keys())
    value_str = ",".join(str(params[k]) for k in sorted_keys)
    return hmac.new(
        client_secret.encode(), value_str.encode(), hashlib.sha256
    ).hexdigest()


class WithingsCollector(BaseCollector):
    source = "withings"
    category = "health"

    def __init__(self):
        self._token_data: dict | None = None

    async def _get_nonce(self, client: httpx.AsyncClient) -> str | None:
        """Get a nonce from Withings signature endpoint."""
        params = {
            "action": "getnonce",
            "client_id": settings.withings_client_id,
            "timestamp": int(time.time()),
        }
        signature = _compute_signature(params, settings.withings_client_secret)
        params["signature"] = signature

        resp = await client.post(f"{WITHINGS_API_BASE}/v2/signature", data=params)
        if resp.status_code != 200:
            logger.error(f"[withings] Nonce request HTTP error: {resp.status_code}")
            return None

        data = resp.json()
        if data.get("status") != 0:
            logger.error(f"[withings] Nonce request failed: {data}")
            return None

        return data.get("body", {}).get("nonce")

    async def _refresh_token(self, client: httpx.AsyncClient) -> str | None:
        """Refresh Withings OAuth token."""
        cursor = self._token_data
        if not cursor or "refresh_token" not in cursor:
            logger.error("[withings] No refresh token available")
            return None

        params = {
            "action": "requesttoken",
            "grant_type": "refresh_token",
            "client_id": settings.withings_client_id,
            "client_secret": settings.withings_client_secret,
            "refresh_token": cursor["refresh_token"],
        }

        resp = await client.post(WITHINGS_TOKEN_URL, data=params)
        if resp.status_code != 200:
            logger.error(f"[withings] Token refresh HTTP error: {resp.status_code} {resp.text[:200]}")
            return None

        data = resp.json()
        if data.get("status") != 0:
            logger.error(f"[withings] Token refresh failed: {data}")
            return None

        token_data = data.get("body", {})
        token_data["_obtained_at"] = time.time()
        self._token_data = token_data
        return token_data.get("access_token")

    async def _get_valid_token(self, session: AsyncSession, client: httpx.AsyncClient) -> str | None:
        """Get a valid access token, refreshing if needed."""
        cursor = await self.get_cursor(session)
        self._token_data = cursor

        if not cursor or "access_token" not in cursor:
            logger.warning("[withings] No token stored in sync_state. Run initial OAuth flow first.")
            return None

        obtained_at = cursor.get("_obtained_at", 0)
        expires_in = cursor.get("expires_in", 10800)  # Withings: 3 hours

        if time.time() > obtained_at + expires_in - 300:
            token = await self._refresh_token(client)
            return token

        return cursor.get("access_token")

    async def _api_post(
        self, client: httpx.AsyncClient, endpoint: str, token: str, params: dict
    ) -> dict | None:
        """Make a signed POST request to Withings API."""
        nonce = await self._get_nonce(client)
        if not nonce:
            logger.error("[withings] Failed to get nonce")
            return None

        # Build params for signature
        sign_params = {**params, "nonce": nonce}
        signature = _compute_signature(sign_params, settings.withings_client_secret)

        post_data = {**params, "nonce": nonce, "signature": signature}

        resp = await client.post(
            f"{WITHINGS_API_BASE}/{endpoint}",
            data=post_data,
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code != 200:
            logger.error(f"[withings] API {endpoint}: HTTP {resp.status_code} {resp.text[:200]}")
            return None

        data = resp.json()
        if data.get("status") != 0:
            logger.error(f"[withings] API {endpoint}: status={data.get('status')} error={data.get('error')}")
            return None

        return data.get("body", {})

    def _parse_measurements(self, data: dict) -> list[dict]:
        """Parse measure/getmeas response into DataItem dicts.

        Groups measurements by date, creating one item per measuregrp.
        """
        items = []
        for grp in data.get("measuregrps", []):
            grp_date = datetime.fromtimestamp(grp.get("date", 0), tz=timezone.utc)
            date_str = grp_date.strftime("%Y-%m-%d")
            grp_id = grp.get("grpid", grp.get("date", 0))

            measures = {}
            for m in grp.get("measures", []):
                type_code = m.get("type")
                if type_code not in MEAS_TYPES:
                    continue
                name, unit = MEAS_TYPES[type_code]
                value = m.get("value", 0) * (10 ** m.get("unit", 0))
                measures[name] = round(value, 2)

            if not measures:
                continue

            # Determine item_type based on what was measured
            if "systolic_bp" in measures or "diastolic_bp" in measures:
                item_type = "blood_pressure"
                title = f"Blood Pressure {date_str}"
                tags = ["withings", "blood_pressure"]
            else:
                item_type = "body_composition"
                title = f"Body Composition {date_str}"
                tags = ["withings", "body_composition"]

            items.append({
                "source": self.source,
                "source_id": f"{item_type}-{grp_id}",
                "category": self.category,
                "item_type": item_type,
                "title": title,
                "content": None,
                "metadata_": {
                    **measures,
                    "raw": grp,
                },
                "tags": tags,
                "is_public": False,
                "source_url": None,
                "created_at": grp_date,
            })

        return items

    def _parse_sleep(self, data: dict) -> list[dict]:
        """Parse v2/sleep getsummary response."""
        items = []
        for s in data.get("series", []):
            start = s.get("startdate")
            end = s.get("enddate")
            if not start:
                continue

            sleep_date = datetime.fromtimestamp(start, tz=timezone.utc)
            date_str = sleep_date.strftime("%Y-%m-%d")
            sleep_data = s.get("data", {})

            duration_sec = (end - start) if end else 0
            total_hours = round(duration_sec / 3600, 1) if duration_sec else None

            items.append({
                "source": self.source,
                "source_id": f"sleep-{s.get('id', start)}",
                "category": self.category,
                "item_type": "sleep",
                "title": f"Sleep {date_str}",
                "content": None,
                "metadata_": {
                    "total_sleep_hours": total_hours,
                    "deep_hours": round(sleep_data.get("deepsleepduration", 0) / 3600, 1),
                    "rem_hours": round(sleep_data.get("remsleepduration", 0) / 3600, 1),
                    "light_hours": round(sleep_data.get("lightsleepduration", 0) / 3600, 1),
                    "wakeup_count": sleep_data.get("wakeupcount"),
                    "wakeup_duration_min": round(sleep_data.get("wakeupduration", 0) / 60, 1),
                    "hr_average": sleep_data.get("hr_average"),
                    "hr_min": sleep_data.get("hr_min"),
                    "rr_average": sleep_data.get("rr_average"),
                    "sleep_score": sleep_data.get("sleep_score"),
                    "raw": s,
                },
                "tags": ["withings", "sleep"],
                "is_public": False,
                "source_url": None,
                "created_at": sleep_date,
            })

        return items

    async def collect(self, session: AsyncSession) -> int:
        async with httpx.AsyncClient(timeout=30) as client:
            token = await self._get_valid_token(session, client)
            if not token:
                raise RuntimeError("No valid Withings token available")

            # Fetch last 30 days of measurements
            now = int(time.time())
            thirty_days_ago = int((datetime.now(timezone.utc) - timedelta(days=30)).timestamp())

            meas_data = await self._api_post(client, "measure", token, {
                "action": "getmeas",
                "meastypes": "1,4,5,6,8,9,10,11,76,77,88",
                "category": "1",  # real measurements only
                "startdate": str(thirty_days_ago),
                "enddate": str(now),
            })

            sleep_data = await self._api_post(client, "v2/sleep", token, {
                "action": "getsummary",
                "startdateymd": (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d"),
                "enddateymd": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            })

            all_items = []
            if meas_data:
                all_items.extend(self._parse_measurements(meas_data))
            if sleep_data:
                all_items.extend(self._parse_sleep(sleep_data))

            count = await self.upsert_items(session, all_items)

            # Save refreshed token back to cursor
            if self._token_data:
                await self.update_sync_state(session, status="idle", items_synced=count, cursor=self._token_data)

            return count
