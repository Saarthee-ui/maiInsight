@echo off
echo ========================================
echo Starting SaarInsights Web Application
echo ========================================
echo.
echo Make sure you have:
echo 1. Activated your virtual environment
echo 2. Installed requirements: pip install -r requirements.txt
echo 3. Configured your .env file
echo.
echo Starting Flask server...
echo Open http://localhost:5000 in your browser
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python run_backend.py

pause

