"""tldv collector — meeting recordings and transcripts sync via API key."""

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from api.collectors.base import BaseCollector
from api.config import settings

logger = logging.getLogger(__name__)

TLDV_API_BASE = "https://api.tldv.io/v1alpha1"


class TldvCollector(BaseCollector):
    source = "tldv"
    category = "productivity"

    async def collect(self, session: AsyncSession) -> int:
        if not settings.tldv_api_key:
            raise RuntimeError("TLDV_API_KEY not configured")

        async with httpx.AsyncClient(timeout=30) as client:
            headers = {
                "x-api-key": settings.tldv_api_key,
                "Content-Type": "application/json",
            }

            # Get cursor for incremental sync
            cursor = await self.get_cursor(session)
            last_sync_at = cursor.get("last_sync_at")

            # Fetch meetings with pagination
            all_items = []
            page = 1
            limit = 50

            while True:
                params = {"page": page, "limit": limit}
                resp = await client.get(
                    f"{TLDV_API_BASE}/meetings",
                    headers=headers,
                    params=params,
                )

                if resp.status_code != 200:
                    logger.error(f"[tldv] API error: {resp.status_code} {resp.text[:200]}")
                    raise RuntimeError(f"tldv API returned {resp.status_code}")

                data = resp.json()
                meetings = data.get("meetings", [])

                if not meetings:
                    break

                # Fetch details for each meeting
                for meeting in meetings:
                    meeting_id = meeting.get("id")
                    if not meeting_id:
                        continue

                    # Skip if already synced (incremental)
                    happened_at = meeting.get("happenedAt")
                    if last_sync_at and happened_at:
                        meeting_time = datetime.fromisoformat(happened_at.replace("Z", "+00:00"))
                        last_sync_time = datetime.fromisoformat(last_sync_at)
                        if meeting_time <= last_sync_time:
                            continue

                    # Fetch meeting details
                    detail_resp = await client.get(
                        f"{TLDV_API_BASE}/meetings/{meeting_id}",
                        headers=headers,
                    )
                    if detail_resp.status_code == 200:
                        meeting_detail = detail_resp.json()
                    else:
                        meeting_detail = meeting

                    # Fetch transcript
                    transcript_text = None
                    transcript_resp = await client.get(
                        f"{TLDV_API_BASE}/meetings/{meeting_id}/transcript",
                        headers=headers,
                    )
                    if transcript_resp.status_code == 200:
                        transcript_data = transcript_resp.json()
                        # Combine all speaker segments into text
                        segments = transcript_data.get("transcript", [])
                        if segments:
                            transcript_text = "\n\n".join(
                                f"[{seg.get('speaker', 'Unknown')}] {seg.get('text', '')}"
                                for seg in segments
                            )

                    # Fetch highlights
                    highlights = []
                    highlights_resp = await client.get(
                        f"{TLDV_API_BASE}/meetings/{meeting_id}/highlights",
                        headers=headers,
                    )
                    if highlights_resp.status_code == 200:
                        highlights_data = highlights_resp.json()
                        highlights = highlights_data.get("highlights", [])

                    # Transform to DataItem
                    item = self._transform_meeting(meeting_detail, transcript_text, highlights)
                    if item:
                        all_items.append(item)

                # Check if there are more pages
                if len(meetings) < limit:
                    break
                page += 1

                # Safety limit: max 10,000 results (200 pages × 50)
                if page > 200:
                    logger.warning("[tldv] Reached pagination limit (10,000 meetings)")
                    break

            # Save to database
            count = await self.upsert_items(session, all_items)

            # Update cursor
            if all_items:
                latest_time = max(
                    datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
                    if isinstance(item["created_at"], str)
                    else item["created_at"]
                    for item in all_items
                )
                await self.update_sync_state(
                    session,
                    status="idle",
                    items_synced=count,
                    cursor={"last_sync_at": latest_time.isoformat()},
                )
            else:
                await self.update_sync_state(session, status="idle", items_synced=0)

            return count

    def _transform_meeting(
        self,
        meeting: dict,
        transcript: str | None,
        highlights: list[dict],
    ) -> dict | None:
        """Transform tldv meeting data to DataItem format."""
        meeting_id = meeting.get("id")
        if not meeting_id:
            return None

        name = meeting.get("name", "Untitled Meeting")
        happened_at = meeting.get("happenedAt")
        duration = meeting.get("duration")  # in seconds
        url = meeting.get("url")

        # Build content
        content_parts = []
        if duration:
            minutes = duration // 60
            content_parts.append(f"Duration: {minutes} minutes")

        organizer = meeting.get("organizer", {})
        if organizer:
            content_parts.append(f"Organizer: {organizer.get('name', '')} <{organizer.get('email', '')}>")

        invitees = meeting.get("invitees", [])
        if invitees:
            invitee_list = ", ".join(inv.get("name", inv.get("email", "")) for inv in invitees[:5])
            if len(invitees) > 5:
                invitee_list += f" (+{len(invitees) - 5} more)"
            content_parts.append(f"Participants: {invitee_list}")

        if highlights:
            highlights_text = "\n\n## Highlights\n\n" + "\n".join(
                f"- {h.get('text', '')}" for h in highlights[:10]
            )
            content_parts.append(highlights_text)

        if transcript:
            content_parts.append(f"\n\n## Transcript\n\n{transcript[:5000]}")  # Limit transcript size

        content = "\n\n".join(content_parts)

        # Parse timestamp
        created_at = datetime.now(timezone.utc)
        if happened_at:
            try:
                created_at = datetime.fromisoformat(happened_at.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        return {
            "source": self.source,
            "source_id": meeting_id,
            "category": self.category,
            "item_type": "meeting",
            "title": name,
            "content": content,
            "metadata_": {
                "duration": duration,
                "organizer": organizer,
                "invitees": [{"name": inv.get("name"), "email": inv.get("email")} for inv in invitees],
                "conference_id": meeting.get("conferenceId"),
                "template": meeting.get("template"),
                "highlights_count": len(highlights),
                "has_transcript": bool(transcript),
            },
            "source_url": url,
            "created_at": created_at,
        }
