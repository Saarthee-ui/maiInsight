# Project Folder Structure

## Overview

The project has been reorganized into separate `frontend/` and `backend/` folders for better organization and maintainability.

## Directory Structure

```
saarInsights/
├── backend/                 # Backend application code
│   ├── __init__.py
│   ├── app.py              # Flask application entry point
│   ├── agents/             # AI agents (ChatbotAgent, DataReaderAgent, etc.)
│   ├── orchestration/      # Workflow orchestration (LangGraph)
│   ├── tools/              # Utility tools (warehouse, dbt, file readers)
│   ├── models/             # Data models (Pydantic schemas)
│   ├── config/             # Configuration management
│   ├── storage/            # State persistence
│   ├── scripts/            # CLI scripts
│   └── tests/              # Test files
│
├── frontend/               # Frontend application code
│   └── templates/         # HTML templates
│       └── chatbot.html    # Main UI template
│
├── docs/                   # Documentation
├── venv/                   # Python virtual environment
├── requirements.txt        # Python dependencies
├── run_backend.py          # Entry point to run backend from root
├── start_web_app.bat       # Windows startup script
├── start_web_app.sh        # Linux/Mac startup script
└── README.md               # Project documentation
```

## Running the Application

### Option 1: Using the startup scripts (Recommended)
```bash
# Windows
start_web_app.bat

# Linux/Mac
./start_web_app.sh
```

### Option 2: Using the Python entry point
```bash
python run_backend.py
```

### Option 3: Running directly from backend folder
```bash
cd backend
python app.py
```

## Important Notes

1. **Template Path**: The Flask app is configured to look for templates in `../frontend/templates/` relative to the backend folder.

2. **Import Paths**: All backend imports use relative paths within the `backend/` folder (e.g., `from agents.chatbot_agent import ChatbotAgent`).

3. **Python Path**: When running from the root using `run_backend.py`, the backend folder is automatically added to the Python path.

4. **Working Directory**: The `run_backend.py` script changes the working directory to `backend/` to ensure relative paths work correctly.

## Development

- **Backend**: All Python backend code is in `backend/`
- **Frontend**: All HTML/CSS/JavaScript is in `frontend/templates/`
- **Configuration**: Environment variables and settings are managed through `backend/config/`

