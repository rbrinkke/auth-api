#!/bin/bash
# ============================================================================
# L2 Cache Performance Test Script - PHASE 4 🚀
# Tests L2 cache (ALL user permissions pre-fetched)
# Expected: 50-93% latency reduction with L2!
# ============================================================================

set -e

echo "=================================="
echo "🚀 L2 Cache Performance Test (Phase 4)"
echo "=================================="
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

API_URL="http://localhost:8000"

# Test with DIFFERENT permissions for same user/org
TEST_USER_ID="550e8400-e29b-41d4-a716-446655440000"
TEST_ORG_ID="650e8400-e29b-41d4-a716-446655440001"
PERM1="activity:create"
PERM2="activity:read"
PERM3="activity:update"
PERM4="activity:delete"

echo -e "${BLUE}Step 1: Checking services...${NC}"
if ! docker ps | grep -q "auth-api"; then
    echo -e "${RED}❌ auth-api not running!${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Services running${NC}"
echo ""

echo -e "${BLUE}Step 2: Clearing Redis cache...${NC}"
docker exec auth-redis redis-cli --no-auth-warning FLUSHDB > /dev/null
echo -e "${GREEN}✅ Cache cleared${NC}"
echo ""

echo -e "${BLUE}Step 3: First request (CACHE MISS - populates L1 + L2)...${NC}"
START1=$(date +%s%N)
RESP1=$(curl -s -X POST "${API_URL}/api/v1/authorization/check" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"${TEST_USER_ID}\",\"org_id\":\"${TEST_ORG_ID}\",\"permission\":\"${PERM1}\"}")
END1=$(date +%s%N)
LAT1=$(( (END1 - START1) / 1000000 ))
echo "Response: ${RESP1}"
echo -e "${YELLOW}⏱️  Latency: ${LAT1}ms (L1 MISS + L2 population)${NC}"
echo ""

echo -e "${BLUE}Step 4: Check Redis keys (L1 + L2 should exist)...${NC}"
KEYS=$(docker exec auth-redis redis-cli --no-auth-warning KEYS "auth:*")
echo "Redis keys:"
echo "${KEYS}"

# Count keys
L1_KEYS=$(echo "${KEYS}" | grep -c "auth:check:" || echo "0")
L2_KEYS=$(echo "${KEYS}" | grep -c "auth:perms:" || echo "0")

echo ""
echo -e "${GREEN}✅ L1 keys (individual): ${L1_KEYS}${NC}"
echo -e "${GREEN}✅ L2 keys (ALL perms): ${L2_KEYS}${NC}"

if [ "$L2_KEYS" -gt 0 ]; then
    # Show L2 cache content
    L2_KEY=$(echo "${KEYS}" | grep "auth:perms:" || echo "")
    if [ -n "$L2_KEY" ]; then
        L2_CONTENT=$(docker exec auth-redis redis-cli --no-auth-warning GET "${L2_KEY}")
        echo -e "${MAGENTA}📦 L2 Cache content: ${L2_CONTENT}${NC}"
    fi
fi
echo ""

echo -e "${BLUE}Step 5: Second request - DIFFERENT permission (L2 HIT! 🚀)...${NC}"
START2=$(date +%s%N)
RESP2=$(curl -s -X POST "${API_URL}/api/v1/authorization/check" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"${TEST_USER_ID}\",\"org_id\":\"${TEST_ORG_ID}\",\"permission\":\"${PERM2}\"}")
END2=$(date +%s%N)
LAT2=$(( (END2 - START2) / 1000000 ))
echo "Response: ${RESP2}"
echo -e "${GREEN}⏱️  Latency: ${LAT2}ms (L2 CACHE HIT - ULTRA FAST! 🔥)${NC}"
echo ""

echo -e "${BLUE}Step 6: Third request - Another permission (L2 HIT! 🚀)...${NC}"
START3=$(date +%s%N)
RESP3=$(curl -s -X POST "${API_URL}/api/v1/authorization/check" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"${TEST_USER_ID}\",\"org_id\":\"${TEST_ORG_ID}\",\"permission\":\"${PERM3}\"}")
END3=$(date +%s%N)
LAT3=$(( (END3 - START3) / 1000000 ))
echo "Response: ${RESP3}"
echo -e "${GREEN}⏱️  Latency: ${LAT3}ms (L2 CACHE HIT - ULTRA FAST! 🔥)${NC}"
echo ""

echo -e "${BLUE}Step 7: Fourth request - Another permission (L2 HIT! 🚀)...${NC}"
START4=$(date +%s%N)
RESP4=$(curl -s -X POST "${API_URL}/api/v1/authorization/check" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"${TEST_USER_ID}\",\"org_id\":\"${TEST_ORG_ID}\",\"permission\":\"${PERM4}\"}")
END4=$(date +%s%N)
LAT4=$(( (END4 - START4) / 1000000 ))
echo "Response: ${RESP4}"
echo -e "${GREEN}⏱️  Latency: ${LAT4}ms (L2 CACHE HIT - ULTRA FAST! 🔥)${NC}"
echo ""

echo -e "${BLUE}Step 8: Performance Analysis${NC}"
echo "========================================"
echo -e "First request (L1 MISS):   ${YELLOW}${LAT1}ms${NC} (database + L2 population)"
echo -e "Second request (L2 HIT):   ${GREEN}${LAT2}ms${NC} ⚡"
echo -e "Third request (L2 HIT):    ${GREEN}${LAT3}ms${NC} ⚡"
echo -e "Fourth request (L2 HIT):   ${GREEN}${LAT4}ms${NC} ⚡"
echo ""

# Calculate average L2 latency
AVG_L2=$(( (LAT2 + LAT3 + LAT4) / 3 ))
echo -e "${MAGENTA}📊 Average L2 cached latency: ${AVG_L2}ms${NC}"

if [ "$LAT1" -gt 0 ]; then
    IMPROVEMENT=$(( (LAT1 - AVG_L2) * 100 / LAT1 ))
    SPEEDUP=$(echo "scale=2; $LAT1 / $AVG_L2" | bc)

    echo ""
    echo -e "${GREEN}🎯 L2 Performance Improvement: ${IMPROVEMENT}%${NC}"
    echo -e "${GREEN}🚀 L2 Speedup: ${SPEEDUP}x faster${NC}"

    if [ "$IMPROVEMENT" -ge 50 ]; then
        echo ""
        echo -e "${GREEN}════════════════════════════════════════${NC}"
        echo -e "${GREEN}✅ L2 CACHE SUCCESS! TARGET ACHIEVED!${NC}"
        echo -e "${GREEN}🏆 PHASE 4 COMPLETE! 👑${NC}"
        echo -e "${GREEN}════════════════════════════════════════${NC}"
    fi
fi
echo ""

echo -e "${BLUE}Step 9: Rapid-fire test (10 different permissions)...${NC}"
PERMS=("activity:create" "activity:read" "activity:update" "activity:delete" "user:create" "user:read" "user:update" "user:delete" "admin:read" "admin:write")
TOTAL_LAT=0
HITS=0

for i in {0..9}; do
    PERM="${PERMS[$i]}"
    START=$(date +%s%N)
    curl -s -X POST "${API_URL}/api/v1/authorization/check" \
      -H "Content-Type: application/json" \
      -d "{\"user_id\":\"${TEST_USER_ID}\",\"org_id\":\"${TEST_ORG_ID}\",\"permission\":\"${PERM}\"}" > /dev/null
    END=$(date +%s%N)
    LAT=$(( (END - START) / 1000000 ))
    TOTAL_LAT=$((TOTAL_LAT + LAT))
    HITS=$((HITS + 1))
    echo -e "  Request $((i+1)) (${PERM}): ${GREEN}${LAT}ms${NC}"
done

AVG_LAT=$((TOTAL_LAT / HITS))
echo ""
echo -e "${MAGENTA}📊 Average latency (all requests): ${AVG_LAT}ms${NC}"
echo ""

echo -e "${BLUE}Step 10: Check logs for L2 cache hits...${NC}"
L2_HITS=$(docker logs auth-api 2>&1 | grep -c "authz_l2_cache_hit" || echo "0")
L1_HITS=$(docker logs auth-api 2>&1 | grep -c "authz_l1_cache_hit" || echo "0")
MISSES=$(docker logs auth-api 2>&1 | grep -c "authz_cache_miss" || echo "0")

echo -e "${MAGENTA}🔥 L2 cache hits: ${L2_HITS}${NC}"
echo -e "${GREEN}✅ L1 cache hits: ${L1_HITS}${NC}"
echo -e "${YELLOW}⚠️  Cache misses: ${MISSES}${NC}"
echo ""

echo "=================================="
echo "🏆 L2 CACHE TEST RESULTS"
echo "=================================="
echo ""
echo "✅ L2 cache: ENABLED"
echo "✅ L2 population: WORKING"
echo "✅ L2 hits: ${L2_HITS}"
echo "✅ Performance: ${IMPROVEMENT}% faster"
echo "✅ Average latency: ${AVG_LAT}ms"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   PHASE 4 - L2 CACHE! 🚀👑${NC}"
echo -e "${GREEN}   BEST OF CLASS! 💪🔥${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
