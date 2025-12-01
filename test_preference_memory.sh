#!/bin/bash
# Test script for smart user preference memory

BASE_URL="http://localhost:5000"

echo "========================================="
echo "Testing Smart User Preference Memory"
echo "========================================="
echo ""

# Test 1: Create session and upload data
echo "Test 1: Creating session and generating sample data..."
SESSION1=$(curl -s -X POST "$BASE_URL/api/session/create" | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', ''))")
echo "Session 1 ID: $SESSION1"

curl -s -X POST "$BASE_URL/api/generate-sample-data" \
  -H "Content-Type: application/json" \
  -d '{"domain": "sales"}' > /dev/null
echo "Sample data generated"
echo ""

# Test 2: Ask about top products
echo "Test 2: Asking about top products..."
curl -s -X POST "$BASE_URL/api/chat-session" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION1\", \"message\": \"What are the top 3 products by sales?\"}" \
  > /tmp/response1.json

echo "Agent response:"
python3 -c "import json; data=json.load(open('/tmp/response1.json')); print(data.get('response', '')[:200])"
echo ""

# Test 3: Express preference
echo "Test 3: User expresses preference..."
curl -s -X POST "$BASE_URL/api/chat-session" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION1\", \"message\": \"Product B is my favorite product\"}" \
  > /tmp/response2.json

echo "Agent response:"
python3 -c "import json; data=json.load(open('/tmp/response2.json')); print(data.get('response', '')[:200])"
echo ""

# Wait for preference extraction
sleep 3

# Test 4: Check if preference was saved
echo "Test 4: Checking if preference was saved to memory..."
curl -s "$BASE_URL/api/memory?category=user_preference" | python3 -c "
import sys, json
data = json.load(sys.stdin)
memories = data.get('memories', [])
print(f'Found {len(memories)} user preferences')
for m in memories:
    if 'Product B' in m.get('content', '') or 'favorite' in m.get('content', '').lower():
        print(f'✓ Preference saved: {m.get(\"content\", \"\")[:100]}')
"
echo ""

# Test 5: New session - test cross-session retrieval
echo "Test 5: Creating new session to test cross-session retrieval..."
SESSION2=$(curl -s -X POST "$BASE_URL/api/session/create" | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', ''))")
echo "Session 2 ID: $SESSION2"
echo ""

# Test 6: Ask about favorite product in new session
echo "Test 6: Asking about 'my favorite product' in new session..."
curl -s -X POST "$BASE_URL/api/chat-session" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION2\", \"message\": \"Show me detailed stats for my favorite product\"}" \
  > /tmp/response3.json

echo "Agent response:"
python3 -c "import json; data=json.load(open('/tmp/response3.json')); print(data.get('response', '')[:300])"
echo ""

# Check if it mentions Product B
python3 -c "
import json
data = json.load(open('/tmp/response3.json'))
response = data.get('response', '')
if 'Product B' in response:
    print('✓ SUCCESS: Agent correctly recalled favorite product (Product B) from memory!')
else:
    print('✗ FAILED: Agent did not recall the favorite product')
"
echo ""

echo "========================================="
echo "Test completed!"
echo "========================================="
