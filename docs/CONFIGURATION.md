# Personal Hub - Configuration Reference

Complete reference for all configuration options.

## Environment Variables

All configuration is done through `.env` file or environment variables.

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `NODE_ENV` | `production` | Environment (development/production) |
| `LOG_LEVEL` | `INFO` | Log level (DEBUG/INFO/WARNING/ERROR) |
| `API_PORT` | `8000` | API server port |
| `WEB_PORT` | `3000` | Web server port |
| `TZ` | `UTC` | Timezone |

### Database

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `POSTGRES_USER` | ✅ | Database user |
| `POSTGRES_PASSWORD` | ✅ | Database password |
| `POSTGRES_DB` | ✅ | Database name |

**Example:**
```bash
DATABASE_URL=postgresql://hub_user:password@postgres:5432/personal_hub
POSTGRES_USER=hub_user
POSTGRES_PASSWORD=secure_random_password
POSTGRES_DB=personal_hub
```

### Authentication

| Variable | Required | Description |
|----------|----------|-------------|
| `AUTH_SECRET` | ✅ | Auth.js secret key (32+ chars) |
| `AUTH_TRUST_HOST` | No | Trust proxy headers (true for Cloudflare) |
| `API_KEY` | No | API authentication key (if empty, auth disabled) |

**Generate secrets:**
```bash
openssl rand -base64 32
```

### CORS

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |

**Example:**
```bash
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Feature Flags

Enable/disable data sources:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_WHOOP` | `false` | Whoop health data |
| `ENABLE_APPLE_HEALTH` | `false` | Apple Health webhook |
| `ENABLE_WITHINGS` | `false` | Withings body metrics |
| `ENABLE_SLACK` | `false` | Slack messages |
| `ENABLE_TELEGRAM` | `false` | Telegram messages |
| `ENABLE_GOOGLE_CALENDAR` | `false` | Google Calendar events |
| `ENABLE_SPOTIFY` | `false` | Spotify listening history |
| `ENABLE_NOTION` | `false` | Notion pages/databases |

### Data Source Configuration

See [DATA_SOURCES.md](DATA_SOURCES.md) for detailed setup of each source.

## Docker Configuration

### docker-compose.yml

**Service profiles:**
- `default`: API, Web, PostgreSQL
- `cloudflare`: Adds Cloudflare Tunnel

**Start with specific profile:**
```bash
docker-compose --profile cloudflare up -d
```

### Resource Limits

Edit `docker-compose.yml` to add resource limits:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

## Security Best Practices

1. **Use strong random secrets**
   ```bash
   openssl rand -base64 32
   ```

2. **Never commit .env to git**
   - Already in .gitignore
   - Use .env.template as reference

3. **Limit CORS origins**
   - Don't use `*` in production
   - Specify exact domains

4. **Use API key authentication**
   - Set `api_key` in .env
   - Include `X-API-Key` header in requests

5. **HTTPS in production**
   - Use reverse proxy (nginx) with SSL
   - Or use Cloudflare Tunnel

6. **Regular backups**
   ```bash
   docker-compose exec postgres pg_dump -U hub_user personal_hub > backup.sql
   ```

## Advanced Configuration

### Custom API Port

```bash
API_PORT=9000
```

Update docker-compose.yml ports mapping:
```yaml
services:
  api:
    ports:
      - "9000:8000"
```

### Multiple Databases

Use different `DATABASE_URL` for read replicas:

```bash
DATABASE_URL=postgresql://...@primary:5432/personal_hub
DATABASE_READONLY_URL=postgresql://...@replica:5432/personal_hub
```

### Redis Caching

```bash
REDIS_URL=redis://localhost:6379/0
```

Add Redis service to docker-compose.yml (see example in repo).

## Environment-Specific Configs

### Development

```bash
NODE_ENV=development
LOG_LEVEL=DEBUG
api_key=  # Disable API auth
```

### Production

```bash
NODE_ENV=production
LOG_LEVEL=INFO
AUTH_TRUST_HOST=true  # If behind proxy
API_KEY=secure_random_key
CORS_ORIGINS=https://yourdomain.com
```

## Configuration Validation

Check configuration:

```bash
# API health check
curl http://localhost:8000/health

# API status (shows enabled features)
curl http://localhost:8000/api/status

# Check environment in container
docker-compose exec api env | grep ENABLE_
```

## Troubleshooting

### Configuration not loading

- Check `.env` file exists in project root
- Restart services after changing .env:
  ```bash
  docker-compose restart
  ```

### OAuth not working

- Verify redirect URIs match exactly
- Check AUTH_TRUST_HOST=true if behind proxy
- Ensure GOOGLE_CLIENT_ID/SECRET are set

### Database connection fails

- Check DATABASE_URL format
- Ensure postgres service is running
- Verify credentials match POSTGRES_* vars
