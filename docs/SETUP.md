# Personal Hub - Setup Guide

Complete setup guide from zero to running Personal Hub.

## Prerequisites

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Domain name** (optional, for public access)
- **OAuth credentials** for data sources you want to use (optional)

## Quick Start (Development)

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/personal-hub-template.git
cd personal-hub-template
```

### 2. Run Automated Setup

```bash
chmod +x scripts/init.sh
./scripts/init.sh
```

This script will:
- Create `.env` from template
- Generate random secrets
- Build Docker images
- Start all services

### 3. Access Your Hub

- **Web UI**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Manual Setup

### Step 1: Environment Configuration

```bash
# Copy template
cp .env.template .env

# Edit configuration
nano .env
```

**Required settings:**
```bash
# Generate random secrets
AUTH_SECRET=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 16)
API_KEY=$(openssl rand -base64 32)

# Add to .env
AUTH_SECRET=your_generated_secret
POSTGRES_PASSWORD=your_generated_password
api_key=your_generated_api_key
```

### Step 2: OAuth Providers (Optional)

#### Google OAuth (for Auth.js login)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Google+ API"
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:3000/api/auth/callback/google`
5. Copy Client ID and Secret to `.env`:
   ```bash
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   ```

### Step 3: Enable Data Sources

Edit `.env` and enable sources you want:

```bash
# Enable health data
ENABLE_WHOOP=true
ENABLE_APPLE_HEALTH=true
ENABLE_WITHINGS=false

# Enable communication
ENABLE_SLACK=true
ENABLE_TELEGRAM=false

# Enable productivity
ENABLE_GOOGLE_CALENDAR=true
```

See [DATA_SOURCES.md](DATA_SOURCES.md) for setup instructions for each source.

### Step 4: Build and Start

```bash
cd docker
docker-compose build
docker-compose up -d
```

### Step 5: Verify Services

```bash
# Check all services are running
docker-compose ps

# View logs
docker-compose logs -f

# Test API
curl http://localhost:8000/health
```

Expected output:
```json
{
  "status": "healthy",
  "environment": "production",
  "features": {
    "whoop": true,
    "apple_health": true,
    ...
  }
}
```

## Production Deployment

### Option 1: VPS with Docker Compose

**Requirements:**
- Ubuntu 22.04+ or similar
- 2GB+ RAM
- Docker installed

**Steps:**

```bash
# 1. Clone on server
git clone https://github.com/yourusername/personal-hub-template.git
cd personal-hub-template

# 2. Configure environment
cp .env.template .env
nano .env  # Edit with production values

# 3. Update CORS origins
CORS_ORIGINS=https://yourdomain.com

# 4. Start services
cd docker
docker-compose up -d

# 5. Set up reverse proxy (nginx)
# See docs/DEPLOYMENT.md for nginx configuration
```

### Option 2: Cloudflare Tunnel (for public access)

```bash
# 1. Install cloudflared
# https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/

# 2. Create tunnel
cloudflared tunnel create personal-hub

# 3. Get tunnel token
cloudflared tunnel token personal-hub

# 4. Add token to .env
ENABLE_CLOUDFLARE_TUNNEL=true
CLOUDFLARE_TUNNEL_TOKEN=your_tunnel_token

# 5. Start with Cloudflare profile
docker-compose --profile cloudflare up -d
```

## Database Migrations

### Initial Setup

Tables are created automatically on first startup via Docker entrypoint.

### Manual Migration (if using Alembic)

```bash
# Generate migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Apply migration
docker-compose exec api alembic upgrade head

# Rollback
docker-compose exec api alembic downgrade -1
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Rebuild images
docker-compose build --no-cache

# Remove volumes (WARNING: deletes data)
docker-compose down -v
```

### Database Connection Errors

```bash
# Check postgres is running
docker-compose ps postgres

# Check connection string
docker-compose exec api python -c "from api.config import settings; print(settings.database_url)"

# Restart postgres
docker-compose restart postgres
```

### OAuth Redirect Errors

- Verify redirect URI in OAuth provider matches exactly
- Check AUTH_TRUST_HOST=true if behind proxy
- Ensure CORS_ORIGINS includes your domain

## Next Steps

- [Configure data sources](DATA_SOURCES.md)
- [Customize configuration](CONFIGURATION.md)
- [Deploy to production](DEPLOYMENT.md)
- [Extend with custom collectors](../api/collectors/README.md)
