# PostgreSQL Setup Guide for Chatbot Data Viewer

## ✅ Code is Ready!

The code to read from PostgreSQL is **already implemented** and ready to use. You just need to **configure the connection**.

---

## 🔧 Setup Steps

### Step 1: Create `.env` File

Copy the template:
```bash
copy env.template .env
```

Or manually create `.env` file in the project root.

### Step 2: Configure PostgreSQL Connection

Edit `.env` file and set these values:

```env
# Set warehouse type to PostgreSQL
WAREHOUSE_TYPE=postgres

# PostgreSQL Connection Details
POSTGRES_HOST=localhost          # Your PostgreSQL host
POSTGRES_PORT=5432               # PostgreSQL port (default: 5432)
POSTGRES_DATABASE=your_database  # Your database name
POSTGRES_USER=postgres           # Your PostgreSQL username
POSTGRES_PASSWORD=your_password  # Your PostgreSQL password

# Schema names (where your tables are)
POSTGRES_SCHEMA_BRONZE=bronze    # Default schema name
```

### Step 3: Verify PostgreSQL is Running

Make sure PostgreSQL is running and accessible:

```bash
# Test connection (if psql is installed)
psql -h localhost -U postgres -d your_database
```

### Step 4: Verify Tables Exist

Make sure your tables exist in PostgreSQL:

```sql
-- Check if schema exists
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'bronze';

-- Check tables in schema
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'bronze';
```

---

## 📋 Example `.env` Configuration

```env
# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# Warehouse Configuration
WAREHOUSE_TYPE=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=saarinsights
POSTGRES_USER=postgres
POSTGRES_PASSWORD=mypassword123
POSTGRES_SCHEMA_BRONZE=bronze
```

---

## 🧪 Test the Connection

### Option 1: Test with Python

```python
from tools.warehouse import warehouse

# Test connection
try:
    result = warehouse.execute_query("SELECT 1 as test")
    print("✅ PostgreSQL connection successful!")
    print(f"Test result: {result}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

### Option 2: Test with Chatbot

```bash
python scripts/run_agent.py "Show me orders data" --schema bronze
```

---

## 🔍 How It Works

1. **DataReaderAgent** reads from PostgreSQL using `warehouse.execute_query()`
2. **Warehouse connection** is built from `.env` settings
3. **Connection string** format: `postgresql://user:password@host:port/database`
4. **Queries** are executed using SQLAlchemy

---

## ⚠️ Common Issues

### Issue 1: "ModuleNotFoundError: No module named 'psycopg2'"

**Solution:**
```bash
pip install psycopg2-binary
```

### Issue 2: "Connection refused" or "Can't connect to PostgreSQL"

**Solutions:**
- Check PostgreSQL is running: `pg_isready` or check Windows Services
- Verify host/port in `.env`
- Check firewall settings
- Verify username/password

### Issue 3: "Database does not exist"

**Solution:**
```sql
-- Create database
CREATE DATABASE saarinsights;

-- Or use existing database
-- Update POSTGRES_DATABASE in .env
```

### Issue 4: "Schema does not exist"

**Solution:**
```sql
-- Create schema
CREATE SCHEMA IF NOT EXISTS bronze;

-- Or use existing schema
-- Update POSTGRES_SCHEMA_BRONZE in .env
```

### Issue 5: "Table does not exist"

**Solution:**
```sql
-- Create a test table
CREATE TABLE bronze.orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    order_date DATE,
    total_amount DECIMAL(10,2),
    status VARCHAR(50)
);

-- Insert test data
INSERT INTO bronze.orders (customer_id, order_date, total_amount, status)
VALUES 
    (101, '2024-01-15', 150.50, 'completed'),
    (102, '2024-01-16', 200.75, 'pending');
```

---

## 📊 What Tables Can Be Read?

The chatbot can read **any table** in your PostgreSQL database that:
- Exists in the schema you specify (default: `bronze`)
- Is accessible with the configured user credentials
- Has SELECT permissions for the user

**Example queries:**
- "Show me orders data" → reads `bronze.orders`
- "Display customers table" → reads `bronze.customers`
- "Show me recent orders" → reads `bronze.orders` with filters

---

## ✅ Quick Checklist

- [ ] `.env` file created
- [ ] `WAREHOUSE_TYPE=postgres` set
- [ ] PostgreSQL connection details configured
- [ ] PostgreSQL is running
- [ ] Database exists
- [ ] Schema exists (e.g., `bronze`)
- [ ] Tables exist in schema
- [ ] `psycopg2-binary` installed
- [ ] Test connection works

---

## 🚀 Once Configured

After setup, you can:

1. **Run chatbot CLI:**
   ```bash
   python scripts/run_agent.py "Show me orders data"
   ```

2. **Run web app:**
   ```bash
   python app.py
   # Open http://localhost:5000
   ```

3. **Use in code:**
   ```python
   from orchestration.chatbot_workflow import run_chatbot_query
   
   result = run_chatbot_query("Show me orders data", schema_name="bronze")
   ```

---

## 📝 Summary

**Code is ready ✅** - You just need to:
1. Create `.env` file
2. Set `WAREHOUSE_TYPE=postgres`
3. Configure PostgreSQL connection details
4. Make sure PostgreSQL is running
5. Make sure tables exist

That's it! 🎉

