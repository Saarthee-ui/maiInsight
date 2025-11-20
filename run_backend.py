"""Entry point to run the Flask backend from project root."""

import sys
import os
from pathlib import Path

# Add backend to Python path so imports work
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

# Change to backend directory so relative paths work
original_cwd = os.getcwd()
os.chdir(backend_path)

# Import app
from app import app

# Run Flask app
if __name__ == "__main__":
    print("\n" + "="*60)
    print("Starting Mailytics Backend & Frontend Server")
    print("="*60)
    print("\nFrontend URL: http://localhost:5000")
    print("Backend API: http://localhost:5000/api/")
    print("\nOpen http://localhost:5000 in your browser")
    print("Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)

