"""Whoop API collector — recovery, sleep, and workout data via OAuth 2.0."""

import logging
import time
from datetime import datetime, timedelta, timezone

from zoneinfo import ZoneInfo

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from api.collectors.base import BaseCollector
from api.config import settings

logger = logging.getLogger(__name__)

WHOOP_API_BASE = "https://api.prod.whoop.com/developer/v2"
WHOOP_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"


class WhoopCollector(BaseCollector):
    source = "whoop"
    category = "health"

    def __init__(self):
        self._token_data: dict | None = None
        self._local_tz = ZoneInfo(settings.timezone)

    async def _refresh_token(self, client: httpx.AsyncClient) -> str | None:
        """Refresh the Whoop OAuth token using stored refresh_token."""
        cursor = None
        # Token data is stored in sync_state.cursor
        if self._token_data and "refresh_token" in self._token_data:
            cursor = self._token_data
        if not cursor or "refresh_token" not in cursor:
            logger.error("[whoop] No refresh token available")
            return None

        resp = await client.post(
            WHOOP_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": cursor["refresh_token"],
                "client_id": settings.whoop_client_id,
                "client_secret": settings.whoop_client_secret,
            },
        )
        if resp.status_code != 200:
            logger.error(f"[whoop] Token refresh failed: {resp.status_code} {resp.text[:200]}")
            return None

        token_data = resp.json()
        token_data["_obtained_at"] = time.time()
        self._token_data = token_data
        return token_data.get("access_token")

    async def _get_valid_token(self, session: AsyncSession, client: httpx.AsyncClient) -> str | None:
        """Get a valid access token, refreshing if needed."""
        cursor = await self.get_cursor(session)
        self._token_data = cursor

        if not cursor or "access_token" not in cursor:
            logger.warning("[whoop] No token stored in sync_state. Run initial OAuth flow first.")
            return None

        obtained_at = cursor.get("_obtained_at", 0)
        expires_in = cursor.get("expires_in", 3600)

        if time.time() > obtained_at + expires_in - 300:
            token = await self._refresh_token(client)
            return token

        return cursor.get("access_token")

    async def _api_get(self, client: httpx.AsyncClient, endpoint: str, token: str, params: dict | None = None) -> dict | None:
        resp = await client.get(
            f"{WHOOP_API_BASE}/{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            params=params or {},
        )
        if resp.status_code != 200:
            logger.error(f"[whoop] API {endpoint}: {resp.status_code} {resp.text[:200]}")
            return None
        return resp.json()

    def _parse_recovery(self, data: dict) -> list[dict]:
        items = []
        for r in data.get("records", []):
            score = r.get("score") or {}
            raw_ts = r.get("created_at", "")
            if not raw_ts:
                continue
            utc_dt = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
            local_dt = utc_dt.astimezone(self._local_tz)
            date_str = local_dt.strftime("%Y-%m-%d")
            cycle_id = r.get("cycle_id", date_str)
            items.append({
                "source": self.source,
                "source_id": f"recovery-{cycle_id}",
                "category": self.category,
                "item_type": "recovery",
                "title": f"Recovery {date_str}",
                "content": None,
                "metadata_": {
                    "recovery_score": score.get("recovery_score"),
                    "hrv_rmssd": score.get("hrv_rmssd_milli"),
                    "resting_hr": score.get("resting_heart_rate"),
                    "spo2": score.get("spo2_percentage"),
                    "skin_temp": score.get("skin_temp_celsius"),
                    "raw": r,
                },
                "tags": ["whoop", "recovery"],
                "is_public": False,
                "source_url": None,
                "created_at": local_dt,
            })
        return items

    def _parse_sleep(self, data: dict) -> list[dict]:
        items = []
        for s in data.get("records", []):
            score = s.get("score") or {}
            stages = score.get("stage_summary") or {}
            raw_ts = s.get("start", "")
            if not raw_ts:
                continue
            utc_dt = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
            local_dt = utc_dt.astimezone(self._local_tz)
            date_str = local_dt.strftime("%Y-%m-%d")
            total_sleep = (
                stages.get("total_light_sleep_time_milli", 0)
                + stages.get("total_rem_sleep_time_milli", 0)
                + stages.get("total_slow_wave_sleep_time_milli", 0)
            )
            items.append({
                "source": self.source,
                "source_id": f"sleep-{s.get('id', date_str)}",
                "category": self.category,
                "item_type": "sleep",
                "title": f"Sleep {date_str}",
                "content": None,
                "metadata_": {
                    "performance": score.get("sleep_performance_percentage"),
                    "efficiency": score.get("sleep_efficiency_percentage"),
                    "respiratory_rate": score.get("respiratory_rate"),
                    "total_sleep_hours": round(total_sleep / 3600000, 1) if total_sleep else None,
                    "rem_hours": round(stages.get("total_rem_sleep_time_milli", 0) / 3600000, 1),
                    "deep_hours": round(stages.get("total_slow_wave_sleep_time_milli", 0) / 3600000, 1),
                    "disturbances": stages.get("disturbance_count"),
                    "raw": s,
                },
                "tags": ["whoop", "sleep"],
                "is_public": False,
                "source_url": None,
                "created_at": local_dt,
            })
        return items

    def _parse_workout(self, data: dict) -> list[dict]:
        items = []
        for w in data.get("records", []):
            score = w.get("score") or {}
            raw_ts = w.get("start", "")
            if not raw_ts:
                continue
            utc_dt = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
            local_dt = utc_dt.astimezone(self._local_tz)
            date_str = local_dt.strftime("%Y-%m-%d")
            items.append({
                "source": self.source,
                "source_id": f"workout-{w.get('id', date_str)}",
                "category": self.category,
                "item_type": "workout",
                "title": f"{w.get('sport_name', 'Workout')} {date_str}",
                "content": None,
                "metadata_": {
                    "sport": w.get("sport_name", ""),
                    "strain": score.get("strain"),
                    "avg_hr": score.get("average_heart_rate"),
                    "max_hr": score.get("max_heart_rate"),
                    "calories_kj": score.get("kilojoule"),
                    "distance_m": score.get("distance_meter"),
                    "raw": w,
                },
                "tags": ["whoop", "workout", w.get("sport_name", "").lower()],
                "is_public": False,
                "source_url": None,
                "created_at": local_dt,
            })
        return items

    async def collect(self, session: AsyncSession) -> int:
        async with httpx.AsyncClient(timeout=30) as client:
            token = await self._get_valid_token(session, client)
            if not token:
                raise RuntimeError("No valid Whoop token available")

            params = {"limit": 25, "order": "desc"}
            recovery_data = await self._api_get(client, "recovery", token, params)
            sleep_data = await self._api_get(client, "activity/sleep", token, params)
            workout_data = await self._api_get(client, "activity/workout", token, params)

            all_items = []
            if recovery_data:
                all_items.extend(self._parse_recovery(recovery_data))
            if sleep_data:
                all_items.extend(self._parse_sleep(sleep_data))
            if workout_data:
                all_items.extend(self._parse_workout(workout_data))

            count = await self.upsert_items(session, all_items)

            # Save refreshed token back to cursor
            if self._token_data:
                await self.update_sync_state(session, status="idle", items_synced=count, cursor=self._token_data)

            return count
