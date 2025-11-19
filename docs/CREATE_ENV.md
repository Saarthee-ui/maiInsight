# How to Create .env File

## Quick Steps

### Option 1: Copy Template (Recommended)

1. **Copy the template file**:
   ```powershell
   # In PowerShell (Windows)
   Copy-Item env.template .env
   
   # Or in Command Prompt
   copy env.template .env
   ```

2. **Edit the .env file** with your actual credentials:
   - Open `.env` in any text editor (VS Code, Notepad, etc.)
   - Replace `your_*_here` placeholders with your actual values
   - Save the file

### Option 2: Create Manually

1. **Create a new file** named `.env` in the project root
2. **Copy the content** from `env.template` 
3. **Fill in your values**

### Option 3: Use Command Line

```powershell
# Create .env file
New-Item -Path .env -ItemType File

# Then edit it with your editor
code .env
```

---

## Minimum Required Configuration

For **testing without a warehouse** (just to test agents):

```env
# LLM Configuration (choose one)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
```

For **full functionality** (with warehouse):

```env
# LLM
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Warehouse
WAREHOUSE_TYPE=snowflake
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
```

---

## Configuration Examples

### Example 1: Using OpenAI + Snowflake

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-proj-abc123xyz...

WAREHOUSE_TYPE=snowflake
SNOWFLAKE_ACCOUNT=abc12345
SNOWFLAKE_USER=myuser
SNOWFLAKE_PASSWORD=mypassword
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=MY_DB
SNOWFLAKE_SCHEMA_BRONZE=BRONZE
SNOWFLAKE_SCHEMA_SILVER=SILVER
SNOWFLAKE_SCHEMA_GOLD=GOLD
```

### Example 2: Using Ollama (Free, Local)

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434

WAREHOUSE_TYPE=snowflake
SNOWFLAKE_ACCOUNT=abc12345
SNOWFLAKE_USER=myuser
SNOWFLAKE_PASSWORD=mypassword
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=MY_DB
```

**Note**: For Ollama, first install it:
1. Download from https://ollama.ai
2. Install and run
3. Pull model: `ollama pull llama3.1`

### Example 3: Using Anthropic Claude

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-abc123...

WAREHOUSE_TYPE=snowflake
SNOWFLAKE_ACCOUNT=abc12345
SNOWFLAKE_USER=myuser
SNOWFLAKE_PASSWORD=mypassword
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=MY_DB
```

---

## Where to Get API Keys

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign in or create account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

### Anthropic API Key
1. Go to https://console.anthropic.com/
2. Sign in or create account
3. Navigate to API Keys
4. Create new key
5. Copy the key (starts with `sk-ant-`)

### Ollama (Free)
1. Download from https://ollama.ai
2. Install and run
3. No API key needed - runs locally
4. Pull model: `ollama pull llama3.1`

---

## Snowflake Connection Details

### How to Find Your Snowflake Account
- Format: `account.region.cloud` (e.g., `abc12345.us-east-1`)
- Or just the account identifier: `abc12345`
- Check your Snowflake URL: `https://abc12345.snowflakecomputing.com`

### How to Find Your Warehouse
- In Snowflake, go to **Warehouses** in the left menu
- Your warehouse name is listed there
- Common names: `COMPUTE_WH`, `ANALYTICS_WH`, etc.

### How to Find Your Database
- In Snowflake, go to **Databases** in the left menu
- Your database name is listed there

---

## Verify Your .env File

After creating `.env`, test it:

```python
# Test configuration loading
from config import settings

print(f"LLM Provider: {settings.llm_provider}")
print(f"Warehouse Type: {settings.warehouse_type}")
print(f"Database: {settings.snowflake_database}")
```

Or run the test script:

```bash
python test_setup.py
```

---

## Security Notes

⚠️ **Important**:
- `.env` file is in `.gitignore` - it won't be committed to git
- **Never commit** your `.env` file to version control
- **Never share** your API keys or passwords
- Use different `.env` files for different environments (dev, prod)

---

## Troubleshooting

### "OPENAI_API_KEY not set"
- Check that `.env` file exists in project root
- Verify `OPENAI_API_KEY=sk-...` is in the file
- Make sure there are no spaces around `=`
- Restart your Python session after creating `.env`

### "Warehouse connection failed"
- Verify Snowflake credentials are correct
- Check account format (should be just identifier, not full URL)
- Test connection manually in Snowflake web UI

### "File not found"
- Make sure `.env` is in the project root (same folder as `requirements.txt`)
- Check file name is exactly `.env` (not `.env.txt`)

---

## Next Steps

After creating `.env`:

1. **Test configuration**:
   ```bash
   python test_setup.py
   ```

2. **Test warehouse connection**:
   ```python
   from tools.warehouse import warehouse
   tables = warehouse.list_tables("BRONZE")
   print(f"Found {len(tables)} tables")
   ```

3. **Run your first transformation**:
   ```bash
   python scripts/run_agent.py bronze-to-silver --schema BRONZE --table your_table
   ```

