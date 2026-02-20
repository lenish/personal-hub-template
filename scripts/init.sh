#!/bin/bash
#
# Personal Hub Template - Initialization Script
# Sets up your Personal Hub instance

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Personal Hub - Initial Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check dependencies
echo "Checking dependencies..."
MISSING_DEPS=()

if ! command -v docker &> /dev/null; then
    MISSING_DEPS+=("docker")
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    MISSING_DEPS+=("docker-compose")
fi

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    echo -e "${RED}✗ Missing dependencies: ${MISSING_DEPS[*]}${NC}"
    echo "Please install them first:"
    echo "  Docker: https://docs.docker.com/get-docker/"
    echo "  Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓${NC} All dependencies found"
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo -e "${YELLOW}⚠${NC} .env file already exists"
    read -p "Overwrite? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing .env file"
    else
        cp .env.template .env
        echo -e "${GREEN}✓${NC} Created new .env from template"
    fi
else
    cp .env.template .env
    echo -e "${GREEN}✓${NC} Created .env from template"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Please edit .env file and configure:"
echo ""
echo "  1. Database credentials (POSTGRES_PASSWORD)"
echo "  2. Authentication secret (AUTH_SECRET)"
echo "  3. OAuth providers (GOOGLE_CLIENT_ID, etc.)"
echo "  4. Enable data sources you want (ENABLE_WHOOP, etc.)"
echo ""
read -p "Press Enter after editing .env file..."

# Generate secrets if needed
if grep -q "CHANGE_ME" .env; then
    echo ""
    echo "Generating random secrets..."

    # Generate AUTH_SECRET
    AUTH_SECRET=$(openssl rand -base64 32)
    sed -i.bak "s/AUTH_SECRET=CHANGE_ME_RANDOM_STRING/AUTH_SECRET=$AUTH_SECRET/" .env

    # Generate POSTGRES_PASSWORD
    PG_PASSWORD=$(openssl rand -base64 16)
    sed -i.bak "s/POSTGRES_PASSWORD=CHANGE_ME/POSTGRES_PASSWORD=$PG_PASSWORD/" .env

    # Generate APPLE_HEALTH_WEBHOOK_TOKEN
    WEBHOOK_TOKEN=$(openssl rand -base64 32)
    sed -i.bak "s/APPLE_HEALTH_WEBHOOK_TOKEN=CHANGE_ME_RANDOM_STRING/APPLE_HEALTH_WEBHOOK_TOKEN=$WEBHOOK_TOKEN/" .env

    rm -f .env.bak

    echo -e "${GREEN}✓${NC} Generated random secrets"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Building Docker Images"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd docker
docker-compose build

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Starting Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

docker-compose up -d postgres
echo "Waiting for database to be ready..."
sleep 10

docker-compose up -d api
echo "Waiting for API to be ready..."
sleep 5

docker-compose up -d web

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ Personal Hub is running!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Access your hub at:"
echo "  • Web UI: http://localhost:3000"
echo "  • API:    http://localhost:8000"
echo "  • Docs:   http://localhost:8000/docs"
echo ""
echo "View logs:"
echo "  docker-compose logs -f"
echo ""
echo "Stop services:"
echo "  docker-compose down"
echo ""
echo "Next steps:"
echo "  1. Configure OAuth providers in .env"
echo "  2. Enable data sources you want to use"
echo "  3. Set up data source API keys"
echo "  4. Read docs/CONFIGURATION.md for details"
echo ""
