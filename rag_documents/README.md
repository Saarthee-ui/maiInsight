# RAG Documents Directory

This directory contains your custom RAG (Retrieval Augmented Generation) files that will be used by the VectorBuildAgent to provide context-aware responses.

## Folder Structure

```
rag_documents/
├── documentation/     # Documentation files (PDFs, markdown, text files)
├── schemas/          # Database schema definitions (JSON, YAML, SQL)
├── examples/         # Example transformations, queries, use cases
└── rules/            # Business rules, best practices, guidelines
```

## Supported File Types

- **Text Files**: `.txt`, `.md`, `.markdown`
- **PDFs**: `.pdf` (requires PDF parser)
- **JSON**: `.json` (schema definitions, configurations)
- **YAML**: `.yaml`, `.yml` (configurations, schemas)
- **SQL**: `.sql` (queries, schema definitions)
- **Word Documents**: `.docx` (requires docx parser)
- **CSV**: `.csv` (structured data)

## How It Works

1. **Place your files** in the appropriate subfolder
2. **Run the ingestion script** (to be created) to process and embed your documents
3. **The VectorBuildAgent** will automatically search these documents during conversations
4. **The model** will use relevant document chunks to enhance its responses

## Example Usage

### Documentation Folder
- `data_warehouse_guide.pdf` - Your data warehouse documentation
- `transformation_best_practices.md` - Best practices guide
- `api_documentation.txt` - API reference

### Schemas Folder
- `sales_schema.json` - Sales database schema
- `customer_schema.yaml` - Customer database schema
- `warehouse_structure.sql` - Complete warehouse structure

### Examples Folder
- `sample_transformations.txt` - Example transformation queries
- `use_cases.md` - Common use cases and solutions
- `query_patterns.sql` - Reusable query patterns

### Rules Folder
- `naming_conventions.md` - Naming standards
- `data_quality_rules.txt` - Data quality guidelines
- `business_rules.json` - Business logic rules

## Next Steps

1. Add your files to the appropriate folders
2. The ingestion system will process them automatically (when implemented)
3. Your documents will be searchable via semantic similarity
4. The agent will use them to provide better, context-aware responses

