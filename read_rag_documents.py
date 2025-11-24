"""
Script to read Word documents from rag_documents folder and extract their content.
"""
import os
from pathlib import Path
from docx import Document
import json

def read_docx(file_path):
    """Read content from a Word document."""
    try:
        doc = Document(file_path)
        content = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                content.append(paragraph.text.strip())
        return "\n\n".join(content)
    except Exception as e:
        return f"Error reading {file_path}: {str(e)}"

def main():
    """Read all Word documents in rag_documents folder."""
    rag_folder = Path("rag_documents")
    documents = {}
    
    # Find all .docx files
    docx_files = list(rag_folder.glob("*.docx"))
    
    print(f"Found {len(docx_files)} Word documents:\n")
    
    for docx_file in docx_files:
        print(f"Reading: {docx_file.name}...")
        content = read_docx(docx_file)
        documents[docx_file.name] = {
            "path": str(docx_file),
            "content": content,
            "length": len(content)
        }
        print(f"  - Extracted {len(content)} characters\n")
    
    # Save extracted content to JSON for analysis
    output_file = "rag_documents_extracted.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Extracted content saved to: {output_file}")
    print(f"\nSummary:")
    for name, data in documents.items():
        print(f"  - {name}: {data['length']} characters")
    
    return documents

if __name__ == "__main__":
    main()

