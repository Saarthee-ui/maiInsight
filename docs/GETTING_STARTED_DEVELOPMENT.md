# Getting Started with Mailytics Development

This guide will help you start developing and working on the Mailytics project.

## Quick Start

### 1. Start the Development Server

**Option A: Using the start script (Recommended)**
```powershell
venv\Scripts\activate
python start_server.py
```

**Option B: Using run_backend.py**
```powershell
venv\Scripts\activate
python run_backend.py
```

**Option C: Using the batch file (Windows)**
```powershell
.\start_web_app.bat
```

### 2. Access the Application

Once the server starts, open your browser and go to:
- **Frontend:** http://localhost:5000
- **Backend API Base:** http://localhost:5000/api/

You should see the SaarInsights interface with the chatbot and data visualization panels.

---

## Project Structure

```
mailytics/
├── backend/              # Backend Flask application
│   ├── app.py           # Main Flask app (routes, API endpoints)
│   ├── agents/          # AI agents for data processing
│   ├── config/          # Configuration settings
│   ├── models/          # Data models and schemas
│   ├── orchestration/   # Workflow orchestration
│   ├── tools/           # Utility tools (database, file readers, etc.)
│   └── storage/         # Storage utilities
├── frontend/
│   └── templates/
│       └── chatbot.html # Frontend HTML/JS interface
├── docs/                # Documentation
├── run_backend.py       # Backend entry point
├── start_server.py      # Alternative server starter
└── requirements.txt     # Python dependencies
```

---

## Key Components to Work On

### Frontend Development

**Location:** `frontend/templates/chatbot.html`

This is a single-page application with:
- Chat interface for querying data
- Data visualization tables
- History/snapshot viewing
- Navigation sidebar

**To modify the UI:**
1. Edit `frontend/templates/chatbot.html`
2. The server auto-reloads (if reloader is enabled)
3. Refresh your browser to see changes

**Key sections:**
- **Lines 1-467:** CSS styles
- **Lines 468-600:** HTML structure
- **Lines 601-1290:** JavaScript functionality

### Backend Development

**Main App:** `backend/app.py`

**Key Routes:**
- `GET /` - Serves frontend HTML
- `POST /api/chatbot/query` - Process chatbot queries
- `GET /api/chatbot/refresh/<monitor_id>` - Refresh data
- `GET /api/chatbot/history/<schema>/<table>` - Get history
- `GET /api/chatbot/snapshot/<snapshot_id>` - Get snapshot

**To add new API endpoints:**
1. Edit `backend/app.py`
2. Add new `@app.route()` decorators
3. Restart server to see changes

### Agents

**Location:** `backend/agents/`

Available agents:
- `chatbot_agent.py` - Main chatbot logic
- `data_reader_agent.py` - Reads data from database
- `data_display_agent.py` - Formats data for display
- `historical_data_agent.py` - Manages data snapshots
- `auto_refresh_agent.py` - Auto-refreshes data

**To modify agent behavior:**
1. Edit the specific agent file in `backend/agents/`
2. Restart the server

### Database Configuration

**Location:** `backend/config/settings.py`

Configure via `.env` file in project root:
```env
# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=your_database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

---

## Development Workflow

### 1. Make Changes

Edit the files you want to modify:
- Frontend: `frontend/templates/chatbot.html`
- Backend: `backend/app.py` or other backend files
- Agents: `backend/agents/*.py`

### 2. Test Changes

**For Frontend Changes:**
- Save the file
- Refresh browser (http://localhost:5000)
- Changes should appear immediately

**For Backend Changes:**
- Save the file
- Restart the server (Ctrl+C, then run again)
- Test the API endpoints

### 3. Debug

**Check Server Logs:**
- Server logs appear in the terminal where you ran `start_server.py`
- Look for errors, warnings, or request logs

**Browser Console:**
- Open browser DevTools (F12)
- Check Console tab for JavaScript errors
- Check Network tab for API request/response issues

**Backend Debugging:**
- Flask debug mode is enabled (shows detailed errors)
- Check terminal for Python tracebacks
- Use `print()` statements or logging for debugging

---

## Common Development Tasks

### Adding a New API Endpoint

1. Open `backend/app.py`
2. Add a new route:
```python
@app.route("/api/my-endpoint", methods=["GET", "POST"])
def my_endpoint():
    # Your logic here
    return jsonify({"success": True, "data": "result"})
```
3. Restart server
4. Test: `http://localhost:5000/api/my-endpoint`

### Modifying the Frontend UI

1. Open `frontend/templates/chatbot.html`
2. Modify HTML/CSS/JavaScript as needed
3. Save and refresh browser

### Adding a New Agent

1. Create new file: `backend/agents/my_agent.py`
2. Inherit from `BaseAgent` (see `base_agent.py`)
3. Implement required methods
4. Import and use in `backend/app.py` or `orchestration/`

### Changing Database Queries

1. Edit `backend/agents/data_reader_agent.py`
2. Modify the `read_table_data()` method
3. Or edit `backend/tools/warehouse.py` for low-level queries

---

## Testing Your Changes

### Manual Testing

1. **Start server:** `python start_server.py`
2. **Open browser:** http://localhost:5000
3. **Test features:**
   - Send a chatbot query
   - View data tables
   - Refresh data
   - Check history

### API Testing

Use tools like:
- **Postman** - GUI for API testing
- **curl** - Command line
- **Browser DevTools** - Network tab

Example curl command:
```bash
curl -X POST http://localhost:5000/api/chatbot/query \
  -H "Content-Type: application/json" \
  -d '{"query": "show me orders", "schema": "public"}'
```

---

## Troubleshooting

### Server Won't Start

**Check:**
1. Virtual environment is activated: `(venv)` should appear in prompt
2. Dependencies installed: `pip install -r requirements.txt`
3. Port 5000 is free: `netstat -ano | findstr :5000`

### Changes Not Appearing

**Frontend:**
- Hard refresh browser (Ctrl+Shift+R or Ctrl+F5)
- Clear browser cache
- Check browser console for errors

**Backend:**
- Restart the server after making changes
- Check terminal for errors
- Verify the route is correct

### Database Connection Issues

**Check:**
1. `.env` file exists and has correct credentials
2. PostgreSQL is running
3. Database exists and is accessible
4. Test connection: `python test_postgres_connection.py`

### Import Errors

**Check:**
1. Virtual environment is activated
2. All dependencies installed: `pip install -r requirements.txt`
3. Python path is correct (scripts handle this automatically)

---

## Next Steps

1. **Explore the codebase:**
   - Read `backend/app.py` to understand routes
   - Check `frontend/templates/chatbot.html` for UI structure
   - Review `backend/agents/` for agent implementations

2. **Set up your environment:**
   - Configure `.env` with your database credentials
   - Add your OpenAI API key (if using OpenAI)

3. **Start making changes:**
   - Pick a feature to work on
   - Make small, incremental changes
   - Test frequently

4. **Read documentation:**
   - Check other docs in `docs/` folder
   - Review architecture docs for design decisions

---

## Useful Commands

```powershell
# Activate virtual environment
venv\Scripts\activate

# Start server
python start_server.py

# Install new package
pip install package_name
pip freeze > requirements.txt  # Update requirements

# Check Python version
python --version

# Check installed packages
pip list

# Run tests (if available)
pytest

# Format code (if black is installed)
black backend/
```

---

## Development Tips

1. **Keep server running** while developing frontend (auto-reloads)
2. **Restart server** after backend changes
3. **Use browser DevTools** for debugging frontend
4. **Check terminal logs** for backend debugging
5. **Make small changes** and test frequently
6. **Use version control** (git) to track changes

---

## Need Help?

- Check `docs/RUNNING_APPLICATION.md` for server setup
- Review `docs/GETTING_STARTED.md` for initial setup
- Check other documentation in `docs/` folder
- Review code comments in source files

Happy coding! 🚀


