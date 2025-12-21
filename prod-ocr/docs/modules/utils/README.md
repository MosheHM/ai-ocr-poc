# Utils Module

PDF manipulation and ZIP packaging utilities.

## Files

| File | Description |
|------|-------------|
| `__init__.py` | Exports `extract_pdf_pages`, `create_results_zip` |
| `pdf_utils.py` | PDF page extraction functions |
| `zip_utils.py` | ZIP file creation |

## Exports

```python
from modules.utils import (
    extract_pdf_pages,
    create_results_zip
)
```

---

## PDF Utilities (`pdf_utils.py`)

### extract_pdf_pages

Extract a range of pages from a PDF into a new PDF.

```python
pdf_bytes = extract_pdf_pages(
    pdf_path: str,     # Source PDF path
    start_page: int,   # Start page (1-indexed)
    end_page: int      # End page (1-indexed, inclusive)
) -> bytes            # New PDF as bytes
```

**Example:**

```python
from modules.utils import extract_pdf_pages

# Extract pages 3-5 from a PDF
pdf_bytes = extract_pdf_pages("document.pdf", 3, 5)

with open("pages_3-5.pdf", "wb") as f:
    f.write(pdf_bytes)
```

### combine_pdf_pages

Combine specific pages from a PDF into a new PDF.

```python
pdf_bytes = combine_pdf_pages(
    pdf_path: str,           # Source PDF path
    page_numbers: List[int]  # Pages to combine (1-indexed)
) -> bytes
```

**Example:**

```python
# Combine pages 1, 3, and 7
pdf_bytes = combine_pdf_pages("document.pdf", [1, 3, 7])
```

**Note:** Uses `pypdf` library. Falls back to returning original PDF if errors occur.

---

## ZIP Utilities (`zip_utils.py`)

### create_results_zip

Create a ZIP file containing all split PDFs and results JSON.

```python
zip_path = create_results_zip(
    output_dir: str,                              # Directory with split PDFs
    results_data: Dict[str, Any],                 # Extraction results dict
    zip_filename: str = "processing_results.zip" # ZIP file name
) -> str                                         # Path to created ZIP
```

**Example:**

```python
from modules.utils import create_results_zip

results = {
    "source_pdf": "combined.pdf",
    "total_documents": 2,
    "documents": [
        {"DOC_TYPE": "INVOICE", "FILE_PATH": "output/inv.pdf", "FILE_NAME": "inv.pdf"},
        {"DOC_TYPE": "OBL", "FILE_PATH": "output/obl.pdf", "FILE_NAME": "obl.pdf"}
    ]
}

zip_path = create_results_zip("output/", results, "results.zip")
```

### ZIP Contents

```
results.zip
├── extraction_results.json    # Full results data
├── inv.pdf                    # Split PDF files
└── obl.pdf
```

**Features:**
- Uses `ZIP_DEFLATED` compression
- Results JSON is pretty-printed (indent=2)
- Only includes files that exist on disk

---

## Dependencies

- `pypdf` - PDF manipulation
- `zipfile` (stdlib) - ZIP creation
