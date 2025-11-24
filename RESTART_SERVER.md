# How to Restart the Server Properly

## The Problem
If you're seeing "Not Found" errors or "Agent not available" messages, it means:
1. The server is running old code, OR
2. The server didn't initialize the agent properly

## Solution: Complete Server Restart

### Step 1: Stop the Current Server
1. Find the terminal/command prompt where the server is running
2. Press `Ctrl+C` to stop it
3. Wait until you see the prompt return (the server has stopped)

### Step 2: Verify No Server is Running
Run this command to check if port 5000 is still in use:
```bash
# Windows PowerShell:
netstat -ano | findstr :5000

# If you see any output, kill the process:
# Find the PID (last number) and run:
taskkill /PID <PID> /F
```

### Step 3: Start the Server Fresh
```bash
python run_backend.py
```

### Step 4: Verify Startup Messages
You should see these messages when the server starts:
```
============================================================
Initializing BuildSummaryAgent...
============================================================
LLM Provider: openai
API Key Configured: True
[OK] Agent initialized with LLM
============================================================
[SUCCESS] BuildSummaryAgent is ready!
   - Agent Name: BuildSummaryAgent
   - Has LLM: True
============================================================
```

**IMPORTANT**: If you see `[CRITICAL ERROR] BuildSummaryAgent is None!`, the server will NOT work. Check the error messages above it.

### Step 5: Test the Server
In a NEW terminal, run:
```bash
python verify_server.py
```

This will test:
- Server connectivity
- Health endpoint
- Build chat endpoint

### Step 6: Use the Web Interface
1. Open http://localhost:5000 in your browser
2. Go to the Build section
3. Start chatting with "Talk to AI Data Engineer"

## Troubleshooting

### Error: "Agent not available"
- **Solution**: The server needs to be restarted. Follow steps 1-3 above.

### Error: "Not Found" on /api/health
- **Solution**: The server is running old code. Stop and restart (steps 1-3).

### Error: "Cannot connect to server"
- **Solution**: The server is not running. Start it with `python run_backend.py`.

### Error: "BuildSummaryAgent is None"
- **Solution**: Check the startup logs for initialization errors. Common causes:
  - Missing or invalid API key in `.env` file
  - Import errors
  - Database connection issues

## Quick Test Commands

```bash
# Test if server is running
python verify_server.py

# Test server import (without starting server)
python -c "import sys; sys.path.insert(0, 'backend'); import os; os.chdir('backend'); from app import build_summary_agent; print('OK' if build_summary_agent else 'FAILED')"
```

