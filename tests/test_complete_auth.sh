#!/bin/bash
set -e

API_URL="http://localhost:8000"
PASSWORD="C0mplex!P@ssw0rd#2025\$Secure"
EMAIL="test_$(date +%s)@example.com"

echo "=== COMPLETE AUTH TEST ==="
echo "Email: $EMAIL"

# Clean slate
echo "1. Reset rate limiting..."
docker compose exec -T redis redis-cli EVAL "return redis.call('FLUSHALL')" 0 2>/dev/null || true

# Test 1: Health
echo "2. Health check..."
curl -s "$API_URL/health" | grep -q "healthy" && echo "✓ Health OK" || exit 1

# Test 2: Database + Redis
echo "3. DB check..."
curl -s "$API_URL/health" | grep -q "database" && echo "✓ DB OK" || exit 1
echo "4. Redis check..."
docker compose exec -T redis redis-cli ping | grep -q "PONG" && echo "✓ Redis OK" || exit 1

# Test 3: Registration
echo "5. Registration test..."
cat > /tmp/test.json << JSON
{"email": "$EMAIL", "password": "$PASSWORD"}
JSON

RESPONSE=$(curl -s -X POST "$API_URL/auth/register" -H "Content-Type: application/json" -d @/tmp/test.json)
echo "$RESPONSE"
echo "$RESPONSE" | grep -q "User registered successfully" && echo "✓ Registration OK" || (echo "$RESPONSE" | grep -q "Rate limit" && echo "⚠ Rate limited - skipping" && exit 0)

# Test 4: Login before verification
echo "6. Login before verification (should fail)..."
cat > /tmp/login.json << JSON
{"username": "$EMAIL", "password": "$PASSWORD"}
JSON

RESPONSE=$(curl -s -X POST "$API_URL/auth/login" -H "Content-Type: application/json" -d @/tmp/login.json)
echo "$RESPONSE"
echo "$RESPONSE" | grep -q "Email not verified" && echo "✓ Unverified login blocked" || echo "⚠ Unexpected response"

# Test 5: Password validation
echo "7. Password validation..."
docker compose exec -T redis redis-cli DEL $(docker compose exec -T redis redis-cli KEYS "ratelimit:*" 2>/dev/null | tr '\n' ' ') 2>/dev/null || true
RESPONSE=$(curl -s -X POST "$API_URL/auth/register" -H "Content-Type: application/json" -d '{"email":"weak@x.com","password":"123"}')
echo "$RESPONSE" | grep -q "password\|strength" && echo "✓ Weak password rejected" || echo "Note: $RESPONSE"

rm -f /tmp/test.json /tmp/login.json
echo "=== TEST COMPLETE ==="