"""Google Calendar collector — event metadata (title, time, attendees)."""

import logging
import re
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from api.collectors.base import BaseCollector
from api.collectors.google_auth import get_valid_google_token, list_google_accounts
from api.config import settings

logger = logging.getLogger(__name__)

CALENDAR_API = "https://www.googleapis.com/calendar/v3"

# Virtual meeting URL patterns to skip geocoding
_VIRTUAL_PATTERN = re.compile(
    r"zoom\.us|meet\.google\.com|teams\.microsoft\.com|webex\.com|whereby\.com|"
    r"gather\.town|around\.co|cal\.com|calendly\.com|^https?://",
    re.IGNORECASE,
)

# Non-address patterns: room codes, floor numbers, generic text
_NON_ADDRESS_PATTERN = re.compile(
    r"^[A-Z]{1,4}-?\d{1,3}[A-Z]?[-./]?\d{0,3}[A-Z]?\s*(\(\d+\))?$"  # room codes like "KS-19-19B (12)"
    r"|^(we |tbd|tbc|online|virtual|remote|see |check )"  # descriptive text
    r"|^\d{1,3}[A-Z]?$"  # bare room/floor numbers
    r"|^(room|floor|level|rm|fl|meeting room)\s"  # room/floor prefixes
    r"|^[^,]{1,20}$"  # very short strings without comma (likely venue name only)
    ,
    re.IGNORECASE,
)

# Google Geocoding result types that indicate a precise-enough match
_GOOD_RESULT_TYPES = {
    "street_address", "premise", "subpremise", "establishment",
    "point_of_interest", "airport", "transit_station",
}


async def _geocode_location(location: str, client: httpx.AsyncClient) -> list[float] | None:
    """Geocode a location string using Google Geocoding API. Returns [lat, lng] or None."""
    if not location or not settings.google_geocoding_api_key:
        return None
    if _VIRTUAL_PATTERN.search(location):
        return None
    if _NON_ADDRESS_PATTERN.search(location.strip()):
        return None
    try:
        resp = await client.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": location, "key": settings.google_geocoding_api_key},
            timeout=5.0,
        )
        data = resp.json()
        if data.get("status") == "OK" and data.get("results"):
            result = data["results"][0]
            result_types = set(result.get("types", []))
            loc_type = result.get("geometry", {}).get("location_type", "")

            if result_types & _GOOD_RESULT_TYPES or loc_type in ("ROOFTOP", "RANGE_INTERPOLATED"):
                loc = result["geometry"]["location"]
                return [loc["lat"], loc["lng"]]
            if loc_type == "GEOMETRIC_CENTER" and not (result_types & {"route"}):
                loc = result["geometry"]["location"]
                return [loc["lat"], loc["lng"]]
    except Exception:
        pass
    return None


class GoogleCalendarCollector(BaseCollector):
    source = "google_calendar"
    category = "productivity"

    async def collect(self, session: AsyncSession) -> int:
        accounts = await list_google_accounts(session)
        if not accounts:
            logger.info("[google_calendar] No Google accounts registered, skipping")
            return 0

        total = 0
        async with httpx.AsyncClient(timeout=30) as client:
            for account in accounts:
                count = await self._collect_account(session, client, account)
                total += count
        return total

    async def _collect_account(
        self, session: AsyncSession, client: httpx.AsyncClient, account: str
    ) -> int:
        token = await get_valid_google_token(session, client, account)
        if not token:
            logger.warning(f"[google_calendar:{account}] No valid token, skipping")
            return 0

        headers = {"Authorization": f"Bearer {token}"}
        cursor = await self.get_cursor(session)
        acct_cursor = cursor.get(account, {})
        sync_tokens = acct_cursor.get("sync_tokens", {})

        calendar_ids = [
            c.strip()
            for c in settings.google_calendar_ids.split(",")
            if c.strip()
        ]

        all_items = []
        new_sync_tokens = dict(sync_tokens)

        for cal_id in calendar_ids:
            sync_token = sync_tokens.get(cal_id)
            items, new_token = await self._fetch_calendar(
                client, headers, cal_id, sync_token, account
            )
            all_items.extend(items)
            if new_token:
                new_sync_tokens[cal_id] = new_token

        count = await self.upsert_items(session, all_items)
        cursor[account] = {"sync_tokens": new_sync_tokens}
        await self.update_sync_state(
            session, status="idle", items_synced=count, cursor=cursor
        )
        return count

    async def _fetch_calendar(
        self, client: httpx.AsyncClient, headers: dict,
        calendar_id: str, sync_token: str | None, account: str,
    ) -> tuple[list[dict], str | None]:
        params: dict = {"maxResults": 250, "singleEvents": "true"}

        if sync_token:
            params["syncToken"] = sync_token
        else:
            now = datetime.now(timezone.utc)
            params["timeMin"] = (now - timedelta(days=3650)).isoformat()
            params["timeMax"] = (now + timedelta(days=30)).isoformat()
            params["orderBy"] = "startTime"

        all_events: list[dict] = []
        next_sync_token: str | None = None

        while True:
            resp = await client.get(
                f"{CALENDAR_API}/calendars/{calendar_id}/events",
                headers=headers,
                params=params,
            )

            if resp.status_code == 410:
                logger.warning(f"[google_calendar:{account}] Sync token expired for {calendar_id}")
                return await self._fetch_calendar(client, headers, calendar_id, None, account)

            if resp.status_code != 200:
                logger.error(f"[google_calendar:{account}] Events {calendar_id}: HTTP {resp.status_code}")
                return [], sync_token

            data = resp.json()
            all_events.extend(data.get("items", []))
            next_sync_token = data.get("nextSyncToken")

            page_token = data.get("nextPageToken")
            if page_token:
                params["pageToken"] = page_token
                params.pop("syncToken", None)
            else:
                break

        events = all_events

        items = []
        for event in events:
            if event.get("status") == "cancelled":
                continue

            event_id = event.get("id", "")
            summary = event.get("summary", "(no title)")
            start = event.get("start", {})
            end = event.get("end", {})

            start_str = start.get("dateTime") or start.get("date", "")
            end_str = end.get("dateTime") or end.get("date", "")

            try:
                if "T" in start_str:
                    created_at = datetime.fromisoformat(start_str)
                else:
                    created_at = datetime.strptime(start_str, "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
            except (ValueError, TypeError):
                created_at = datetime.now(timezone.utc)

            attendees = event.get("attendees", [])
            date_str = start_str[:10] if start_str else ""

            location = event.get("location")
            coordinates = await _geocode_location(location, client) if location else None

            items.append({
                "source": self.source,
                "source_id": f"{account}-event-{event_id}",
                "category": self.category,
                "item_type": "event",
                "title": f"{summary} ({date_str})",
                "content": event.get("description"),
                "metadata_": {
                    "account": account,
                    "calendar_id": calendar_id,
                    "start": start_str,
                    "end": end_str,
                    "location": location,
                    "coordinates": coordinates,
                    "attendee_count": len(attendees),
                    "organizer": event.get("organizer", {}).get("email"),
                    "status": event.get("status"),
                    "recurring": bool(event.get("recurringEventId")),
                    "hangout_link": event.get("hangoutLink"),
                },
                "tags": ["google_calendar", account],
                "is_public": False,
                "source_url": event.get("htmlLink"),
                "created_at": created_at,
            })

        return items, next_sync_token
