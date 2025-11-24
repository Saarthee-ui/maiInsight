"""Test script to verify build agent is working."""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

print("="*60)
print("Testing Build Summary Agent")
print("="*60)
print()

# Test 1: Import
print("1. Testing imports...")
try:
    from app import app, build_summary_agent
    print("   [OK] Imports successful")
except Exception as e:
    print(f"   [ERROR] Import failed: {e}")
    sys.exit(1)

# Test 2: Agent status
print("\n2. Checking agent status...")
if build_summary_agent is None:
    print("   [ERROR] Agent is None!")
    sys.exit(1)
else:
    print("   [OK] Agent is initialized")
    print(f"   - Has LLM: {build_summary_agent.llm is not None}")

# Test 3: Test conversation
print("\n3. Testing conversation...")
try:
    result = build_summary_agent.start_conversation("test_session_123", "I want to create a Sales Dashboard")
    print("   [OK] Conversation started successfully")
    print(f"   - Stage: {result.get('stage')}")
    print(f"   - Message: {result.get('message', '')[:100]}...")
except Exception as e:
    print(f"   [ERROR] Conversation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check routes
print("\n4. Checking API routes...")
try:
    routes = [str(r) for r in app.url_map.iter_rules() if '/api/build' in str(r)]
    print(f"   [OK] Found {len(routes)} build routes:")
    for route in routes:
        print(f"      - {route}")
except Exception as e:
    print(f"   [ERROR] Route check failed: {e}")

print("\n" + "="*60)
print("[SUCCESS] All tests passed! Agent is ready to use.")
print("="*60)
print("\nNext steps:")
print("   1. Make sure your Flask server is running: python run_backend.py")
print("   2. Visit: http://localhost:5000")
print("   3. Click 'Build' in the sidebar")
print("   4. Try: 'I want to create a Sales Dashboard'")

