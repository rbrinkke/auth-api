#!/bin/bash
set -e

API="http://localhost:8000"
PASS="C0mplex!P@ssw0rd#2025\$Secure"

docker compose exec -T redis redis-cli FLUSHALL 2>/dev/null || true
docker compose exec postgres psql -U activity_user -d activitydb -c "DELETE FROM activity.users WHERE email LIKE 'ultimate_%';" 2>/dev/null || true

EMAIL="debug_$(date +%s)@example.com"
cat > ./reg.json << JSON
{"email": "$EMAIL", "password": "$PASS"}
JSON

echo "Registering..."
R=$(curl -s -X POST "$API/auth/register" -H "Content-Type: application/json" -d @./reg.json)
echo "$R"

USER_ID=$(docker compose exec postgres psql -U activity_user -d activitydb -t -c "SELECT id FROM activity.users WHERE email='$EMAIL';" 2>/dev/null | xargs)
echo "User ID: $USER_ID"

CODE_KEY=$(docker compose exec -T redis redis-cli KEYS "2FA:*:verify" 2>/dev/null | head -1)
CODE=$(docker compose exec -T redis redis-cli GET "$CODE_KEY" 2>/dev/null)
echo "Code: $CODE"

cat > ./verify.json << JSON
{"user_id": "$USER_ID", "code": "$CODE"}
JSON

echo "Verifying..."
R=$(curl -s -X POST "$API/auth/verify-code" -H "Content-Type: application/json" -d @./verify.json)
echo "$R"

HASH_OLD=$(docker compose exec postgres psql -U activity_user -d activitydb -t -c "SELECT LEFT(hashed_password, 50) FROM activity.users WHERE id='$USER_ID';" 2>/dev/null | xargs)
echo "Old hash: $HASH_OLD"

cat > ./login.json << JSON
{"username": "$EMAIL", "password": "$PASS"}
JSON

echo "Logging in..."
R=$(curl -s -X POST "$API/auth/login" -H "Content-Type: application/json" -d @./login.json)
echo "$R"
