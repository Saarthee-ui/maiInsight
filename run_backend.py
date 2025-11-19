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

# Import app and background monitoring setup
from app import app, active_monitors, background_monitor
import threading

# Start background monitoring thread
monitor_thread = threading.Thread(target=background_monitor, daemon=True)
monitor_thread.start()

# Run Flask app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

