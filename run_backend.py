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
from app import app, build_summary_agent

# Verify agent is initialized
print("\n" + "="*60)
print("FINAL VERIFICATION")
print("="*60)
if build_summary_agent is None:
    print("[CRITICAL ERROR] BuildSummaryAgent is NOT initialized!")
    print("The agent will not work. Check the logs above for errors.")
    print("="*60)
    print("\nDO NOT CONTINUE - Fix the initialization errors first!")
    sys.exit(1)
else:
    print("[SUCCESS] BuildSummaryAgent is ready to use")
    print(f"   - Agent Name: {build_summary_agent.name}")
    print(f"   - Has LLM: {build_summary_agent.llm is not None}")
    print("="*60 + "\n")

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

