# Personal Hub - Data Sources Guide

## Available Data Sources

This guide covers setup for each supported data source.

## Health Data

### Apple Health (via Webhook)

**How it works:** iOS app "Health Auto Export" sends data to your API via webhook.

**Setup:**

1. Install "Health Auto Export" on iPhone
2. Configure webhook URL: `https://your-domain.com/api/health/webhook`
3. Set webhook token in `.env`:
   ```bash
   ENABLE_APPLE_HEALTH=true
   APPLE_HEALTH_WEBHOOK_TOKEN=your_random_token
   ```
4. Configure app to send data (recommend: hourly)

**Supported metrics:** Steps, Heart Rate, Sleep, Workouts, and 20+ more

### Whoop

**How it works:** OAuth 2.0 + API polling every 5 minutes

**Setup:**

1. Create Whoop developer account
2. Register OAuth application
3. Get Client ID and Secret
4. Add to `.env`:
   ```bash
   ENABLE_WHOOP=true
   WHOOP_CLIENT_ID=your_client_id
   WHOOP_CLIENT_SECRET=your_client_secret
   WHOOP_REDIRECT_URI=https://your-domain.com/api/health/whoop/callback
   ```
5. Visit `/api/health/whoop/authorize` to connect

**Data collected:** Recovery score, Sleep, Workouts, Heart Rate

### Withings

Similar to Whoop - OAuth 2.0 setup required.

## Communication

### Slack

**Setup:**

1. Create Slack app at api.slack.com/apps
2. Add Bot Token Scopes: `channels:history`, `channels:read`
3. Install app to workspace
4. Add to `.env`:
   ```bash
   ENABLE_SLACK=true
   SLACK_BOT_TOKEN=xoxb-your-token
   ```

**Data collected:** Messages, channels, files

### Telegram

Coming soon - contributions welcome!

## Productivity

### Google Calendar

**Setup:**

1. Google Cloud Console → Create OAuth credentials
2. Enable Google Calendar API
3. Add to `.env`:
   ```bash
   ENABLE_GOOGLE_CALENDAR=true
   GOOGLE_CLIENT_ID=your_id
   GOOGLE_CLIENT_SECRET=your_secret
   GOOGLE_CALENDAR_IDS=primary  # Or specific calendar IDs
   ```

**Data collected:** Events, attendees, locations

## Adding Custom Data Sources

See [api/collectors/README.md](../api/collectors/README.md) for guide on implementing custom collectors.

**Example structure:**

```python
from api.collectors.base import BaseCollector

class MyCollector(BaseCollector):
    source = "my-service"
    category = "productivity"

    async def collect(self, session):
        # 1. Fetch from external API
        # 2. Transform to DataItem format
        # 3. Use self.upsert_items() to save
        pass
```
