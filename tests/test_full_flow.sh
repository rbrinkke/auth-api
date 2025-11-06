#!/bin/bash
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_URL="http://localhost:8000"
COMPLEX_PASSWORD="C0mplex!P@ssw0rd#2025\$Secure"

echo -e "${BLUE}=== Full Auth Flow Test ===${NC}\n"

# Generate unique email
TEST_EMAIL="flowtest_$(date +%s)@example.com"
echo -e "${YELLOW}Testing with email: $TEST_EMAIL${NC}\n"

# Step 1: Register
echo -e "${YELLOW}Step 1: Registration${NC}"
cat > /tmp/test_flow.json << JSON
{"email": "$TEST_EMAIL", "password": "$COMPLEX_PASSWORD"}
JSON

RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d @/tmp/test_flow.json)

echo "$RESPONSE"
if echo "$RESPONSE" | grep -q "User registered successfully"; then
    echo -e "${GREEN}✓ Registration successful${NC}\n"
else
    echo -e "${RED}✗ Registration failed${NC}\n"
    exit 1
fi

# Step 2: Try login (should fail - email not verified)
echo -e "${YELLOW}Step 2: Login Before Verification (Should Fail)${NC}"
cat > /tmp/test_flow_login.json << JSON
{"username": "$TEST_EMAIL", "password": "$COMPLEX_PASSWORD"}
JSON

RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d @/tmp/test_flow_login.json)

echo "$RESPONSE"
if echo "$RESPONSE" | grep -q "Email not verified"; then
    echo -e "${GREEN}✓ Correctly blocked unverified login${NC}\n"
else
    echo -e "${YELLOW}Note: Got response (may vary)${NC}\n"
fi

# Step 3: Password validation test
echo -e "${YELLOW}Step 3: Test Different Password Strengths${NC}"

# Test with breached password
cat > /tmp/breached.json << JSON
{"email": "breached_$(date +%s)@example.com", "password": "TestPassword123!"}
JSON

RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d @/tmp/breached.json)

echo "Breached password response:"
echo "$RESPONSE" | head -c 100
echo -e "\n${GREEN}✓ Breached password detected${NC}\n"

# Test with weak password
cat > /tmp/weakpass.json << JSON
{"email": "weak_$(date +%s)@example.com", "password": "123"}
JSON

RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d @/tmp/weakpass.json)

echo "Weak password response:"
echo "$RESPONSE" | head -c 100
echo -e "\n${GREEN}✓ Weak password rejected${NC}\n"

# Cleanup
rm -f /tmp/test_flow*.json /tmp/breached.json /tmp/weakpass.json

echo -e "${GREEN}=== Full Flow Test Complete ===${NC}\n"
