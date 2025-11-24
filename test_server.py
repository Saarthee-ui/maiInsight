"""Test if the running server is working correctly."""

import requests
import json

BASE_URL = "http://localhost:5000"

print("="*60)
print("Testing Running Server")
print("="*60)
print()

# Test 1: Health endpoint
print("1. Testing /api/health...")
try:
    response = requests.get(f"{BASE_URL}/api/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] Health check passed")
        print(f"   - Agent available: {data.get('agent_available')}")
        print(f"   - Agent has LLM: {data.get('agent_has_llm')}")
        print(f"   - Storage available: {data.get('storage_available')}")
    else:
        print(f"   [ERROR] Health check failed: {response.status_code}")
        print(f"   Response: {response.text}")
except requests.exceptions.ConnectionError:
    print("   [ERROR] Cannot connect to server. Is it running?")
    print("   Start server with: python run_backend.py")
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 2: Test endpoint
print("\n2. Testing /api/test...")
try:
    response = requests.get(f"{BASE_URL}/api/test", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] Test endpoint works")
        print(f"   - Message: {data.get('message')}")
    else:
        print(f"   [ERROR] Test endpoint failed: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] {e}")

# Test 3: Build chat endpoint
print("\n3. Testing /api/build/chat...")
try:
    response = requests.post(
        f"{BASE_URL}/api/build/chat",
        json={"message": "test", "session_id": "test123"},
        timeout=10
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   [OK] Build chat endpoint works")
        print(f"   - Success: {data.get('success')}")
        print(f"   - Stage: {data.get('stage')}")
    elif response.status_code == 503:
        data = response.json()
        print(f"   [ERROR] Agent not available: {data.get('error')}")
        print(f"   This means the server is running but agent is not initialized")
    else:
        print(f"   [ERROR] Build chat failed: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   [ERROR] {e}")

print("\n" + "="*60)
print("Test complete!")
print("="*60)

