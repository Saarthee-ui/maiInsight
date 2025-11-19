"""Quick script to check if the server is running."""

import requests
import sys

try:
    response = requests.get("http://localhost:5000", timeout=2)
    print(f"✅ Server is running! Status: {response.status_code}")
    print(f"🌐 Open http://localhost:5000 in your browser")
    sys.exit(0)
except requests.exceptions.ConnectionError:
    print("❌ Server is not running on port 5000")
    print("💡 Start it with: python app.py")
    sys.exit(1)
except Exception as e:
    print(f"⚠️  Error checking server: {e}")
    sys.exit(1)

