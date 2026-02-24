# Personal Hub Template

**A self-hosted personal data hub** - Collect, aggregate, and visualize your personal data from multiple sources in one unified dashboard.

## Quick Links

- [Setup Guide](SETUP.md) - Complete installation instructions
- [Configuration](CONFIGURATION.md) - All configuration options
- [Data Sources](DATA_SOURCES.md) - Setting up each data source

## Features

### 📊 Data Sources (All Optional & Modular)

**Health & Fitness**
- 🏃 Whoop (recovery, sleep, workouts)
- 🍎 Apple Health (26+ metrics via webhook)
- ⚖️ Withings (body composition, blood pressure)

**Music & Entertainment**
- 🎵 Spotify (listening history, playlists)

**Productivity**
- 📅 Google Calendar (events, meetings, multi-account support)

### 🔐 Authentication

- Auth.js v5 (NextAuth)
- Google OAuth (default)
- Single-user deployment model

### 🎨 Dashboard

- Next.js 15 with App Router
- Server Components + Client Islands
- shadcn/ui components
- Dark mode support
- Responsive design

### 🚀 Deployment

- Docker Compose - One command deployment
- Self-hosted - Your server, your data
- Cloudflare Tunnel optional
- PostgreSQL database

## Quick Start

```bash
# 1. Clone repository
git clone https://github.com/lenish/personal-hub-template.git
cd personal-hub-template

# 2. Run setup script
chmod +x scripts/init.sh
./scripts/init.sh

# 3. Access your hub
open http://localhost:3000
```

## Architecture

```
┌──────────────────────────────────────────────┐
│           Next.js 15 Frontend                │
│         (Port 3000, Auth.js v5)              │
└───────────────┬──────────────────────────────┘
                │ HTTP/REST
                │
┌───────────────▼──────────────────────────────┐
│          FastAPI Backend (Port 8000)         │
│                                              │
│  Collectors:                                 │
│  • Whoop, Apple Health, Withings            │
│  • Spotify, Google Calendar                 │
│  • APScheduler auto-sync                    │
└───────────────┬──────────────────────────────┘
                │ SQL
                │
┌───────────────▼──────────────────────────────┐
│        PostgreSQL Database (Port 5432)       │
│                                              │
│  Tables: data_items, sync_state             │
└──────────────────────────────────────────────┘
```

## Project Status

🏗️ **v0.3.0** - Template Release (~70% complete)

- ✅ Core template structure
- ✅ 5 data collectors (Whoop, Apple Health, Withings, Spotify, Google Calendar)
- ✅ Full-featured dashboard (5 pages)
- ✅ OAuth flows for all sources
- ✅ Auto-sync scheduler
- ✅ Docker deployment

## License

MIT License - See LICENSE for details.

---

**Made with ❤️ for the self-hosted community**
