#!/bin/bash
# Test script for session and memory management features

BASE_URL="http://localhost:5000"

echo "========================================="
echo "Testing Session and Memory Features"
echo "========================================="
echo ""

# Test 1: Create a session
echo "Test 1: Creating a new session..."
SESSION_RESPONSE=$(curl -s -X POST "$BASE_URL/api/session/create" \
  -H "Content-Type: application/json" \
  -d '{"metadata": {"test": "demo"}}')
echo "Response: $SESSION_RESPONSE"

SESSION_ID=$(echo $SESSION_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('session_id', ''))")
echo "Session ID: $SESSION_ID"
echo ""

# Test 2: Get session info
echo "Test 2: Getting session information..."
curl -s "$BASE_URL/api/session/$SESSION_ID" | python3 -m json.tool
echo ""

# Test 3: Generate sample data
echo "Test 3: Generating sample data..."
curl -s -X POST "$BASE_URL/api/generate-sample-data" \
  -H "Content-Type: application/json" \
  -d '{"domain": "sales"}' | python3 -m json.tool
echo ""

# Test 4: Chat with session
echo "Test 4: Chatting with session - Question 1..."
curl -s -X POST "$BASE_URL/api/chat-session" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"What are the top 5 products by total sales?\"}" \
  > /tmp/chat_response_1.json

echo "Response saved to /tmp/chat_response_1.json"
python3 -c "import json; data=json.load(open('/tmp/chat_response_1.json')); print('Success:', data.get('success')); print('Response:', data.get('response', '')[:200])"
echo ""

# Test 5: Chat again in same session
echo "Test 5: Chatting with session - Question 2..."
curl -s -X POST "$BASE_URL/api/chat-session" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"message\": \"Show me the sales trend over time\"}" \
  > /tmp/chat_response_2.json

echo "Response saved to /tmp/chat_response_2.json"
python3 -c "import json; data=json.load(open('/tmp/chat_response_2.json')); print('Success:', data.get('success')); print('Response:', data.get('response', '')[:200])"
echo ""

# Test 6: Get session history
echo "Test 6: Getting session conversation history..."
curl -s "$BASE_URL/api/session/$SESSION_ID" | python3 -c "import sys, json; data=json.load(sys.stdin); print('Messages in history:', len(data.get('session', {}).get('conversation_history', [])))"
echo ""

# Test 7: Get memories
echo "Test 7: Getting memories from memory bank..."
curl -s "$BASE_URL/api/memory?limit=10" | python3 -m json.tool
echo ""

# Test 8: Add a manual memory
echo "Test 8: Adding a manual memory..."
curl -s -X POST "$BASE_URL/api/memory" \
  -H "Content-Type: application/json" \
  -d '{"content": "User prefers visualizations with dark theme", "category": "user_preference", "metadata": {"session_id": "demo"}}' | python3 -m json.tool
echo ""

# Test 9: Get memory summary
echo "Test 9: Getting memory bank summary..."
curl -s "$BASE_URL/api/memory/summary" | python3 -m json.tool
echo ""

# Test 10: Delete session
echo "Test 10: Deleting session..."
curl -s -X DELETE "$BASE_URL/api/session/$SESSION_ID" | python3 -m json.tool
echo ""

echo "========================================="
echo "All tests completed!"
echo "========================================="
