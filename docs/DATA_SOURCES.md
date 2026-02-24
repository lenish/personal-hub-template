# Personal Hub - Data Sources Guide

## Available Data Sources

This guide covers setup for each supported data source.

## Health Data

### Apple Health (via Webhook)

**How it works:** iOS app "Health Auto Export" sends data to your API via webhook.

**Setup:**

1. Install "Health Auto Export" app from iOS App Store
2. Configure webhook URL in app: `https://your-domain.com/api/health/webhook`
3. Generate webhook token and add to `.env`:
   ```bash
   ENABLE_APPLE_HEALTH=true
   HEALTH_API_TOKEN=$(openssl rand -base64 32)  # Or use init.sh
   ```
4. In app settings:
   - Enable metrics you want to track
   - Set sync frequency (recommend: hourly or when data changes)
   - Add Authorization header: `Bearer your_health_api_token`

**Supported metrics:** Steps, Heart Rate, Sleep Analysis, Workouts, Active Energy, and 20+ more

**Data format:** Automatically parsed and stored in `data_items` table with category `health`

### Whoop

**How it works:** OAuth 2.0 + API polling every 5 minutes (configurable)

**Setup:**

1. Go to [Whoop Developer Portal](https://developer.whoop.com/)
2. Create a developer account (requires Whoop membership)
3. Register a new OAuth application:
   - Application Name: "Personal Hub"
   - Redirect URI: `http://localhost:8000/api/health/whoop/callback` (or your domain)
4. Copy Client ID and Secret to `.env`:
   ```bash
   ENABLE_WHOOP=true
   WHOOP_CLIENT_ID=your_client_id
   WHOOP_CLIENT_SECRET=your_client_secret
   WHOOP_REDIRECT_URI=http://localhost:8000/api/health/whoop/callback
   WHOOP_SYNC_INTERVAL=5  # Minutes between syncs
   ```
5. Start your hub and visit Settings page → Connect Whoop
6. Authorize the app in Whoop OAuth flow

**Data collected:** Recovery score, Sleep performance, Workouts, Heart Rate variability, Strain

**Sync frequency:** Every 5 minutes by default (configurable via `WHOOP_SYNC_INTERVAL`)

### Withings

**How it works:** OAuth 2.0 + API polling every 5 minutes (configurable)

**Setup:**

1. Go to [Withings Developer Dashboard](https://developer.withings.com/)
2. Create a developer account
3. Register a new application:
   - Application Name: "Personal Hub"
   - Callback URL: `http://localhost:8000/api/health/withings/callback`
4. Get API credentials and add to `.env`:
   ```bash
   ENABLE_WITHINGS=true
   WITHINGS_CLIENT_ID=your_client_id
   WITHINGS_CLIENT_SECRET=your_client_secret
   WITHINGS_REDIRECT_URI=http://localhost:8000/api/health/withings/callback
   WITHINGS_SYNC_INTERVAL=5  # Minutes
   ```
5. Visit Settings page → Connect Withings

**Data collected:** Body weight, Body fat %, Muscle mass, Bone mass, Water %, Heart rate, Blood pressure

**Sync frequency:** Every 5 minutes by default

## Music & Entertainment

### Spotify

**How it works:** OAuth 2.0 + API polling for listening history

**Setup:**

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app:
   - App Name: "Personal Hub"
   - Redirect URI: `http://localhost:8000/api/collectors/spotify/callback`
3. Get Client ID and Secret from app settings
4. Add to `.env`:
   ```bash
   ENABLE_SPOTIFY=true
   SPOTIFY_CLIENT_ID=your_client_id
   SPOTIFY_CLIENT_SECRET=your_client_secret
   SPOTIFY_REDIRECT_URI=http://localhost:8000/api/collectors/spotify/callback
   SPOTIFY_SYNC_INTERVAL=10  # Minutes
   ```
5. Visit Settings page → Connect Spotify
6. Authorize app to access your listening history

**Data collected:**
- Recently played tracks (artist, album, duration)
- Playlists (public and private)
- Listening timestamps
- Track metadata

**Sync frequency:** Every 10 minutes by default

**Note:** Spotify API has rate limits. The collector respects these limits automatically.

## Productivity

### Google Calendar

**How it works:** OAuth 2.0 + on-demand API queries (supports multiple Google accounts)

**Setup:**

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Calendar API:
   - APIs & Services → Enable APIs and Services
   - Search "Google Calendar API" → Enable
4. Create OAuth 2.0 credentials:
   - Credentials → Create Credentials → OAuth client ID
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:8000/api/collectors/google/callback`
5. Copy Client ID and Secret (same as Auth.js Google OAuth)
6. Add to `.env`:
   ```bash
   ENABLE_GOOGLE_CALENDAR=true
   GOOGLE_REDIRECT_URI=http://localhost:8000/api/collectors/google/callback
   GOOGLE_SYNC_INTERVAL=15  # Minutes
   ```
7. Visit Settings page → Connect Google Calendar
8. Select Google account and authorize Calendar access

**Data collected:**
- Calendar events (title, description, time, location)
- Attendees and organizers
- Event status (confirmed, tentative, cancelled)
- Recurring event instances

**Multi-account support:** You can connect multiple Google accounts. Each account is stored separately.

**Sync frequency:** Every 15 minutes by default

**Privacy:** Only events from calendars you explicitly grant access to are synced.

## Communication (Legacy - Optional)

### Slack

**Note:** Slack collector is available but not actively maintained in the template.

**Setup:**

1. Create Slack app at [api.slack.com/apps](https://api.slack.com/apps)
2. Add Bot Token Scopes: `channels:history`, `channels:read`, `users:read`
3. Install app to workspace
4. Add to `.env`:
   ```bash
   ENABLE_SLACK=true
   SLACK_BOT_TOKEN=xoxb-your-token
   ```

**Data collected:** Messages, channels, users

### Telegram

Not currently implemented in template. Contributions welcome!

---

## Adding Custom Data Sources

Want to add your own data source? It's easy!

See [api/collectors/README.md](../api/collectors/README.md) for detailed guide.

**Quick example:**

```python
from api.collectors.base import BaseCollector
from datetime import datetime

class MyCollector(BaseCollector):
    source = "my-service"
    category = "productivity"

    async def collect(self, session):
        # 1. Fetch from external API
        data = await fetch_my_api()

        # 2. Transform to DataItem format
        items = [
            {
                "source": self.source,
                "source_id": item["id"],
                "category": self.category,
                "item_type": "task",
                "title": item["name"],
                "metadata_": {"status": item["status"]},
                "created_at": datetime.fromisoformat(item["created"])
            }
            for item in data
        ]

        # 3. Save to database
        await self.upsert_items(session, items)
```

Then register it in `api/services/sync.py` with a feature flag.
