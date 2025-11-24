"""Verify the server is running correctly."""

import requests
import sys
import time

BASE_URL = "http://localhost:5000"

def test_server():
    print("="*60)
    print("Server Verification")
    print("="*60)
    print()
    
    # Test 1: Check if server is running
    print("1. Checking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}/api/test", timeout=2)
        if response.status_code == 200:
            print("   [OK] Server is running")
        else:
            print(f"   [ERROR] Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("   [ERROR] Cannot connect to server!")
        print("   The server is not running or not accessible.")
        print()
        print("   SOLUTION:")
        print("   1. Make sure the server is running:")
        print("      python run_backend.py")
        print("   2. Wait for the startup messages to appear")
        print("   3. Look for: '[SUCCESS] BuildSummaryAgent is ready!'")
        return False
    except Exception as e:
        print(f"   [ERROR] {e}")
        return False
    
    # Test 2: Health check
    print("\n2. Testing /api/health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("   [OK] Health endpoint works")
            print(f"   - Agent available: {data.get('agent_available')}")
            print(f"   - Agent has LLM: {data.get('agent_has_llm')}")
            print(f"   - Storage available: {data.get('storage_available')}")
            
            if not data.get('agent_available'):
                print("\n   [CRITICAL] Agent is not available!")
                print("   The server needs to be restarted.")
                return False
        else:
            print(f"   [ERROR] Health check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   [ERROR] {e}")
        return False
    
    # Test 3: Build chat
    print("\n3. Testing /api/build/chat endpoint...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/build/chat",
            json={"message": "test", "session_id": "verify123"},
            timeout=60  # Increased timeout to 60 seconds for LLM calls
        )
        if response.status_code == 200:
            data = response.json()
            print("   [OK] Build chat endpoint works")
            print(f"   - Success: {data.get('success')}")
            print(f"   - Stage: {data.get('stage')}")
            return True
        elif response.status_code == 503:
            data = response.json()
            print(f"   [ERROR] Agent not available: {data.get('error')}")
            print("\n   SOLUTION: Restart the server")
            return False
        else:
            print(f"   [ERROR] Build chat failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"   [ERROR] {e}")
        return False

if __name__ == "__main__":
    success = test_server()
    print("\n" + "="*60)
    if success:
        print("[SUCCESS] Server is working correctly!")
        print("You can now use the Build section in the web interface.")
    else:
        print("[FAILED] Server is not working correctly.")
        print("\nTROUBLESHOOTING:")
        print("1. Stop the current server (Ctrl+C)")
        print("2. Restart: python run_backend.py")
        print("3. Wait for '[SUCCESS] BuildSummaryAgent is ready!' message")
        print("4. Run this script again: python verify_server.py")
    print("="*60)

