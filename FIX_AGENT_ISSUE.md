# Fix: Agent Not Working - Complete Solution

## Problem Summary
The Build Summary Agent is not working. This is typically caused by:
1. Server running old code (needs restart)
2. Agent not initializing properly at startup
3. Port 5000 conflict

## Complete Fix Steps

### Step 1: Stop All Running Servers

**Option A: Use the stop script**
```bash
python stop_server.py
```

**Option B: Manual stop**
1. Find the terminal running the server
2. Press `Ctrl+C`
3. Wait for it to stop completely

**Option C: Force kill (if needed)**
```bash
# Windows PowerShell:
netstat -ano | findstr :5000
# Note the PID (last number)
taskkill /PID <PID> /F
```

### Step 2: Verify Server is Stopped
```bash
python verify_server.py
```
If it says "Cannot connect to server", you're good. If it connects, the server is still running.

### Step 3: Start Fresh Server
```bash
python run_backend.py
```

### Step 4: Check Startup Messages

**✅ GOOD - You should see:**
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

============================================================
FINAL VERIFICATION
============================================================
[SUCCESS] BuildSummaryAgent is ready to use
   - Agent Name: BuildSummaryAgent
   - Has LLM: True
============================================================
```

**❌ BAD - If you see:**
```
[CRITICAL ERROR] BuildSummaryAgent is None!
The application will not work properly.
```
**→ DO NOT CONTINUE. Check the error messages above.**

### Step 5: Test the Server (in a NEW terminal)
```bash
python verify_server.py
```

Expected output:
```
[OK] Server is running
[OK] Health endpoint works
   - Agent available: True
   - Agent has LLM: True
   - Storage available: True
[OK] Build chat endpoint works
[SUCCESS] Server is working correctly!
```

### Step 6: Test in Browser
1. Open http://localhost:5000
2. Go to Build section
3. Type a message in "Talk to AI Data Engineer"
4. You should get a response

## Common Issues & Solutions

### Issue 1: "Not Found" on /api/health
**Cause**: Server is running old code
**Solution**: 
1. Stop server completely (Step 1)
2. Restart (Step 3)
3. Verify startup messages (Step 4)

### Issue 2: "Agent not available" in browser
**Cause**: Agent didn't initialize
**Solution**:
1. Check startup logs for errors
2. Verify `.env` file has `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
3. Restart server

### Issue 3: "Cannot connect to server"
**Cause**: Server is not running
**Solution**:
1. Start server: `python run_backend.py`
2. Wait for startup messages
3. Test again

### Issue 4: Agent is None at startup
**Cause**: Initialization error
**Solution**:
1. Check the error messages in startup logs
2. Common causes:
   - Missing API key in `.env`
   - Invalid API key
   - Import errors
   - Database connection issues
3. Fix the issue and restart

## Verification Commands

```bash
# Test server import (without starting server)
python -c "import sys; sys.path.insert(0, 'backend'); import os; os.chdir('backend'); from app import build_summary_agent; print('OK' if build_summary_agent else 'FAILED')"

# Test running server
python verify_server.py

# Stop server
python stop_server.py
```

## What Was Fixed

1. ✅ Added comprehensive startup verification
2. ✅ Added clear error messages
3. ✅ Added fallback initialization
4. ✅ Added health check endpoint
5. ✅ Added test endpoint
6. ✅ Added verification scripts
7. ✅ Improved error handling in API routes

## Next Steps After Fix

Once the server is working:
1. The agent will guide you through creating transformations
2. It will ask about your goals
3. It will suggest databases and transformation names
4. It will collect connection details
5. It will save everything to the database

## Still Not Working?

If you've followed all steps and it's still not working:

1. **Check the logs**: Look at the terminal output when starting the server
2. **Check .env file**: Make sure `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set
3. **Check Python version**: Should be Python 3.8+
4. **Check dependencies**: Run `pip install -r requirements.txt`
5. **Share the error**: Copy the exact error message from the terminal

