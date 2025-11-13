#!/bin/bash
# Force rebuild auth-api with NO cache
set -e

echo "=== Force Rebuild Auth-API ==="
echo ""

echo "1️⃣  Stopping container..."
docker compose stop auth-api

echo "2️⃣  Removing container..."
docker compose rm -f auth-api

echo "3️⃣  Removing image..."
docker rmi -f auth-api-auth-api 2>/dev/null || true

echo "4️⃣  Pruning build cache..."
docker builder prune -f

echo "5️⃣  Building with NO cache..."
docker compose build --no-cache --progress=plain auth-api

echo "6️⃣  Starting container..."
docker compose up -d auth-api

echo "7️⃣  Waiting for startup..."
sleep 15

echo "8️⃣  Container status:"
docker compose ps auth-api

echo ""
echo "✅ Rebuild complete!"
