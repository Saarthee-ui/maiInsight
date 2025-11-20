"""Test script to verify frontend and backend setup."""

import sys
import os
from pathlib import Path

print("="*60)
print("Testing Mailytics Frontend & Backend Setup")
print("="*60)

# Check 1: Virtual environment
print("\n1. Checking virtual environment...")
if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
    print("   ✓ Virtual environment is activated")
else:
    print("   ✗ Virtual environment is NOT activated")
    print("   Run: venv\\Scripts\\activate")

# Check 2: Template file exists
print("\n2. Checking frontend template file...")
template_path = Path("frontend/templates/chatbot.html")
if template_path.exists():
    print(f"   ✓ Template file found: {template_path}")
    print(f"   File size: {template_path.stat().st_size} bytes")
else:
    print(f"   ✗ Template file NOT found: {template_path}")
    print("   Expected location: frontend/templates/chatbot.html")

# Check 3: Backend app.py
print("\n3. Checking backend app.py...")
app_path = Path("backend/app.py")
if app_path.exists():
    print(f"   ✓ Backend app found: {app_path}")
    
    # Check template folder configuration
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if "template_folder" in content:
            print("   ✓ Template folder is configured in Flask app")
        else:
            print("   ✗ Template folder NOT configured in Flask app")
else:
    print(f"   ✗ Backend app NOT found: {app_path}")

# Check 4: Required packages
print("\n4. Checking required packages...")
required_packages = ['flask', 'flask_cors']
missing = []
for package in required_packages:
    try:
        __import__(package.replace('-', '_'))
        print(f"   ✓ {package} is installed")
    except ImportError:
        print(f"   ✗ {package} is NOT installed")
        missing.append(package)

if missing:
    print(f"\n   Install missing packages: pip install {' '.join(missing)}")

# Check 5: .env file
print("\n5. Checking .env file...")
env_path = Path(".env")
if env_path.exists():
    print(f"   ✓ .env file found")
else:
    print(f"   ⚠ .env file NOT found (optional, but recommended)")
    print("   Create .env file for database and LLM configuration")

# Check 6: Run backend import test
print("\n6. Testing backend imports...")
try:
    sys.path.insert(0, str(Path("backend")))
    os.chdir("backend")
    from app import app
    print("   ✓ Backend app imports successfully")
    print(f"   ✓ Flask app name: {app.name}")
    print(f"   ✓ Template folder: {app.template_folder}")
    os.chdir("..")
except Exception as e:
    print(f"   ✗ Backend import failed: {e}")
    os.chdir("..")

print("\n" + "="*60)
print("Setup Test Complete")
print("="*60)
print("\nIf all checks passed, you can start the server with:")
print("  python run_backend.py")
print("\nThen open http://localhost:5000 in your browser")


