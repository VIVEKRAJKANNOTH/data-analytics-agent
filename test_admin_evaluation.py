#!/usr/bin/env python3
"""
Test script to create sample evaluation data for the admin dashboard.
This script will:
1. Create a session
2. Upload a test dataset
3. Send queries to the analytics agent
4. Submit user feedback to create evaluation entries
5. Allow testing of the LLM-based evaluation feature
"""

import requests
import json
import time

API_URL = "http://localhost:5000/api"

def create_session():
    """Create a new session."""
    print("🔐 Creating new session...")
    
    response = requests.post(f"{API_URL}/session/create", json={})
    
    if response.status_code == 200:
        data = response.json()
        session_id = data['session_id']
        print(f"✅ Session created!")
        print(f"   Session ID: {session_id}")
        return session_id
    else:
        print(f"❌ Session creation failed: {response.text}")
        return None

def upload_dataset(session_id):
    """Upload the test dataset."""
    print("\n📤 Uploading test dataset...")
    
    with open('test_products.csv', 'rb') as f:
        files = {'file': ('test_products.csv', f, 'text/csv')}
        response = requests.post(f"{API_URL}/upload", files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Dataset uploaded successfully!")
        print(f"   Rows: {data.get('rows')}")
        print(f"   Columns: {', '.join(data.get('column_names', []))}")
        return True
    else:
        print(f"❌ Upload failed: {response.text}")
        return False

def ask_query(session_id, query):
    """Send a query to the analytics agent using session."""
    print(f"\n💬 Asking query: '{query}'")
    
    payload = {
        "message": query,
        "session_id": session_id
    }
    
    response = requests.post(f"{API_URL}/chat-session", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        agent_response = data.get('response', '')
        print(f"✅ Agent responded!")
        print(f"   Response: {agent_response[:150]}...")
        return {
            'user_message': query,
            'agent_response': agent_response
        }
    else:
        print(f"❌ Query failed: {response.text}")
        return None

def submit_feedback(session_id, message_index, user_message, agent_response, rating, feedback_text=None):
    """Submit user feedback for evaluation."""
    print(f"\n⭐ Submitting {rating} feedback...")
    
    payload = {
        "session_id": session_id,
        "message_index": message_index,
        "rating": rating,
        "feedback": feedback_text,
        "context": {
            "user_message": user_message,
            "agent_response": agent_response
        }
    }
    
    response = requests.post(f"{API_URL}/evaluate", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Feedback submitted!")
        print(f"   Evaluation ID: {data.get('evaluation_id', 'N/A')}")
        return data.get('evaluation_id')
    else:
        print(f"❌ Feedback submission failed: {response.text}")
        return None

def main():
    """Run the test scenario."""
    print("🚀 Starting Admin Dashboard Test Scenario")
    print("=" * 60)
    
    # Step 1: Create session
    session_id = create_session()
    if not session_id:
        print("Failed to create session. Exiting.")
        return
    
    time.sleep(1)
    
    # Step 2: Upload dataset
    if not upload_dataset(session_id):
        print("Failed to upload dataset. Exiting.")
        return
    
    time.sleep(1)
    
    # Step 3: Ask analytics queries
    test_queries = [
        {
            "query": "What is the total sales revenue across all products?",
            "rating": "positive",
            "feedback": "Great! The calculation was accurate and well-explained."
        },
        {
            "query": "Which product has the highest sales value?",
            "rating": "positive",
            "feedback": "Perfect answer with clear explanation of the results."
        },
        {
            "query": "Show me a breakdown of sales by product category",
            "rating": "negative",
            "feedback": "The analysis was correct but the visualization could be more detailed."
        },
        {
            "query": "What's the average quantity sold per product?",
            "rating": "positive",
            "feedback": "Excellent breakdown with good statistical analysis."
        },
        {
            "query": "Compare sales performance across different regions",
            "rating": "positive",
            "feedback": None  # Testing without feedback text
        }
    ]
    
    for i, test in enumerate(test_queries):
        print(f"\n{'='*60}")
        print(f"Test Query {i+1}/{len(test_queries)}")
        print(f"{'='*60}")
        
        # Ask the query
        result = ask_query(session_id, test["query"])
        if not result:
            continue
        
        time.sleep(1)
        
        # Submit feedback
        submit_feedback(
            session_id=session_id,
            message_index=i,
            user_message=result['user_message'],
            agent_response=result['agent_response'],
            rating=test["rating"],
            feedback_text=test["feedback"]
        )
        
        time.sleep(1)
    
    print("\n" + "="*60)
    print("✨ Test scenario completed!")
    print("="*60)
    print(f"\n📊 Summary:")
    print(f"   Session ID: {session_id}")
    print(f"   Evaluations created: {len(test_queries)}")
    print("\n📋 Next steps:")
    print("   1. Go to http://localhost:5173/admin")
    print("   2. You should see 5 evaluation entries")
    print("   3. Look for the 'Auto-Evaluate with AI' button")
    print("   4. Click it to trigger LLM-based evaluation")
    print("\n💡 The LLM evaluation will assess:")
    print("   - Correctness: How accurate is the response?")
    print("   - Helpfulness: How useful is the response?")
    print("   - Clarity: How clear and understandable is it?")
    print(f"\n🔗 Admin Dashboard: http://localhost:5173/admin")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

