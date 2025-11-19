# S3 File Loading Guide

This guide explains how to use the S3 file loading functionality with PostgreSQL.

## Overview

The platform now supports:
1. **Loading files from S3 into PostgreSQL** (CSV, JSON, Parquet, Excel)
2. **Analyzing S3 files** without loading
3. **Complete workflow from S3 to Silver** (S3 → analysis → Data Vault → dbt)
4. **Listing files in S3 buckets**

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
# Installs boto3 for AWS S3 access
```

### 2. Configure AWS Credentials

**Option A: Environment Variables (.env file)**

```env
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_S3_BUCKET=my-data-bucket  # Optional: default bucket
```

**Option B: AWS IAM Role** (if running on EC2/ECS/Lambda)
- No credentials needed - uses IAM role automatically

**Option C: AWS Credentials File** (`~/.aws/credentials`)
```ini
[default]
aws_access_key_id = your_access_key
aws_secret_access_key = your_secret_key
```

### 3. Configure PostgreSQL

```env
WAREHOUSE_TYPE=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=saarinsights
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

## Usage

### Option 1: Load File from S3

```bash
# Load CSV file from S3
python scripts/run_agent.py load-s3 --s3-bucket my-bucket --s3-key data/orders.csv

# Load JSON file
python scripts/run_agent.py load-s3 --s3-bucket my-bucket --s3-key data/customers.json
```

### Option 2: Analyze S3 File (No Loading)

```python
from agents.schema_agent import SchemaUnderstandingAgent

agent = SchemaUnderstandingAgent()

# Using S3 path string
metadata = agent.analyze("s3://my-bucket/data/orders.csv")

# Or using bucket/key
metadata = agent.analyze_s3_file("my-bucket", "data/orders.csv")
```

### Option 3: Complete Workflow from S3

```bash
# Using S3 path string
python scripts/run_agent.py bronze-to-silver --file s3://my-bucket/data/orders.csv

# Or using bucket/key
python scripts/run_agent.py bronze-to-silver --s3-bucket my-bucket --s3-key data/orders.csv
```

### Option 4: List S3 Files

```python
from agents.s3_loader_agent import S3LoaderAgent

loader = S3LoaderAgent()
files = loader.list_s3_files("my-bucket", prefix="bronze/")
print(f"Found {len(files)} files")
```

## S3 Path Formats

### Format 1: S3 Path String (Recommended)

```python
s3_path = "s3://bucket-name/path/to/file.csv"
```

**Usage:**
```python
# Works with schema agent
metadata = schema_agent.analyze("s3://my-bucket/data/orders.csv")

# Works with workflow
result = run_bronze_to_silver_from_file("s3://my-bucket/data/orders.csv")
```

### Format 2: Bucket and Key Separately

```python
bucket = "my-bucket"
key = "data/orders.csv"
```

**Usage:**
```python
loader = S3LoaderAgent()
result = loader.load_s3_file(bucket, key)
```

## Examples

### Example 1: Load S3 File

```python
from agents.s3_loader_agent import S3LoaderAgent

loader = S3LoaderAgent()
result = loader.load_s3_file(
    bucket="my-data-bucket",
    key="bronze/orders.csv",
    schema_name="bronze"
)

# Result:
# {
#   "status": "success",
#   "s3_path": "s3://my-data-bucket/bronze/orders.csv",
#   "table_name": "orders",
#   "row_count": 1000,
#   "columns": 5
# }
```

### Example 2: Analyze S3 File

```python
from agents.schema_agent import SchemaUnderstandingAgent

agent = SchemaUnderstandingAgent()

# Method 1: S3 path string
metadata = agent.analyze("s3://my-bucket/data/orders.csv")

# Method 2: Bucket and key
metadata = agent.analyze_s3_file("my-bucket", "data/orders.csv")
```

### Example 3: Complete Workflow

```python
from orchestration import run_bronze_to_silver_from_s3

# From S3
result = run_bronze_to_silver_from_s3("my-bucket", "data/orders.csv")

# Or using S3 path string
from orchestration import run_bronze_to_silver_from_file
result = run_bronze_to_silver_from_file("s3://my-bucket/data/orders.csv")
```

### Example 4: List Files

```python
from agents.s3_loader_agent import S3LoaderAgent

loader = S3LoaderAgent()
files = loader.list_s3_files("my-bucket", prefix="bronze/")

for file_key in files:
    print(f"Found: {file_key}")
```

## Supported File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| CSV | `.csv` | UTF-8 encoding |
| JSON | `.json` | Array of objects |
| Parquet | `.parquet` | Efficient, compressed |
| Excel | `.xlsx`, `.xls` | First sheet only |

## S3 Bucket Structure

Recommended structure:

```
my-data-bucket/
├── bronze/
│   ├── orders.csv
│   ├── customers.json
│   └── products.parquet
├── silver/
│   └── (processed data)
└── gold/
    └── (analytics data)
```

## Troubleshooting

### "AWS credentials not found"
- Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `.env`
- Or configure AWS credentials file: `~/.aws/credentials`
- Or use IAM role if running on AWS

### "Access Denied"
- Check S3 bucket permissions
- Verify IAM user/role has `s3:GetObject` permission
- Check bucket policy

### "File not found in S3"
- Verify bucket name is correct
- Check key (path) is correct
- Ensure file exists in S3

### "Connection timeout"
- Check network connectivity
- Verify AWS region is correct
- Check firewall/proxy settings

## Security Best Practices

1. **Use IAM Roles** (preferred for production)
   - No credentials in code
   - Automatic rotation
   - Least privilege access

2. **Environment Variables**
   - Store credentials in `.env` (not in code)
   - Use AWS Secrets Manager for production

3. **Bucket Policies**
   - Restrict access to specific IPs
   - Use bucket policies for fine-grained control

4. **Encryption**
   - Enable S3 bucket encryption
   - Use KMS for key management

## Cost Considerations

- **S3 Storage**: ~$0.023 per GB/month
- **Data Transfer**: Free within same region
- **API Requests**: Minimal cost (GET requests are cheap)

## Next Steps

After loading from S3:
1. Analyze with SchemaUnderstandingAgent
2. Generate Data Vault models
3. Create Silver layer with dbt
4. Build Gold layer for analytics

See `examples/s3_loading_example.py` for complete examples.

