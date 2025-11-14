#!/bin/bash

# 🎯 100% MSW Endpoint Test Script
# Systematically tests ALL 41 backend endpoints
# Best-of-class validation for frontend developer 🏆

set -e  # Exit on error

# Color codes for beautiful output ✨
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Test statistics
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
START_TIME=$(date +%s)

# Test results array
declare -a FAILED_ENDPOINTS

echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${WHITE}🎯 100% MSW ENDPOINT TEST SUITE${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Testing ALL 41 backend endpoints systematically${NC}"
echo -e "${CYAN}Goal: Best-of-class 100% validation 🏆${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local url="$3"
    local data="$4"
    local expected_status="$5"
    local validation="$6"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -e "${BLUE}[$TOTAL_TESTS] Testing: ${WHITE}$name${NC}"
    echo -e "   ${CYAN}$method $url${NC}"

    # Build curl command
    local curl_cmd="curl -s -w '\n%{http_code}' -X $method"
    curl_cmd="$curl_cmd -H 'Content-Type: application/json'"

    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi

    curl_cmd="$curl_cmd 'http://localhost:3000$url'"

    # Execute request
    local response=$(eval $curl_cmd)
    local http_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n-1)

    # Validate status code
    if [ "$http_code" != "$expected_status" ]; then
        echo -e "   ${RED}❌ FAILED - Expected status $expected_status, got $http_code${NC}"
        echo -e "   ${RED}Response: $body${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        FAILED_ENDPOINTS+=("$name")
        return 1
    fi

    # Custom validation if provided
    if [ -n "$validation" ]; then
        if ! echo "$body" | grep -q "$validation"; then
            echo -e "   ${RED}❌ FAILED - Validation failed: $validation not found in response${NC}"
            echo -e "   ${RED}Response: $body${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            FAILED_ENDPOINTS+=("$name")
            return 1
        fi
    fi

    echo -e "   ${GREEN}✅ PASSED${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo ""
    return 0
}

# Start MSW server in background
echo -e "${YELLOW}🚀 Starting MSW server...${NC}"
cd /mnt/d/activity/auth-api/frontend-mocks

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 Installing dependencies...${NC}"
    npm install
fi

# Create simple server file if it doesn't exist
cat > test-server.mjs << 'EOF'
import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'
import { handlers } from './src/mocks/handlers.js'
import express from 'express'

const server = setupServer(...handlers)
await server.listen({ onUnhandledRequest: 'bypass' })

const app = express()
app.use(express.json())

// Proxy all requests through MSW
app.all('*', async (req, res) => {
  try {
    const url = `http://localhost:3000${req.path}`
    const response = await fetch(url, {
      method: req.method,
      headers: req.headers,
      body: req.method !== 'GET' && req.method !== 'HEAD' ? JSON.stringify(req.body) : undefined
    })
    const data = await response.json().catch(() => null)
    res.status(response.status).json(data)
  } catch (error) {
    res.status(500).json({ error: error.message })
  }
})

app.listen(3000, () => {
  console.log('MSW test server running on http://localhost:3000')
})
EOF

# Start server in background
node test-server.mjs > /dev/null 2>&1 &
SERVER_PID=$!

# Wait for server to start
echo -e "${YELLOW}⏳ Waiting for server to start...${NC}"
sleep 3

# Trap to ensure server is killed on exit
trap "kill $SERVER_PID 2>/dev/null || true" EXIT

echo -e "${GREEN}✓ Server started (PID: $SERVER_PID)${NC}"
echo ""

# ════════════════════════════════════════════════════════════════
# 1. AUTHENTICATION ENDPOINTS (11 tests)
# ════════════════════════════════════════════════════════════════

echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${WHITE}1️⃣  AUTHENTICATION ENDPOINTS (11 endpoints)${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo ""

test_endpoint \
    "POST /api/auth/register - Create new user" \
    "POST" \
    "/api/auth/register" \
    '{"email":"newuser@test.com","password":"Password123!"}' \
    "201" \
    "newuser@test.com"

test_endpoint \
    "POST /api/auth/verify-code - Verify registration code" \
    "POST" \
    "/api/auth/verify-code" \
    '{"email":"newuser@test.com","code":"123456"}' \
    "200" \
    "access_token"

test_endpoint \
    "POST /api/auth/login - Step 1 (password)" \
    "POST" \
    "/api/auth/login" \
    '{"email":"test@example.com","password":"Password123!"}' \
    "200" \
    "requires_code"

test_endpoint \
    "POST /api/auth/login - Step 2 (with code)" \
    "POST" \
    "/api/auth/login" \
    '{"email":"test@example.com","password":"Password123!","code":"123456"}' \
    "200" \
    "organizations"

test_endpoint \
    "POST /api/auth/login - Step 3 (with org)" \
    "POST" \
    "/api/auth/login" \
    '{"email":"test@example.com","password":"Password123!","code":"123456","org_id":"650e8400-e29b-41d4-a716-446655440001"}' \
    "200" \
    "access_token"

test_endpoint \
    "POST /api/auth/refresh - Refresh access token" \
    "POST" \
    "/api/auth/refresh" \
    '{"refresh_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}' \
    "200" \
    "access_token"

test_endpoint \
    "POST /api/auth/logout - Logout user" \
    "POST" \
    "/api/auth/logout" \
    '{"refresh_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}' \
    "200" \
    "success"

test_endpoint \
    "POST /api/auth/request-password-reset - Request password reset" \
    "POST" \
    "/api/auth/request-password-reset" \
    '{"email":"test@example.com"}' \
    "200" \
    "reset_token"

test_endpoint \
    "POST /api/auth/reset-password - Reset password with token" \
    "POST" \
    "/api/auth/reset-password" \
    '{"reset_token":"reset_abc123","code":"123456","new_password":"NewPassword123!"}' \
    "200" \
    "success"

test_endpoint \
    "POST /api/auth/2fa/setup - Setup 2FA" \
    "POST" \
    "/api/auth/2fa/setup" \
    '{}' \
    "200" \
    "qr_code"

test_endpoint \
    "POST /api/auth/2fa/verify - Verify 2FA code" \
    "POST" \
    "/api/auth/2fa/verify" \
    '{"code":"123456"}' \
    "200" \
    "backup_codes"

# ════════════════════════════════════════════════════════════════
# 2. OAUTH 2.0 ENDPOINTS (5 tests)
# ════════════════════════════════════════════════════════════════

echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${WHITE}2️⃣  OAUTH 2.0 ENDPOINTS (5 endpoints)${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo ""

test_endpoint \
    "GET /.well-known/oauth-authorization-server - Discovery" \
    "GET" \
    "/.well-known/oauth-authorization-server" \
    "" \
    "200" \
    "authorization_endpoint"

test_endpoint \
    "GET /oauth/authorize - Authorization request" \
    "GET" \
    "/oauth/authorize?response_type=code&client_id=test-client&redirect_uri=http://localhost:3000/callback&code_challenge=abc&code_challenge_method=S256" \
    "" \
    "200" \
    "consent"

test_endpoint \
    "POST /oauth/authorize - Consent submission" \
    "POST" \
    "/oauth/authorize" \
    '{"client_id":"test-client","redirect_uri":"http://localhost:3000/callback","scope":"read write","consent":true}' \
    "200" \
    "authorization_code"

test_endpoint \
    "POST /oauth/token - Token exchange (authorization_code)" \
    "POST" \
    "/oauth/token" \
    '{"grant_type":"authorization_code","code":"auth_abc123","redirect_uri":"http://localhost:3000/callback","client_id":"test-client","client_secret":"test-secret","code_verifier":"xyz"}' \
    "200" \
    "access_token"

test_endpoint \
    "POST /oauth/revoke - Revoke token" \
    "POST" \
    "/oauth/revoke" \
    '{"token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...","client_id":"test-client","client_secret":"test-secret"}' \
    "200" \
    "success"

# ════════════════════════════════════════════════════════════════
# 3. ORGANIZATION ENDPOINTS (7 tests)
# ════════════════════════════════════════════════════════════════

echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${WHITE}3️⃣  ORGANIZATION ENDPOINTS (7 endpoints)${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo ""

test_endpoint \
    "POST /api/auth/organizations - Create organization" \
    "POST" \
    "/api/auth/organizations" \
    '{"name":"New Org","description":"Test organization"}' \
    "201" \
    "org_id"

test_endpoint \
    "GET /api/auth/organizations - List user organizations" \
    "GET" \
    "/api/auth/organizations" \
    "" \
    "200" \
    "organizations"

test_endpoint \
    "GET /api/auth/organizations/{org_id} - Get organization details" \
    "GET" \
    "/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001" \
    "" \
    "200" \
    "name"

test_endpoint \
    "GET /api/auth/organizations/{org_id}/members - List members" \
    "GET" \
    "/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/members" \
    "" \
    "200" \
    "members"

test_endpoint \
    "POST /api/auth/organizations/{org_id}/members - Add member" \
    "POST" \
    "/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/members" \
    '{"email":"newmember@test.com","role":"member"}' \
    "201" \
    "success"

test_endpoint \
    "DELETE /api/auth/organizations/{org_id}/members/{user_id} - Remove member" \
    "DELETE" \
    "/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/members/550e8400-e29b-41d4-a716-446655440000" \
    "" \
    "200" \
    "success"

test_endpoint \
    "PATCH /api/auth/organizations/{org_id}/members/{user_id}/role - Update role" \
    "PATCH" \
    "/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/members/550e8400-e29b-41d4-a716-446655440000/role" \
    '{"role":"admin"}' \
    "200" \
    "success"

# ════════════════════════════════════════════════════════════════
# 4. GROUPS & RBAC ENDPOINTS (13 tests)
# ════════════════════════════════════════════════════════════════

echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${WHITE}4️⃣  GROUPS & RBAC ENDPOINTS (13 endpoints)${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo ""

test_endpoint \
    "POST /api/auth/organizations/{org_id}/groups - Create group" \
    "POST" \
    "/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/groups" \
    '{"name":"Developers","description":"Development team"}' \
    "201" \
    "group_id"

test_endpoint \
    "GET /api/auth/organizations/{org_id}/groups - List groups" \
    "GET" \
    "/api/auth/organizations/650e8400-e29b-41d4-a716-446655440001/groups" \
    "" \
    "200" \
    "groups"

test_endpoint \
    "GET /api/auth/groups/{group_id} - Get group details" \
    "GET" \
    "/api/auth/groups/750e8400-e29b-41d4-a716-446655440001" \
    "" \
    "200" \
    "name"

test_endpoint \
    "PATCH /api/auth/groups/{group_id} - Update group" \
    "PATCH" \
    "/api/auth/groups/750e8400-e29b-41d4-a716-446655440001" \
    '{"name":"Senior Developers","description":"Senior dev team"}' \
    "200" \
    "success"

test_endpoint \
    "DELETE /api/auth/groups/{group_id} - Delete group" \
    "DELETE" \
    "/api/auth/groups/750e8400-e29b-41d4-a716-446655440001" \
    "" \
    "200" \
    "success"

test_endpoint \
    "POST /api/auth/groups/{group_id}/members - Add member to group" \
    "POST" \
    "/api/auth/groups/750e8400-e29b-41d4-a716-446655440001/members" \
    '{"user_id":"550e8400-e29b-41d4-a716-446655440000"}' \
    "201" \
    "success"

test_endpoint \
    "DELETE /api/auth/groups/{group_id}/members/{user_id} - Remove member" \
    "DELETE" \
    "/api/auth/groups/750e8400-e29b-41d4-a716-446655440001/members/550e8400-e29b-41d4-a716-446655440000" \
    "" \
    "200" \
    "success"

test_endpoint \
    "GET /api/auth/groups/{group_id}/members - List group members" \
    "GET" \
    "/api/auth/groups/750e8400-e29b-41d4-a716-446655440001/members" \
    "" \
    "200" \
    "members"

test_endpoint \
    "POST /api/auth/groups/{group_id}/permissions - Grant permission" \
    "POST" \
    "/api/auth/groups/750e8400-e29b-41d4-a716-446655440001/permissions" \
    '{"permission_id":"850e8400-e29b-41d4-a716-446655440001"}' \
    "201" \
    "success"

test_endpoint \
    "DELETE /api/auth/groups/{group_id}/permissions/{permission_id} - Revoke permission" \
    "DELETE" \
    "/api/auth/groups/750e8400-e29b-41d4-a716-446655440001/permissions/850e8400-e29b-41d4-a716-446655440001" \
    "" \
    "200" \
    "success"

test_endpoint \
    "GET /api/auth/groups/{group_id}/permissions - List group permissions" \
    "GET" \
    "/api/auth/groups/750e8400-e29b-41d4-a716-446655440001/permissions" \
    "" \
    "200" \
    "permissions"

test_endpoint \
    "POST /api/auth/permissions - Create permission" \
    "POST" \
    "/api/auth/permissions" \
    '{"permission_string":"activity:create","description":"Create activities"}' \
    "201" \
    "permission_id"

test_endpoint \
    "GET /api/auth/permissions - List all permissions" \
    "GET" \
    "/api/auth/permissions" \
    "" \
    "200" \
    "permissions"

# ════════════════════════════════════════════════════════════════
# 5. AUTHORIZATION ENDPOINTS (4 tests)
# ════════════════════════════════════════════════════════════════

echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${WHITE}5️⃣  AUTHORIZATION ENDPOINTS (4 endpoints)${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo ""

test_endpoint \
    "POST /api/auth/authorize - THE CORE authorization check" \
    "POST" \
    "/api/auth/authorize" \
    '{"user_id":"550e8400-e29b-41d4-a716-446655440000","organization_id":"650e8400-e29b-41d4-a716-446655440001","permission":"activity:create"}' \
    "200" \
    "authorized"

test_endpoint \
    "POST /api/v1/authorization/check - Image-API compatible check" \
    "POST" \
    "/api/v1/authorization/check" \
    '{"user_id":"550e8400-e29b-41d4-a716-446655440000","organization_id":"650e8400-e29b-41d4-a716-446655440001","permission":"activity:create"}' \
    "200" \
    "authorized"

test_endpoint \
    "GET /api/auth/users/{user_id}/permissions - List user permissions" \
    "GET" \
    "/api/auth/users/550e8400-e29b-41d4-a716-446655440000/permissions?organization_id=650e8400-e29b-41d4-a716-446655440001" \
    "" \
    "200" \
    "permissions"

test_endpoint \
    "GET /api/auth/users/{user_id}/check-permission - Quick permission check" \
    "GET" \
    "/api/auth/users/550e8400-e29b-41d4-a716-446655440000/check-permission?organization_id=650e8400-e29b-41d4-a716-446655440001&permission=activity:create" \
    "" \
    "200" \
    "has_permission"

# ════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ════════════════════════════════════════════════════════════════

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${WHITE}📊 FINAL TEST RESULTS${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Total Tests:${NC}    ${WHITE}$TOTAL_TESTS${NC}"
echo -e "${GREEN}Passed:${NC}         ${WHITE}$PASSED_TESTS${NC}"
echo -e "${RED}Failed:${NC}         ${WHITE}$FAILED_TESTS${NC}"
echo -e "${YELLOW}Duration:${NC}       ${WHITE}${DURATION}s${NC}"
echo ""

# Calculate percentage
if [ $TOTAL_TESTS -gt 0 ]; then
    PERCENTAGE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo -e "${CYAN}Coverage:${NC}       ${WHITE}${PERCENTAGE}%${NC}"
    echo ""
fi

# Show failed endpoints
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "${RED}❌ FAILED ENDPOINTS:${NC}"
    for endpoint in "${FAILED_ENDPOINTS[@]}"; do
        echo -e "   ${RED}• $endpoint${NC}"
    done
    echo ""
fi

# Final verdict
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ 100% SUCCESS - ALL ENDPOINTS WORKING! 🎯🏆${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${WHITE}Frontend developer can proceed with confidence! 💪${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
    exit 0
else
    echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}❌ FAILURES DETECTED - NEEDS INVESTIGATION${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}Do NOT call frontend developer until all tests pass!${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
    exit 1
fi
