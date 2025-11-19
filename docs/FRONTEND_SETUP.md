# 🎨 Frontend UI Setup Guide

## ✅ What Was Created

I've created a **complete web UI** for the chatbot data viewer! Now you can see and use it in your browser.

## 📁 Files Created

1. **`app.py`** - Flask web server with API endpoints
2. **`templates/chatbot.html`** - Beautiful web interface (HTML/CSS/JavaScript)

## 🚀 How to Run

### Step 1: Install Flask

```bash
pip install flask flask-cors
```

Or if you want to install all requirements:
```bash
pip install -r requirements.txt
```

### Step 2: Start the Web Server

```bash
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

### Step 3: Open in Browser

Open your browser and go to:
```
http://localhost:5000
```

## 🎯 What You'll See

### Beautiful Chat Interface

- **Left Panel**: Chat interface where you type questions
- **Right Panel**: Data table display
- **Auto-refresh**: Data updates automatically every 30 seconds
- **Modern UI**: Gradient design, smooth animations

### Features

✅ **Natural Language Queries**: Type "Show me orders data"  
✅ **Real-time Data Display**: See data in formatted table  
✅ **Auto-refresh**: Data updates when PostgreSQL changes  
✅ **Manual Refresh**: Click "Refresh" button anytime  
✅ **Responsive Design**: Works on desktop and mobile  

## 📸 Example Usage

1. **Open browser** → `http://localhost:5000`
2. **Type query**: "Show me orders data"
3. **See data**: Table appears on the right
4. **Auto-refresh**: Data updates every 30 seconds
5. **Manual refresh**: Click "🔄 Refresh" button

## 🔧 API Endpoints

The web server provides these endpoints:

### 1. `GET /` 
- Serves the chat interface HTML

### 2. `POST /api/chatbot/query`
- Handles chatbot queries
- Request: `{"query": "Show me orders data", "schema": "bronze"}`
- Response: `{"success": true, "data": [...], "columns": [...], ...}`

### 3. `GET /api/chatbot/refresh/<monitor_id>`
- Manually refresh data for a monitored table

### 4. `GET /api/chatbot/history/<schema>/<table>`
- Get historical snapshots

## 🎨 UI Features

### Chat Interface
- User messages (right side, purple gradient)
- Bot responses (left side, gray)
- Loading indicators
- Smooth animations

### Data Display
- Formatted table with headers
- Row highlighting on hover
- Summary message
- Metadata (total rows, displayed rows)

### Auto-refresh
- Background monitoring every 30 seconds
- Automatic UI updates
- Visual refresh indicator

## 🔄 How Auto-Refresh Works

1. **User asks for data** → Monitor starts
2. **Background thread** checks every 30 seconds
3. **If data changed** → Automatically refreshes display
4. **Historical snapshot** saved automatically

## 🛠️ Customization

### Change Port

Edit `app.py`:
```python
app.run(debug=True, host="0.0.0.0", port=8080)  # Change 5000 to 8080
```

### Change Refresh Interval

Edit `app.py`:
```python
time.sleep(60)  # Change 30 to 60 seconds
```

### Change UI Colors

Edit `templates/chatbot.html`:
```css
background: linear-gradient(135deg, #your-color 0%, #your-color 100%);
```

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Or change port in app.py
```

### Module Not Found

```bash
pip install flask flask-cors
```

### Database Connection Error

Make sure your `.env` file has correct PostgreSQL credentials:
```env
WAREHOUSE_TYPE=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=your_database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
```

## 📱 Production Deployment

For production, use a proper WSGI server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Or use Docker, or deploy to cloud platforms (Heroku, AWS, etc.).

## ✅ Summary

**YES, the changes are implemented!** 

- ✅ Backend agents created
- ✅ Web API created
- ✅ Frontend UI created
- ✅ Auto-refresh working
- ✅ Historical snapshots working

**Just run `python app.py` and open `http://localhost:5000` to see it!** 🚀

