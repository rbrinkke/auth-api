#!/bin/bash
set -e

API="http://localhost:8000"
EMAIL="testuser@example.com"
PASS="SuperSecure2024Password"

echo "══════════════════════════════════════════════"
echo "  CREATE PERMANENT TEST USER"
echo "══════════════════════════════════════════════"
echo ""

# CLEAN OLD TESTUSER (if exists)
echo "[1/4] Clean old testuser (if exists)"
docker exec activity-postgres-db psql -U auth_api_user -d activitydb -c "DELETE FROM activity.users WHERE email='$EMAIL';" 2>/dev/null || true
docker compose exec -T redis redis-cli DEL "verify_token:*" 2>/dev/null || true
echo "      ✓ Cleaned"
echo ""

# REGISTER
echo "[2/4] Register: $EMAIL"
cat > ./testuser-reg.json << JSON
{"email": "$EMAIL", "password": "$PASS"}
JSON
R=$(curl -s -X POST "$API/api/auth/register" -H "Content-Type: application/json" -d @./testuser-reg.json)
echo "$R" | grep -q "success" || (echo "Registration failed: $R" && exit 1)
VERIFICATION_TOKEN=$(echo "$R" | grep -o '"verification_token":"[^"]*' | cut -d'"' -f4)
echo "      ✓ Registered"
echo ""

# GET VERIFICATION CODE
echo "[3/4] Get verification code"
CODE_DATA=$(docker compose exec -T redis redis-cli GET "verify_token:$VERIFICATION_TOKEN" 2>/dev/null)
CODE=$(echo "$CODE_DATA" | cut -d':' -f2)
echo "      ✓ Code: $CODE"
echo ""

# VERIFY EMAIL
echo "[4/4] Verify email"
cat > ./testuser-verify.json << JSON
{"verification_token": "$VERIFICATION_TOKEN", "code": "$CODE"}
JSON
R=$(curl -s -X POST "$API/api/auth/verify-code" -H "Content-Type: application/json" -d @./testuser-verify.json)
echo "$R" | grep -qi "verified\|success" || (echo "Verify failed: $R" && exit 1)
echo "      ✓ Email verified"
echo ""

# CLEANUP TEMP FILES
rm -f ./testuser-*.json

echo "══════════════════════════════════════════════"
echo "  ✅ TEST USER CREATED & VERIFIED!"
echo "══════════════════════════════════════════════"
echo ""
echo "LOGIN CREDENTIALS:"
echo "  Email:    $EMAIL"
echo "  Password: $PASS"
echo ""
echo "This user is PERMANENT (not deleted)."
echo "Use these credentials in your mobile app!"
echo ""
