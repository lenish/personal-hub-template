# Personal Hub Template

**A self-hosted personal data hub** - Collect, aggregate, and visualize your personal data from multiple sources in one unified dashboard.

🏗️ **Status**: Active Development - v0.1.0 Template Release

## 🎯 What is This?

Personal Hub is an open-source template for building your own personal data platform. It helps you:

- **Aggregate** health data from Whoop, Apple Health, Withings
- **Centralize** communications from Slack, Telegram
- **Visualize** your data in beautiful dashboards
- **Own** your data - completely self-hosted
- **Extend** with custom data sources

## ✨ Features

### 📊 Data Sources (All Optional & Modular)

- **Health & Fitness**
  - 🏃 Whoop (recovery, sleep, workouts)
  - 🍎 Apple Health (26+ metrics via webhook)
  - ⚖️ Withings (body composition, blood pressure)

- **Communication**
  - 💬 Slack (message history, channels)
  - ✈️ Telegram (messages, groups)

- **Productivity**
  - 📅 Google Calendar (events, meetings)

### 🔐 Authentication

- Auth.js v5 (NextAuth)
- Google OAuth (default)
- Extensible to GitHub, Apple, etc.

### 🎨 Dashboard

- Next.js 15 (App Router)
- Server Components + Client Islands
- Radix UI + Tailwind CSS 4
- Responsive design

### 🚀 Deployment

- **Docker Compose** - One command deployment
- **Self-hosted** - Your server, your data
- **Cloudflare Tunnel** - Optional public access
- **Systemd** - Production-ready services

## 📦 Quick Start

### Prerequisites

- Docker & Docker Compose
- (Optional) Domain name for public access
- (Optional) OAuth credentials for data sources

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/personal-hub-template.git
cd personal-hub-template

# 2. Run setup script
chmod +x scripts/init.sh
./scripts/init.sh

# 3. Access your hub
open http://localhost:3000
```

The init script will:
- ✅ Create `.env` from template
- ✅ Generate secure random secrets
- ✅ Build Docker images
- ✅ Start all services
- ✅ Set up database

### Manual Setup

```bash
# 1. Copy environment template
cp .env.template .env

# 2. Edit .env and configure:
#    - Database credentials
#    - Auth secret
#    - OAuth providers
#    - Data sources (enable/disable)
nano .env

# 3. Start services
cd docker
docker-compose up -d

# 4. View logs
docker-compose logs -f
```

## 📖 Documentation

- [**Setup Guide**](docs/SETUP.md) - Detailed installation instructions
- [**Configuration**](docs/CONFIGURATION.md) - All configuration options
- [**Data Sources**](docs/DATA_SOURCES.md) - Setting up each data source
- [**Deployment**](docs/DEPLOYMENT.md) - Production deployment guide
- [**Architecture**](docs/ARCHITECTURE.md) - System architecture overview

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────┐
│                   User Interface                      │
│            Next.js 15 + Auth.js v5                   │
│                 (Port 3000)                          │
└───────────────────┬──────────────────────────────────┘
                    │
                    │ HTTP/REST
                    │
┌───────────────────▼──────────────────────────────────┐
│                FastAPI Backend                        │
│          (Port 8000, Auto Docs at /docs)             │
├──────────────────────────────────────────────────────┤
│  Modular Data Collectors:                            │
│  • Whoop (OAuth 2.0, 5-min sync)                    │
│  • Apple Health (Webhook, iOS app)                   │
│  • Withings (OAuth 2.0, 5-min sync)                 │
│  • Slack (Bot Token, 10-min sync)                   │
│  • Telegram (Bot API, real-time)                    │
│  • Google Calendar (OAuth 2.0, on-demand)           │
└───────────────────┬──────────────────────────────────┘
                    │
                    │ SQL
                    │
┌───────────────────▼──────────────────────────────────┐
│            PostgreSQL Database                        │
│              (Port 5432)                             │
│                                                      │
│  Tables: users, health_data, messages,              │
│          calendar_events, data_sources              │
└──────────────────────────────────────────────────────┘
```

## 🔧 Configuration

All configuration via `.env` file:

```bash
# Enable/disable data sources
ENABLE_WHOOP=true
ENABLE_APPLE_HEALTH=false
ENABLE_WITHINGS=true
# ... etc

# Configure each source
WHOOP_CLIENT_ID=your_client_id
WHOOP_CLIENT_SECRET=your_secret
# ... etc
```

See [`.env.template`](.env.template) for all options.

## 🚀 Deployment Options

### Docker Compose (Recommended)

```bash
docker-compose up -d
```

### Systemd Services

```bash
# Install as systemd services
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable personal-hub-{api,web}
sudo systemctl start personal-hub-{api,web}
```

### Cloudflare Tunnel

```bash
# Add to docker-compose.yml
docker-compose --profile cloudflare up -d
```

## 🔒 Security

- ✅ OAuth 2.0 for all integrations
- ✅ Webhook token validation
- ✅ Environment-based secrets
- ✅ Optional 1Password CLI integration
- ✅ CORS configuration
- ✅ Docker network isolation

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit a pull request

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend with [Next.js 15](https://nextjs.org/)
- Authentication via [Auth.js](https://authjs.dev/)
- UI components from [Radix UI](https://www.radix-ui.com/)

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/personal-hub-template/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/personal-hub-template/discussions)

## 🗺️ Roadmap

- [x] Core template structure
- [x] Docker Compose setup
- [x] Health data collectors
- [x] Basic dashboard
- [ ] Data export/backup tools
- [ ] More data sources (Spotify, Strava, etc.)
- [ ] Mobile app
- [ ] AI insights & analytics
- [ ] Multi-user support

---

**Made with ❤️ for the self-hosted community**

⭐ Star this repo if you find it useful!
