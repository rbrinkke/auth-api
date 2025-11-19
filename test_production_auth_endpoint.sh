#!/bin/bash
# Test script for Production Auth Endpoint (/api/v1/authorization/check)
# Tests 4 key scenarios:
# 1. Removal of test-mode hardcoded users
# 2. HTTP 200 response for denied access (no 403)
# 3. Strict UUID validation (no auto-conversion)
# 4. Successful authorization with group membership (REQUIRES: setup_real_test_data.sql)

set -e

API_URL="http://localhost:8000"
AUTH_ENDPOINT="$API_URL/api/v1/authorization/check"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "Testing Production Auth Endpoint"
echo "========================================"
echo ""

# Function to test and verify response
test_endpoint() {
    local test_name="$1"
    local payload="$2"
    local expected_status="$3"
    local expected_allowed="$4"
    local expected_reason_contains="$5"
    local expected_group="${6:-}"  # Optional: expected group name

    echo -e "${YELLOW}Test: $test_name${NC}"
    echo "Payload: $payload"

    # Make request and capture response
    response=$(curl -s -w "\n%{http_code}" -X POST "$AUTH_ENDPOINT" \
        -H "Content-Type: application/json" \
        -d "$payload")

    # Extract HTTP status code (last line)
    http_status=$(echo "$response" | tail -n 1)

    # Extract response body (all but last line)
    body=$(echo "$response" | head -n -1)

    # Extract allowed field (handle boolean properly)
    allowed=$(echo "$body" | jq -r '.allowed')
    reason=$(echo "$body" | jq -r '.reason // "null"')
    groups=$(echo "$body" | jq -r '.groups // []')

    echo "HTTP Status: $http_status"
    echo "Response Body: $body"
    echo ""

    # Validate HTTP status
    if [ "$http_status" != "$expected_status" ]; then
        echo -e "${RED}❌ FAILED: Expected HTTP $expected_status, got $http_status${NC}"
        echo ""
        return 1
    fi

    # Validate allowed field
    if [ "$allowed" != "$expected_allowed" ]; then
        echo -e "${RED}❌ FAILED: Expected allowed=$expected_allowed, got allowed=$allowed${NC}"
        echo ""
        return 1
    fi

    # Validate reason contains expected text (if provided)
    if [ -n "$expected_reason_contains" ]; then
        if [[ ! "$reason" =~ $expected_reason_contains ]]; then
            echo -e "${RED}❌ FAILED: Expected reason to contain '$expected_reason_contains', got '$reason'${NC}"
            echo ""
            return 1
        fi
    fi

    # Validate groups field (if expected_group provided)
    if [ -n "$expected_group" ]; then
        if [ "$groups" == "[]" ] || [ "$groups" == "null" ]; then
            echo -e "${RED}❌ FAILED: Expected groups to contain data, got empty/null${NC}"
            echo ""
            return 1
        fi

        if [[ ! "$groups" =~ $expected_group ]]; then
            echo -e "${RED}❌ FAILED: Expected group '$expected_group' in groups, got: $groups${NC}"
            echo ""
            return 1
        fi

        echo -e "${GREEN}✓ Group '$expected_group' verified in response${NC}"
    fi

    echo -e "${GREEN}✅ PASSED${NC}"
    echo ""
    return 0
}

echo "========================================"
echo "TEST 1: Hardcoded Test Users Removed"
echo "========================================"
echo "OLD: System accepted 'test-user' / 'test-org'"
echo "NEW: Must return allowed: false (no DB entry)"
echo ""

test_endpoint \
    "Test with old hardcoded test-user credentials" \
    '{
        "user_id": "test-user",
        "org_id": "test-org",
        "permission": "image:upload"
    }' \
    "200" \
    "false" \
    "Invalid ID format"

echo "========================================"
echo "TEST 2: HTTP 200 for Denied Access"
echo "========================================"
echo "OLD: Returned HTTP 403 Forbidden"
echo "NEW: Returns HTTP 200 with allowed: false"
echo ""

# Use a valid UUID format but non-existent user
test_endpoint \
    "Test with valid UUID but no database entry" \
    '{
        "user_id": "00000000-0000-0000-0000-000000000001",
        "org_id": "00000000-0000-0000-0000-000000000002",
        "permission": "image:upload"
    }' \
    "200" \
    "false" \
    ""

echo "========================================"
echo "TEST 3: Strict UUID Validation"
echo "========================================"
echo "OLD: Auto-converted invalid strings to MD5"
echo "NEW: Rejects with 'Invalid ID format'"
echo ""

test_endpoint \
    "Test with invalid org_id (non-UUID string)" \
    '{
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "org_id": "foute-string",
        "permission": "image:upload"
    }' \
    "200" \
    "false" \
    "Invalid ID format"

test_endpoint \
    "Test with invalid user_id (non-UUID string)" \
    '{
        "user_id": "mijn-organisatie",
        "org_id": "550e8400-e29b-41d4-a716-446655440000",
        "permission": "image:upload"
    }' \
    "200" \
    "false" \
    "Invalid ID format"

test_endpoint \
    "Test with both IDs invalid" \
    '{
        "user_id": "invalid-user",
        "org_id": "invalid-org",
        "permission": "image:upload"
    }' \
    "200" \
    "false" \
    "Invalid ID format"

echo "========================================"
echo "BONUS TEST: Valid UUID Format"
echo "========================================"
echo "Verify that valid UUIDs are accepted (even if not in DB)"
echo ""

test_endpoint \
    "Test with valid UUIDs (should process, return allowed: false)" \
    '{
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "org_id": "650e8400-e29b-41d4-a716-446655440001",
        "permission": "image:upload"
    }' \
    "200" \
    "false" \
    ""

echo "========================================"
echo "TEST 4: Successful Authorization"
echo "========================================"
echo "Test positive case with real database data"
echo "REQUIRES: setup_real_test_data.sql to be run first!"
echo ""

test_endpoint \
    "Test with authorized user (should return allowed: true)" \
    '{
        "user_id": "22222222-2222-2222-2222-222222222222",
        "org_id": "11111111-1111-1111-1111-111111111111",
        "permission": "image:upload"
    }' \
    "200" \
    "true" \
    "permission" \
    "Content Creators"

echo "========================================"
echo "TEST SUMMARY"
echo "========================================"
echo -e "${GREEN}All production auth endpoint tests passed!${NC}"
echo ""
echo "Validated:"
echo "✅ 1. Hardcoded test users removed (test-user rejected)"
echo "✅ 2. HTTP 200 returned for denied access (no 403)"
echo "✅ 3. Strict UUID validation (invalid strings rejected)"
echo "✅ 4. Successful authorization with group membership verification"
echo ""
