#!/bin/bash
# Quick manual test of preference memory

SESSION_ID="a7892b39-09e1-46ef-9681-7f591ecf99f9"
BASE_URL="http://localhost:5000"

echo "=== Test 1: Ask about top products ==="
curl -s -X POST "$BASE_URL/api/chat-session" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"What are the top 3 products by sales?\"}" \
  | python3 -c "import json, sys; d=json.load(sys.stdin); print(d.get('response', '')[:150])"
echo -e "\n"

sleep 2

echo "=== Test 2: Express preference ==="
curl -s -X POST "$BASE_URL/api/chat-session" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"Product B is my favorite product\"}" \
  | python3 -c "import json, sys; d=json.load(sys.stdin); print(d.get('response', ''))"
echo -e "\n"

sleep 5

echo "=== Test 3: Check memory ==="
curl -s "$BASE_URL/api/memory?category=user_preference" \
  | python3 -c "import json, sys; d=json.load(sys.stdin); print(f\"Found {len(d.get('memories', []))} preferences\"); [print(f\"  - {m['content']}\") for m in d.get('memories', [])]"
echo -e "\n"

echo "=== Test 4: Create new session ==="
SESSION2=$(curl -s -X POST "$BASE_URL/api/session/create" -H "Content-Type: application/json" -d '{}' | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', ''))")
echo "New session: $SESSION2"
echo ""

sleep 2

echo "=== Test 5: Ask about favorite in new session ==="
curl -s -X POST "$BASE_URL/api/chat-session" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION2\", \"message\": \"Show me stats for my favorite product\"}" \
  | python3 -c "import json, sys; d=json.load(sys.stdin); r=d.get('response', ''); print(r[:300]); print('\n✓ SUCCESS!' if 'Product B' in r else '\n✗ FAILED')"
