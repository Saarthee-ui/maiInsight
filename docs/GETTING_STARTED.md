# Getting Started Checklist

## 🚀 Quick Start: Running Frontend & Backend

### Step 0: Start the Application (Frontend + Backend Together)

The Mailytics application runs both frontend and backend on a single Flask server. Follow these steps:

#### 1. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
venv\Scripts\activate
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

#### 2. Start the Server (Frontend + Backend)

**Option A: Using run_backend.py (Recommended)**
```powershell
python run_backend.py
```

**Option B: Using start_web_app.bat (Windows)**
```powershell
.\start_web_app.bat
```

**Option C: Using start_web_app.sh (Linux/Mac)**
```bash
chmod +x start_web_app.sh
./start_web_app.sh
```

#### 3. What You Should See

When the server starts successfully, you'll see:

```
============================================================
Starting Mailytics Backend & Frontend Server
============================================================

Frontend URL: http://localhost:5000
Backend API: http://localhost:5000/api/

Open http://localhost:5000 in your browser
Press Ctrl+C to stop the server
============================================================

 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.1.104:5000
Press CTRL+C to quit
```

#### 4. Verify Setup (Optional but Recommended)

Before starting, you can test your setup:

```powershell
python test_frontend_setup.py
```

This will check:
- Virtual environment is activated
- Frontend template file exists
- Backend app is configured correctly
- Required packages are installed

#### 5. Access the Application

**Open your web browser and go to:**
- **Frontend:** http://localhost:5000
- **Alternative:** http://127.0.0.1:5000

You should see the SaarInsights interface with:
- Chat interface on the left
- Data visualization panel on the right
- Navigation sidebar

#### 6. Test the Application

1. **Try a query in the chat:**
   - Type: "Show me orders data"
   - Or: "Display customers table"
   - The chatbot will query your database and display results

2. **Check data visualization:**
   - Results appear in the right panel
   - You can refresh data using the refresh button
   - View history in the History tab

#### 5. Test the Backend API

The backend API endpoints are available at:
- `POST http://localhost:5000/api/chatbot/query` - Query data
- `GET http://localhost:5000/api/chatbot/refresh/<monitor_id>` - Refresh data
- `GET http://localhost:5000/api/chatbot/history/<schema>/<table>` - Get history

### Complete Backend Code (run_backend.py)

Here's the complete code that starts both frontend and backend:

```python
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
    print("\n" + "="*60)
    print("Starting Mailytics Backend & Frontend Server")
    print("="*60)
    print("\nFrontend URL: http://localhost:5000")
    print("Backend API: http://localhost:5000/api/")
    print("\nOpen http://localhost:5000 in your browser")
    print("Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
```

### Complete Frontend Code Location

The frontend is a single HTML file located at:
- **File:** `frontend/templates/chatbot.html`
- **Served by:** Flask route `@app.route("/")` in `backend/app.py`

### How Frontend and Backend Work Together

1. **Flask serves the frontend:**
   ```python
   # In backend/app.py
   @app.route("/")
   def index():
       return render_template("chatbot.html")
   ```

2. **Frontend JavaScript calls backend APIs:**
   ```javascript
   // In chatbot.html
   fetch('/api/chatbot/query', {
       method: 'POST',
       headers: {'Content-Type': 'application/json'},
       body: JSON.stringify({query: userQuery})
   })
   ```

3. **Backend processes and returns data:**
   ```python
   # In backend/app.py
   @app.route("/api/chatbot/query", methods=["POST"])
   def chatbot_query():
       # Process query and return JSON
       return jsonify(response)
   ```

### Troubleshooting Frontend Issues

**If frontend doesn't load:**

1. **Check server is running:**
   ```powershell
   netstat -ano | findstr :5000
   ```
   Should show port 5000 is listening.

2. **Check browser console:**
   - Press F12 in browser
   - Check Console tab for errors
   - Check Network tab for failed requests

3. **Verify template file exists:**
   ```powershell
   Test-Path frontend\templates\chatbot.html
   ```
   Should return `True`

4. **Check Flask can find templates:**
   - Verify `backend/app.py` has: `template_folder='../frontend/templates'`
   - Verify `chatbot.html` exists in that folder

5. **Try accessing directly:**
   - http://localhost:5000/ (should show HTML)
   - http://localhost:5000/api/chatbot/query (should show method not allowed, not 404)

**Common Issues:**

- **404 Error:** Server not running or wrong port
- **500 Error:** Check server terminal for Python errors
- **Blank Page:** Check browser console for JavaScript errors
- **CORS Error:** Already handled by `CORS(app)` in backend

### Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

---

## ✅ Step 1: Review Architecture (15 minutes)

1. Read `docs/ARCHITECTURE_DECISION.md` - Understand when agentic AI is beneficial
2. Read `docs/MULTI_AGENT_ARCHITECTURE.md` - Understand agent design
3. Read `docs/SUMMARY.md` - Get the big picture

## ✅ Step 2: Set Up Environment (10 minutes)

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env` file** (copy from template below):
   ```bash
   # Minimum required for testing
   LLM_PROVIDER=ollama  # or openai
   OPENAI_API_KEY=your_key_here  # if using OpenAI
   
   # Warehouse (Snowflake example)
   WAREHOUSE_TYPE=snowflake
   SNOWFLAKE_ACCOUNT=your_account
   SNOWFLAKE_USER=your_user
   SNOWFLAKE_PASSWORD=your_password
   SNOWFLAKE_WAREHOUSE=your_warehouse
   SNOWFLAKE_DATABASE=your_database
   SNOWFLAKE_SCHEMA_BRONZE=BRONZE
   SNOWFLAKE_SCHEMA_SILVER=SILVER
   SNOWFLAKE_SCHEMA_GOLD=GOLD
   ```

## ✅ Step 3: Test Local LLM (Optional, 5 minutes)

If you want to test without API costs:

1. **Install Ollama**: https://ollama.ai
2. **Pull model**:
   ```bash
   ollama pull llama3.1
   ```
3. **Test**:
   ```bash
   ollama run llama3.1 "Hello"
   ```
4. **Update `.env`**:
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   ```

## ✅ Step 4: Test Warehouse Connection (5 minutes)

```python
from tools.warehouse import warehouse
from config import settings

# List tables in Bronze
tables = warehouse.list_tables(settings.snowflake_schema_bronze)
print(f"Found {len(tables)} tables")

# Test metadata extraction
if tables:
    metadata = warehouse.get_table_metadata(
        settings.snowflake_schema_bronze, 
        tables[0]
    )
    print(f"Table: {metadata.name}")
    print(f"Columns: {len(metadata.columns)}")
```

## ✅ Step 5: Run Your First Transformation (10 minutes)

### Option A: Using CLI

```bash
python scripts/run_agent.py bronze-to-silver --schema BRONZE --table orders
```

### Option B: Using Python Script

```bash
python examples/bronze_to_silver_example.py
```

### Option C: Using Python API

```python
from orchestration import run_bronze_to_silver

result = run_bronze_to_silver("BRONZE", "orders")
print(result)
```

## ✅ Step 6: Review Generated Code (5 minutes)

1. **Check generated dbt models**:
   ```bash
   ls -la dbt_project/models/silver/
   ```

2. **Review a model**:
   ```bash
   cat dbt_project/models/silver/hub_orders.sql
   ```

3. **Run dbt** (if dbt is configured):
   ```bash
   cd dbt_project
   dbt run --models silver
   ```

## ✅ Step 7: Customize for Your Use Case (30+ minutes)

1. **Modify Data Vault patterns**:
   - Edit `agents/datavault_agent.py` prompts
   - Add custom templates in `templates/datavault/`

2. **Customize dbt generation**:
   - Edit `tools/dbt_generator.py`
   - Add your SQL patterns

3. **Add custom validation**:
   - Extend `agents/base_agent.py` validation methods

## 🎯 What You Have Now

✅ **Working Phase 1 MVP**:
- Bronze Schema Understanding Agent
- Data Vault Modeling Agent  
- ETL Code Generation Agent
- LangGraph orchestration
- CLI interface

✅ **Ready to Extend**:
- Query Monitoring Agent (Phase 2)
- Gold Optimization Agent (Phase 2)
- Anomaly Detection Agent (Phase 3)
- Business Question Agent (Phase 3)

## 📚 Next Steps

1. **Read the docs** in `docs/` folder
2. **Experiment** with different Bronze tables
3. **Customize** prompts and templates
4. **Extend** with Phase 2 agents when ready

## 🆘 Troubleshooting

### Frontend Not Loading

**Symptoms:** Blank page, 404 error, or page doesn't appear

**Solutions:**

1. **Verify server is running:**
   ```powershell
   # Check if port 5000 is in use
   netstat -ano | findstr :5000
   ```
   If nothing shows, server isn't running. Start it with `python run_backend.py`

2. **Check template file exists:**
   ```powershell
   Test-Path frontend\templates\chatbot.html
   ```
   If False, the file is missing. Check file structure.

3. **Verify Flask template folder path:**
   - Open `backend/app.py`
   - Line 16 should be: `app = Flask(__name__, template_folder='../frontend/templates')`
   - This tells Flask where to find HTML files

4. **Check browser console (F12):**
   - Open DevTools (F12)
   - Check Console tab for JavaScript errors
   - Check Network tab for failed requests (404, 500, etc.)

5. **Test backend API directly:**
   ```powershell
   # Test if backend is responding
   curl http://localhost:5000/api/chatbot/query
   ```
   Should return method not allowed (not 404), meaning backend is running.

6. **Clear browser cache:**
   - Press Ctrl+Shift+R (hard refresh)
   - Or clear browser cache completely

### "Module not found"
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt`
- Verify you see `(venv)` in terminal prompt

### "LLM API key not set"
- Check `.env` file exists in project root
- Verify `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set
- Or use `LLM_PROVIDER=ollama` for local testing
- Note: Frontend will still work, but chatbot queries won't

### "Warehouse connection failed"
- Verify credentials in `.env`
- Test connection manually with SQLAlchemy
- Check network/firewall settings
- Note: Frontend will load, but database features won't work

### "Table not found"
- Verify table exists in Bronze schema
- Check schema name (case-sensitive for Snowflake)
- List tables: `warehouse.list_tables("BRONZE")`

### Server Won't Start

**Error:** `Address already in use` or `Port 5000 is already in use`

**Solution:**
1. Find process using port 5000:
   ```powershell
   netstat -ano | findstr :5000
   ```
2. Kill the process or change port in `run_backend.py`:
   ```python
   app.run(debug=True, host="0.0.0.0", port=5001)  # Change to 5001
   ```

### Frontend Shows But API Calls Fail

**Symptoms:** Frontend loads but queries don't work

**Solutions:**
1. Check browser Network tab (F12) for API request status
2. Check server terminal for error messages
3. Verify `.env` file has correct database/LLM configuration
4. Test API directly with curl or Postman

## 💡 Tips

1. **Start with Ollama** for development (free, fast iteration)
2. **Use GPT-4o** for production (better quality)
3. **Review generated models** before running dbt
4. **Customize prompts** for your domain
5. **Add validation** for your specific requirements

## 🎓 Learning Path

1. **Week 1**: Understand architecture, test with sample tables
2. **Week 2**: Customize prompts, add domain-specific patterns
3. **Week 3**: Implement Phase 2 (Query Monitoring + Gold Optimization)
4. **Week 4**: Production deployment, monitoring, optimization

Good luck! 🚀

