#!/bin/bash
#
# Start the Auth API Testing UI as a standalone Docker container
#

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🧪 Auth API Testing UI - Standalone Container          ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if auth-api is running
echo -e "${YELLOW}Checking dependencies...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Auth API (port 8000) is running${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Auth API (port 8000) is not responding${NC}"
    echo "   The testing UI will start, but won't be able to test the API."
    echo "   To start auth-api:"
    echo "   cd /mnt/d/activity && ./scripts/start-infra.sh"
    echo "   cd auth-api && docker compose up -d"
    echo ""
fi

# Check if network exists
if ! docker network ls | grep -q activity-network; then
    echo -e "${YELLOW}⚠️  Creating activity-network...${NC}"
    docker network create activity-network
    echo -e "${GREEN}✅ Network created${NC}"
fi

# Navigate to testing_ui directory
cd "$(dirname "$0")"

# Build and start the container
echo -e "${YELLOW}Building and starting testing UI container...${NC}"
docker compose up -d --build

# Wait for container to be healthy
echo -e "${YELLOW}Waiting for container to be ready...${NC}"
sleep 3

# Check health
if curl -s http://localhost:8099/health > /dev/null 2>&1; then
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ Auth API Testing UI is running!                      ║${NC}"
    echo -e "${GREEN}╟───────────────────────────────────────────────────────────╢${NC}"
    echo -e "${GREEN}║  🌐 Testing UI:  http://localhost:8099/test/auth         ║${NC}"
    echo -e "${GREEN}║  💚 Health:      http://localhost:8099/health            ║${NC}"
    echo -e "${GREEN}║  📚 API Docs:    http://localhost:8099/docs              ║${NC}"
    echo -e "${GREEN}╟───────────────────────────────────────────────────────────╢${NC}"
    echo -e "${GREEN}║  🎯 Target API:  http://localhost:8000 (auth-api)        ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Commands:"
    echo "  • View logs:    docker logs -f auth-testing-ui"
    echo "  • Stop:         docker compose down"
    echo "  • Rebuild:      docker compose build && docker compose restart"
    echo ""
else
    echo -e "${YELLOW}⚠️  Container started but health check failed.${NC}"
    echo "   Check logs: docker logs auth-testing-ui"
fi
