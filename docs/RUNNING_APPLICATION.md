# Running the Application

This guide explains how to run both the frontend and backend of the SaarInsights application.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Running the Application](#running-the-application)
- [Accessing the Application](#accessing-the-application)
- [Troubleshooting](#troubleshooting)

---

## Overview

The SaarInsights application consists of:

- **Backend**: Flask web server (Python) that serves the API and frontend templates
- **Frontend**: Single-page HTML application served by Flask (no separate frontend server needed)

The application runs on a single Flask server that handles both API requests and serves the frontend interface.

---

## Prerequisites

Before running the application, ensure you have:

1. **Python 3.11+** installed
   - Check version: `python --version` or `python3 --version`

2. **Virtual Environment** (recommended)
   - Python's `venv` module (usually included with Python)

3. **PostgreSQL Database** (optional but recommended)
   - Required for full functionality
   - Can run without it, but database features will be disabled

4. **LLM Provider** (required)
   - OpenAI API key, OR
   - Anthropic API key, OR
   - Ollama (local LLM) installed

---

## Environment Setup

### Step 1: Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create a `.env` file in the project root directory. You can copy from the template:

**Windows:**
```powershell
Copy-Item docs\env.template .env
```

**Linux/Mac:**
```bash
cp docs/env.template .env
```

Then edit `.env` with your configuration. Minimum required configuration:

```env
# LLM Configuration (choose one)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# OR use Ollama (local, free)
# LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434

# PostgreSQL Configuration (optional but recommended)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=your_database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

For detailed configuration options, see [CREATE_ENV.md](./CREATE_ENV.md).

---

## Running the Application

### Option 1: Using the Start Scripts (Recommended)

**Windows:**
```powershell
.\start_web_app.bat
```

**Linux/Mac:**
```bash
chmod +x start_web_app.sh
./start_web_app.sh
```

### Option 2: Using Python Directly

**From project root:**
```bash
python run_backend.py
```

**Or from backend directory:**
```bash
cd backend
python app.py
```

### Option 3: Using Flask CLI

```bash
cd backend
flask run --host=0.0.0.0 --port=5000
```

---

## Accessing the Application

Once the server is running, you should see output like:

```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

### Open in Browser

Open your web browser and navigate to:

```
http://localhost:5000
```

or

```
http://127.0.0.1:5000
```

### Application Features

The web interface provides:

- **Chat Interface**: Ask questions about your data in natural language
- **Data Visualization**: View query results in tabular format
- **Data Refresh**: Manually refresh data for monitored tables
- **History**: View historical snapshots of table data
- **Navigation**: Access different sections (Visualize, Build, Extract, etc.)

---

## Application Structure

### Backend Endpoints

The Flask backend provides the following API endpoints:

- `GET /` - Serves the main frontend interface
- `POST /api/chatbot/query` - Process chatbot queries
- `GET /api/chatbot/refresh/<monitor_id>` - Refresh data for a monitor
- `GET /api/chatbot/history/<schema>/<table>` - Get historical snapshots
- `GET /api/chatbot/snapshot/<snapshot_id>` - Get specific snapshot data

### Frontend Location

The frontend HTML file is located at:
```
frontend/templates/chatbot.html
```

This file is automatically served by Flask when you access the root URL.

---

## Stopping the Application

To stop the server:

1. **In the terminal where it's running**, press `Ctrl+C` (Windows/Linux/Mac)
2. The server will shut down gracefully

---

## Troubleshooting

### Port Already in Use

**Error:** `Address already in use` or `Port 5000 is already in use`

**Solution:**
1. Find the process using port 5000:
   ```bash
   # Windows
   netstat -ano | findstr :5000
   
   # Linux/Mac
   lsof -i :5000
   ```
2. Kill the process or change the port in `backend/app.py`:
   ```python
   app.run(debug=True, host="0.0.0.0", port=5001)  # Change port
   ```

### Virtual Environment Path Error

**Error:** `Fatal error in launcher: Unable to create process using... The system cannot find the file specified`

**Cause:** This happens when the virtual environment was created in a different location or moved. The pip executable has hardcoded paths pointing to the old location.

**Solution:**
1. **Deactivate** the current virtual environment:
   ```powershell
   deactivate
   ```

2. **Delete** the old virtual environment:
   ```powershell
   # Windows
   Remove-Item -Recurse -Force venv
   
   # Or manually delete the venv folder
   ```

3. **Create a new virtual environment**:
   ```powershell
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Reinstall dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

**Note:** Always create virtual environments in the same directory as your project. Don't copy or move virtual environments between projects.

### Module Not Found Errors

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
1. Ensure virtual environment is activated
2. Reinstall dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Database Connection Errors

**Error:** `Database connection not available`

**Solution:**
1. Check PostgreSQL is running
2. Verify credentials in `.env` file
3. Test connection:
   ```bash
   python test_postgres_connection.py
   ```
4. The application will still start without database, but database features will be disabled

### LLM API Errors

**Error:** `OPENAI_API_KEY not set` or API errors

**Solution:**
1. Verify `.env` file exists and contains correct API key
2. Check API key is valid and has credits
3. For Ollama, ensure it's running:
   ```bash
   ollama serve
   ```

### Frontend Not Loading

**Error:** Blank page or 404 errors

**Solution:**
1. Check server is running on correct port
2. Verify `frontend/templates/chatbot.html` exists
3. Check browser console for JavaScript errors
4. Ensure Flask can find templates (check `template_folder` in `app.py`)

### CORS Errors

**Error:** CORS policy errors in browser console

**Solution:**
- CORS is already enabled in `app.py` with `CORS(app)`
- If issues persist, check browser console for specific error messages

---

## Development Mode

The application runs in **debug mode** by default, which provides:

- Automatic reloading when code changes
- Detailed error messages
- Debug console in browser

To disable debug mode, edit `backend/app.py`:

```python
app.run(debug=False, host="0.0.0.0", port=5000)
```

---

## Production Deployment

For production deployment:

1. **Disable debug mode** (set `debug=False`)
2. **Use a production WSGI server** (e.g., Gunicorn, uWSGI)
3. **Set up proper logging**
4. **Configure environment variables** securely
5. **Use HTTPS** with a reverse proxy (nginx, Apache)
6. **Set up process management** (systemd, supervisor)

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "backend.app:app"
```

---

## Next Steps

After successfully running the application:

1. **Test the chatbot**: Try asking questions about your data
2. **Explore features**: Navigate through different sections
3. **Read documentation**: Check other docs in the `docs/` folder
4. **Customize**: Modify agents, prompts, or UI as needed

For more information:
- [Getting Started Guide](./GETTING_STARTED.md)
- [Environment Setup](./CREATE_ENV.md)
- [Architecture Overview](./ARCHITECTURE_DECISION.md)

---

## Quick Reference

### Start Application
```bash
# Windows
.\start_web_app.bat

# Linux/Mac
./start_web_app.sh

# Or directly
python run_backend.py
```

### Access Application
```
http://localhost:5000
```

### Stop Application
```
Press Ctrl+C in terminal
```

### Check Status
- Server logs will show in terminal
- Browser console shows frontend errors
- Check `http://localhost:5000` for connection

---

**Need Help?** Check the troubleshooting section above or review the other documentation files in the `docs/` folder.

