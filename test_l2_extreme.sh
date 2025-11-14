#!/bin/bash
# L2 Cache EXTREME Performance Test
set -e

USER_ID="c0a61eba-5805-494c-bc1b-563d3ca49126"
ORG_ID="1ab0e9fa-b4ec-4a8b-9cfa-7f2bb57db87e"
API_URL="http://localhost:8000"

echo "🚀 L2 CACHE EXTREME TEST - 20 RAPID REQUESTS"
echo "=============================================="
echo ""

# Clear cache
docker exec auth-redis redis-cli --no-auth-warning FLUSHDB > /dev/null
echo "✅ Cache cleared"
echo ""

# First request - MISS (populates L2)
echo "First request (CACHE MISS - populates L2):"
START=$(date +%s%N)
curl -s -X POST "${API_URL}/api/v1/authorization/check" \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"${USER_ID}\",\"org_id\":\"${ORG_ID}\",\"permission\":\"activity:create\"}" > /dev/null
END=$(date +%s%N)
LAT=$(( (END - START) / 1000000 ))
FIRST_LAT=$LAT
echo "⏱️  ${LAT}ms (DB + L2 population)"
echo ""

# 19 more requests - ALL L2 HITS
echo "Next 19 requests (ALL L2 HITS! 🚀):"
PERMS=("activity:read" "activity:update" "activity:delete" "activity:create" "activity:read" "activity:update" "activity:delete" "activity:create" "activity:read" "activity:update" "activity:delete" "activity:create" "activity:read" "activity:update" "activity:delete" "activity:create" "activity:read" "activity:update" "activity:delete")

TOTAL_LAT=0
COUNT=0

for i in "${!PERMS[@]}"; do
    PERM="${PERMS[$i]}"
    START=$(date +%s%N)
    curl -s -X POST "${API_URL}/api/v1/authorization/check" \
      -H "Content-Type: application/json" \
      -d "{\"user_id\":\"${USER_ID}\",\"org_id\":\"${ORG_ID}\",\"permission\":\"${PERM}\"}" > /dev/null
    END=$(date +%s%N)
    LAT=$(( (END - START) / 1000000 ))
    TOTAL_LAT=$((TOTAL_LAT + LAT))
    COUNT=$((COUNT + 1))
    echo "  Request $((i+2)): ${LAT}ms"
done

AVG_L2=$((TOTAL_LAT / COUNT))

echo ""
echo "📊 EXTREME PERFORMANCE ANALYSIS"
echo "=============================================="
echo "First request (DB):           ${FIRST_LAT}ms"
echo "Average L2 cached (19 reqs):  ${AVG_L2}ms"
echo ""

IMPROVEMENT=$(( (FIRST_LAT - AVG_L2) * 100 / FIRST_LAT ))
SPEEDUP=$(echo "scale=2; $FIRST_LAT / $AVG_L2" | bc)

echo "🎯 L2 Performance improvement: ${IMPROVEMENT}%"
echo "🚀 L2 Speedup: ${SPEEDUP}x faster"
echo ""

if [ "$IMPROVEMENT" -ge 50 ]; then
    echo "════════════════════════════════════════"
    echo "✅ L2 CACHE SUCCESS! TARGET ACHIEVED!"
    echo "🏆 PHASE 4 COMPLETE! 👑"
    echo "════════════════════════════════════════"
else
    echo "⚠️  Target: 50%+, Got: ${IMPROVEMENT}%"
fi

echo ""
echo "Checking logs..."
L2_HITS=$(docker logs auth-api 2>&1 | tail -100 | grep -c "authz_l2_cache_hit" || echo "0")
L2_POP=$(docker logs auth-api 2>&1 | tail -100 | grep -c "authz_l2_cache_populated" || echo "0")
echo "L2 cache hits (recent): ${L2_HITS}"
echo "L2 cache populated: ${L2_POP}"
