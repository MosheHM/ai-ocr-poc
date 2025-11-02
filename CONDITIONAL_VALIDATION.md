# Conditional Validation Mode

## Overview

This feature enables **conditional processing** of PDF documents based on the presence of `.txt` ground truth files. This is designed to optimize API usage during testing and validation by only processing documents that have ground truth data available.

## Purpose

When running validation workflows (e.g., for testing or quality assurance), you often have a mix of documents:
- Some have `.txt` ground truth files (typically invoices)
- Some don't have `.txt` files (typically BOL, packing lists, etc.)

Without this feature, the system would:
- Call the Gemini API for ALL documents
- Waste API quota on documents that can't be validated
- Generate unnecessary costs

With conditional validation mode:
- Only documents with `.txt` ground truth files are processed
- Documents without `.txt` files are skipped with clear status reporting
- API calls are optimized for actual validation needs

## How It Works

### 1. Automatic .txt File Detection

The `ValidationWorkflow` automatically checks for a `.txt` file with the same base name as the PDF:

```
Example:
  PDF:  invoice_12345.PDF
  TXT:  invoice_12345.txt  ← Automatically detected
```

### 2. Conditional Processing Logic

```
IF .txt file exists:
  ├─ Load ground truth from .txt file
  ├─ Classify pages
  ├─ Extract data using Gemini API
  └─ Validate against ground truth
  
ELSE:
  └─ Skip processing and report as SKIPPED
```

### 3. Ground Truth Format

The `.txt` files should contain JSON data in one of these formats:

**Simple JSON:**
```json
{
  "INVOICE_NO": "12345",
  "INVOICE_DATE": "2025080100000000",
  "CURRENCY_ID": "USD",
  "INVOICE_AMOUNT": 1000.00
}
```

**JSON with OCC wrapper (automatically unwrapped):**
```json
{
  "OCC": {
    "INVOICE_NO": "12345",
    "INVOICE_DATE": "2025080100000000",
    "CURRENCY_ID": "USD",
    "INVOICE_AMOUNT": 1000.00
  }
}
```

## Usage

### Command Line

#### Enable validation mode (checks for .txt files):
```bash
python main.py document.pdf --validate-txt
```

#### Provide explicit ground truth:
```bash
python main.py document.pdf --ground-truth ground_truth.json
```

#### Normal extraction mode (no validation):
```bash
python main.py document.pdf
```

### Programmatic Usage

```python
from modules.workflows import ValidationWorkflow

# Create workflow
api_key = "your-gemini-api-key"
workflow = ValidationWorkflow(api_key)

# Process document (automatically checks for .txt file)
result = workflow.process_document("invoice.PDF")

# Check if processing was skipped
skipped = any("No .txt ground truth file" in err for err in result.errors)

if skipped:
    print("Document skipped - no .txt file found")
else:
    print(f"Validation score: {result.overall_score}%")
```

## Output Format

### Skipped Documents

When a document is skipped (no .txt file), the output includes:

**Console Report:**
```
================================================================================
Validation Report: document.PDF
================================================================================
Total Pages: 2
Success: True

Processing Status:
--------------------------------------------------------------------------------
⚠ SKIPPED: No .txt ground truth file found.
Extraction was not performed to avoid unnecessary Gemini API calls.

Note: Only documents with .txt ground truth files are processed
in validation mode for quality assurance and testing.
```

**JSON Output:**
```json
{
  "pdf_path": "document.PDF",
  "total_pages": 2,
  "success": true,
  "skipped": true,
  "overall_score": null,
  "classifications": [],
  "extractions": [],
  "validations": [],
  "errors": [
    "No .txt ground truth file found. Extraction skipped to avoid unnecessary API calls."
  ]
}
```

### Processed Documents

When a document has a .txt file, normal validation output is provided with:
- Page classifications
- Extracted data
- Validation results with field-by-field comparison
- Overall validation score

## Use Cases

### 1. Batch Testing with Mixed Documents

```bash
# Directory structure:
# sampels/
#   ├── invoice_001.PDF
#   ├── invoice_001.txt      ← Has ground truth
#   ├── invoice_002.PDF
#   ├── invoice_002.txt      ← Has ground truth
#   ├── bol_001.PDF          ← No .txt file
#   └── packing_001.PDF      ← No .txt file

# Process all documents - only invoices will be validated
for pdf in sampels/*.PDF; do
    python main.py "$pdf" --validate-txt
done
```

Result:
- invoice_001.PDF: ✓ Processed and validated
- invoice_002.PDF: ✓ Processed and validated
- bol_001.PDF: ⚠ Skipped (no .txt)
- packing_001.PDF: ⚠ Skipped (no .txt)

### 2. Quality Assurance Workflow

```python
from pathlib import Path
from modules.workflows import ValidationWorkflow

workflow = ValidationWorkflow(api_key)
results = []

for pdf_file in Path("sampels").glob("*.PDF"):
    result = workflow.process_document(str(pdf_file))
    
    skipped = any("No .txt ground truth file" in err for err in result.errors)
    
    if skipped:
        print(f"⚠ {pdf_file.name}: Skipped (no ground truth)")
    else:
        print(f"✓ {pdf_file.name}: Score {result.overall_score:.2f}%")
        results.append(result)

# Calculate average score for processed documents
avg_score = sum(r.overall_score for r in results) / len(results)
print(f"\nAverage validation score: {avg_score:.2f}%")
```

## Benefits

1. **Cost Optimization**: Reduces unnecessary Gemini API calls
2. **Clear Reporting**: Explicitly shows which documents were skipped
3. **Flexible Testing**: Mix validated and non-validated documents
4. **Automatic Detection**: No manual configuration needed
5. **Graceful Handling**: Skipping is not treated as an error

## API Functions

### find_ground_truth_txt(pdf_path: str) -> Optional[str]
Finds the .txt ground truth file for a given PDF.

**Parameters:**
- `pdf_path`: Path to the PDF file

**Returns:**
- Path to .txt file if exists, None otherwise

### load_ground_truth_from_txt(txt_path: str) -> Optional[Dict[str, Any]]
Loads ground truth data from a .txt file.

**Parameters:**
- `txt_path`: Path to the .txt file

**Returns:**
- Dictionary with ground truth data, or None if loading fails

**Note:** Automatically unwraps OCC wrapper if present.

## Testing

Run the test suite to verify conditional processing:

```bash
# Run all tests
pytest tests/test_conditional_processing.py -v

# Run specific test
pytest tests/test_conditional_processing.py::TestConditionalProcessing::test_workflow_skips_without_txt_file -v
```

## Migration Notes

This feature is **backward compatible**:
- Existing code without `--validate-txt` flag works unchanged
- ExtractionWorkflow (normal mode) is not affected
- ValidationWorkflow with explicit ground truth still works

## See Also

- [README.md](README.md) - Main documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [modules/workflows/validation_workflow.py](modules/workflows/validation_workflow.py) - Implementation
