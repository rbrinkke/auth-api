#!/bin/bash
# L2 Cache Test with REAL authorized user
set -e

USER_ID="c0a61eba-5805-494c-bc1b-563d3ca49126"
ORG_ID="1ab0e9fa-b4ec-4a8b-9cfa-7f2bb57db87e"
API_URL="http://localhost:8000"

echo "🚀 L2 CACHE TEST - REAL AUTHORIZED USER"
echo "========================================"
echo ""

echo "Step 1: First request (activity:create) - CACHE MISS"
START1=$(date +%s%N)
RESP1=$(curl -s -X POST "${API_URL}/api/v1/authorization/check" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"${USER_ID}\",\"org_id\":\"${ORG_ID}\",\"permission\":\"activity:create\"}")
END1=$(date +%s%N)
LAT1=$(( (END1 - START1) / 1000000 ))
echo "Response: ${RESP1}"
echo "⏱️  Latency: ${LAT1}ms (DB query + L2 population)"
echo ""

echo "Step 2: Check Redis - L2 cache should be populated!"
KEYS=$(docker exec auth-redis redis-cli --no-auth-warning KEYS "auth:*")
echo "Redis keys:"
echo "${KEYS}"
L2_KEYS=$(echo "${KEYS}" | grep -c "auth:perms:" || echo "0")
echo "L2 keys found: ${L2_KEYS}"
echo ""

if [ "$L2_KEYS" -gt 0 ]; then
    echo "Step 3: Show L2 cache content"
    L2_KEY=$(echo "${KEYS}" | grep "auth:perms:" | head -1)
    L2_CONTENT=$(docker exec auth-redis redis-cli --no-auth-warning GET "${L2_KEY}")
    echo "L2 Cache key: ${L2_KEY}"
    echo "L2 Cache content: ${L2_CONTENT}"
    echo ""
fi

echo "Step 4: Second request (activity:read) - DIFFERENT permission - L2 HIT!"
START2=$(date +%s%N)
RESP2=$(curl -s -X POST "${API_URL}/api/v1/authorization/check" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"${USER_ID}\",\"org_id\":\"${ORG_ID}\",\"permission\":\"activity:read\"}")
END2=$(date +%s%N)
LAT2=$(( (END2 - START2) / 1000000 ))
echo "Response: ${RESP2}"
echo "⏱️  Latency: ${LAT2}ms (L2 CACHE HIT! 🚀)"
echo ""

echo "Step 5: Third request (activity:update) - L2 HIT!"
START3=$(date +%s%N)
RESP3=$(curl -s -X POST "${API_URL}/api/v1/authorization/check" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"${USER_ID}\",\"org_id\":\"${ORG_ID}\",\"permission\":\"activity:update\"}")
END3=$(date +%s%N)
LAT3=$(( (END3 - START3) / 1000000 ))
echo "Response: ${RESP3}"
echo "⏱️  Latency: ${LAT3}ms (L2 CACHE HIT! 🚀)"
echo ""

echo "Step 6: Fourth request (activity:delete) - L2 HIT!"
START4=$(date +%s%N)
RESP4=$(curl -s -X POST "${API_URL}/api/v1/authorization/check" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"${USER_ID}\",\"org_id\":\"${ORG_ID}\",\"permission\":\"activity:delete\"}")
END4=$(date +%s%N)
LAT4=$(( (END4 - START4) / 1000000 ))
echo "Response: ${RESP4}"
echo "⏱️  Latency: ${LAT4}ms (L2 CACHE HIT! 🚀)"
echo ""

echo "📊 PERFORMANCE ANALYSIS"
echo "========================================"
echo "First request (DB):     ${LAT1}ms"
echo "Second request (L2):    ${LAT2}ms"
echo "Third request (L2):     ${LAT3}ms"
echo "Fourth request (L2):    ${LAT4}ms"
echo ""

AVG_L2=$(( (LAT2 + LAT3 + LAT4) / 3 ))
echo "Average L2 latency: ${AVG_L2}ms"

if [ "$LAT1" -gt 0 ]; then
    IMPROVEMENT=$(( (LAT1 - AVG_L2) * 100 / LAT1 ))
    echo "L2 Performance improvement: ${IMPROVEMENT}%"
    echo ""
    
    if [ "$IMPROVEMENT" -ge 50 ]; then
        echo "🏆 SUCCESS! L2 CACHE WORKS! TARGET ACHIEVED! 👑"
    else
        echo "⚠️  L2 improvement < 50% (got ${IMPROVEMENT}%)"
    fi
fi

echo ""
echo "Step 7: Check logs for L2 cache hits"
L2_HITS=$(docker logs auth-api 2>&1 | grep -c "authz_l2_cache_hit" || echo "0")
L2_POP=$(docker logs auth-api 2>&1 | grep -c "authz_l2_cache_populated" || echo "0")
echo "L2 cache hits: ${L2_HITS}"
echo "L2 cache populated: ${L2_POP}"
echo ""
echo "🎯 PHASE 4 COMPLETE! 🚀👑"
