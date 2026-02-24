"""Spotify collector — recently played tracks sync via OAuth 2.0."""

import base64
import logging
import time
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from api.collectors.base import BaseCollector
from api.config import settings

logger = logging.getLogger(__name__)

SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"


class SpotifyCollector(BaseCollector):
    source = "spotify"
    category = "entertainment"

    def __init__(self):
        self._token_data: dict | None = None

    def _basic_auth(self) -> str:
        """Build Basic auth header for token requests."""
        creds = f"{settings.spotify_client_id}:{settings.spotify_client_secret}"
        return "Basic " + base64.b64encode(creds.encode()).decode()

    async def _refresh_token(self, client: httpx.AsyncClient) -> str | None:
        if not self._token_data or "refresh_token" not in self._token_data:
            logger.error("[spotify] No refresh token available")
            return None

        resp = await client.post(
            SPOTIFY_TOKEN_URL,
            headers={
                "Authorization": self._basic_auth(),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._token_data["refresh_token"],
            },
        )
        if resp.status_code != 200:
            logger.error(f"[spotify] Token refresh failed: {resp.status_code} {resp.text[:200]}")
            return None

        token_data = resp.json()
        token_data["_obtained_at"] = time.time()
        # Spotify may not return a new refresh_token; keep the old one
        if "refresh_token" not in token_data:
            token_data["refresh_token"] = self._token_data["refresh_token"]
        self._token_data = token_data
        return token_data.get("access_token")

    async def _get_valid_token(self, session: AsyncSession, client: httpx.AsyncClient) -> str | None:
        cursor = await self.get_cursor(session)
        self._token_data = cursor

        if not cursor or "access_token" not in cursor:
            logger.warning("[spotify] No token stored. Run OAuth flow first: GET /api/collectors/spotify/authorize")
            return None

        obtained_at = cursor.get("_obtained_at", 0)
        expires_in = cursor.get("expires_in", 3600)

        if time.time() > obtained_at + expires_in - 300:
            return await self._refresh_token(client)

        return cursor.get("access_token")

    async def collect(self, session: AsyncSession) -> int:
        if not settings.spotify_client_id:
            raise RuntimeError("SPOTIFY_CLIENT_ID not configured")

        async with httpx.AsyncClient(timeout=30) as client:
            token = await self._get_valid_token(session, client)
            if not token:
                raise RuntimeError("No valid Spotify token available")

            # Get last sync timestamp for incremental fetch
            after_ms = self._token_data.get("_last_played_at_ms")

            items = await self._fetch_recently_played(client, token, after_ms)
            count = await self.upsert_items(session, items)

            # Update cursor with token + last played timestamp
            if items:
                latest_ms = max(
                    int(datetime.fromisoformat(i["created_at"].isoformat()).timestamp() * 1000)
                    if isinstance(i["created_at"], datetime)
                    else 0
                    for i in items
                )
                if self._token_data:
                    self._token_data["_last_played_at_ms"] = latest_ms

            # Sync playlists (full sync every time — playlists change)
            playlist_items = await self._fetch_playlists(client, token)
            playlist_count = await self.upsert_items(session, playlist_items)
            count += playlist_count

            # Sync playlist tracks
            playlist_track_items = await self._fetch_playlist_tracks(client, token, playlist_items)
            pt_count = await self.upsert_items(session, playlist_track_items)
            count += pt_count

            if self._token_data:
                await self.update_sync_state(session, status="idle", items_synced=count, cursor=self._token_data)

            return count

    async def _fetch_recently_played(
        self, client: httpx.AsyncClient, token: str, after_ms: int | None,
    ) -> list[dict]:
        params: dict[str, str] = {"limit": "50"}
        if after_ms:
            params["after"] = str(after_ms)

        resp = await client.get(
            f"{SPOTIFY_API_BASE}/me/player/recently-played",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        if resp.status_code != 200:
            logger.error(f"[spotify] recently-played: {resp.status_code} {resp.text[:200]}")
            return []

        data = resp.json()
        items_list = data.get("items", [])

        items: list[dict] = []
        for entry in items_list:
            track = entry.get("track") or {}
            played_at_str = entry.get("played_at", "")

            try:
                played_at = datetime.fromisoformat(played_at_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                played_at = datetime.now(timezone.utc)

            track_id = track.get("id", "")
            track_name = track.get("name", "")
            artists = track.get("artists", [])
            artist_name = ", ".join(a.get("name", "") for a in artists) if artists else ""
            album = track.get("album", {})
            album_images = album.get("images", [])
            album_art = album_images[0].get("url") if album_images else None

            context = entry.get("context") or {}

            items.append({
                "source": self.source,
                "source_id": f"listen-{track_id}-{int(played_at.timestamp() * 1000)}",
                "category": self.category,
                "item_type": "listen",
                "title": f"{track_name} — {artist_name}",
                "content": None,
                "metadata_": {
                    "track_id": track_id,
                    "track_name": track_name,
                    "artist_name": artist_name,
                    "artist_ids": [a.get("id") for a in artists],
                    "album_name": album.get("name", ""),
                    "album_id": album.get("id", ""),
                    "duration_ms": track.get("duration_ms"),
                    "explicit": track.get("explicit", False),
                    "album_art_url": album_art,
                    "context_type": context.get("type"),
                    "context_uri": context.get("uri"),
                    "played_at": played_at_str,
                },
                "tags": ["spotify", "music"],
                "is_public": False,
                "source_url": f"https://open.spotify.com/track/{track_id}" if track_id else None,
                "created_at": played_at,
            })

        return items

    async def _fetch_playlists(self, client: httpx.AsyncClient, token: str) -> list[dict]:
        """Fetch all user playlists with pagination."""
        all_items: list[dict] = []
        url = f"{SPOTIFY_API_BASE}/me/playlists"
        params: dict[str, str] = {"limit": "50", "offset": "0"}
        now = datetime.now(timezone.utc)

        while url:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
                params=params if "offset" in params else None,
            )
            if resp.status_code != 200:
                logger.error(f"[spotify] playlists: {resp.status_code} {resp.text[:200]}")
                break

            data = resp.json()
            for pl in data.get("items", []):
                if not pl:
                    continue
                pl_id = pl.get("id", "")
                images = pl.get("images") or []
                image_url = images[0].get("url") if images else None
                owner = pl.get("owner") or {}
                tracks_total = (pl.get("tracks") or pl.get("items") or {}).get("total", 0)
                external_urls = pl.get("external_urls") or {}

                all_items.append({
                    "source": self.source,
                    "source_id": f"playlist-{pl_id}",
                    "category": self.category,
                    "item_type": "playlist",
                    "title": pl.get("name", ""),
                    "content": pl.get("description") or None,
                    "metadata_": {
                        "playlist_id": pl_id,
                        "track_count": tracks_total,
                        "image_url": image_url,
                        "owner_name": owner.get("display_name", ""),
                        "owner_id": owner.get("id", ""),
                        "public": pl.get("public"),
                        "collaborative": pl.get("collaborative", False),
                        "snapshot_id": pl.get("snapshot_id", ""),
                    },
                    "tags": ["spotify", "playlist"],
                    "is_public": bool(pl.get("public")),
                    "source_url": external_urls.get("spotify"),
                    "created_at": now,
                })

            next_url = data.get("next")
            if next_url:
                url = next_url
                params = {}  # next_url already has query params
            else:
                break

        logger.info(f"[spotify] Fetched {len(all_items)} playlists")
        return all_items

    async def _fetch_playlist_tracks(self, client: httpx.AsyncClient, token: str, playlists: list[dict]) -> list[dict]:
        """Fetch tracks for each playlist."""
        import asyncio

        all_items: list[dict] = []
        now = datetime.now(timezone.utc)

        for pl_item in playlists:
            pl_id = pl_item["metadata_"].get("playlist_id", "")
            pl_name = pl_item.get("title", "")
            if not pl_id:
                continue

            # First page: fetch full playlist object
            url: str | None = f"{SPOTIFY_API_BASE}/playlists/{pl_id}"
            first_page = True
            position = 0

            while url:
                resp = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                )
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("retry-after", "60"))
                    if retry_after <= 30:
                        logger.info(f"[spotify] Rate limited, waiting {retry_after}s...")
                        await asyncio.sleep(retry_after + 1)
                        continue
                    logger.warning(f"[spotify] Rate limited, retry-after={retry_after}s. Stopping playlist track fetch.")
                    return all_items
                if resp.status_code != 200:
                    logger.error(f"[spotify] playlist tracks {pl_id}: {resp.status_code} {resp.text[:200]}")
                    break

                data = resp.json()

                if first_page:
                    page = data.get("items") or data.get("tracks") or {}
                    first_page = False
                else:
                    page = data

                entries = page.get("items", []) if isinstance(page, dict) else []

                for entry in entries:
                    track = entry.get("item") or entry.get("track")
                    if not track or not track.get("id"):
                        continue  # skip local files or null tracks

                    track_id = track["id"]
                    artists = track.get("artists", [])
                    artist_name = ", ".join(a.get("name", "") for a in artists) if artists else ""
                    album = track.get("album") or {}
                    album_images = album.get("images", [])
                    album_art = album_images[0].get("url") if album_images else None
                    added_at = entry.get("added_at", "")
                    added_by = (entry.get("added_by") or {}).get("id", "")

                    all_items.append({
                        "source": self.source,
                        "source_id": f"pt-{pl_id}-{track_id}",
                        "category": self.category,
                        "item_type": "playlist_track",
                        "title": f"{track.get('name', '')} — {artist_name}",
                        "content": None,
                        "metadata_": {
                            "track_id": track_id,
                            "track_name": track.get("name", ""),
                            "artist_name": artist_name,
                            "artist_ids": [a.get("id") for a in artists],
                            "album_name": album.get("name", ""),
                            "album_id": album.get("id", ""),
                            "duration_ms": track.get("duration_ms"),
                            "explicit": track.get("explicit", False),
                            "album_art_url": album_art,
                            "added_at": added_at,
                            "added_by": added_by,
                            "playlist_id": pl_id,
                            "playlist_name": pl_name,
                            "position": position,
                        },
                        "tags": ["spotify", "playlist-track"],
                        "is_public": False,
                        "source_url": f"https://open.spotify.com/track/{track_id}",
                        "created_at": now,
                    })
                    position += 1

                next_url = page.get("next") if isinstance(page, dict) else None
                if next_url:
                    url = next_url
                    await asyncio.sleep(0.5)
                else:
                    break

            # Delay between playlists to avoid rate limiting
            await asyncio.sleep(2.0)

        logger.info(f"[spotify] Fetched {len(all_items)} playlist tracks from {len(playlists)} playlists")
        return all_items
