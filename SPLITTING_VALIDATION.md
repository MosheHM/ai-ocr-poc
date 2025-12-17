# PDF Splitting Validation

This feature validates PDF document splitting results against XML ground truth files.

## Overview

The PDF splitting validation system compares the AI's PDF splitting results (how it identified and grouped document pages) against XML ground truth files that contain the expected splitting results. This is useful for:

- Evaluating the accuracy of the document classification and grouping
- Identifying which document types are being correctly identified
- Measuring the precision of page-level splitting

## Components

### 1. XML Parser (`modules/validators/xml_parser.py`)

Parses `SplittedResult` XML files that contain ground truth information about how a PDF should be split.

**Key classes:**
- `PageInfo`: Information about a single page (page number, rotation)
- `SplitDocumentInfo`: Information about a split document (type, pages, filing info)
- `SplittedResultInfo`: Complete information from the XML file

**Example usage:**
```python
from modules.validators import parse_splitted_result_xml

ground_truth = parse_splitted_result_xml('path/to/file.xml')
print(f"Total documents: {ground_truth.total_documents}")
print(f"Documents by type: {ground_truth.get_documents_by_type()}")
```

### 2. Splitting Validator (`modules/validators/splitting_validator.py`)

Validates PDF splitting results against parsed XML ground truth.

**Metrics calculated:**
- Document count match: Whether predicted and ground truth have same number of documents
- Document type accuracy: Percentage of documents with correct type
- Page count accuracy: Percentage of documents with correct page count
- Page numbers accuracy: Percentage of documents with exact page number matches
- Overall score: Weighted average of all metrics (40% type, 30% count, 30% pages)

**Example usage:**
```python
from modules.validators import SplittingValidator

validator = SplittingValidator()
result = validator.validate(processing_result, ground_truth)

print(f"Overall Score: {result.overall_score:.1f}%")
print(f"Type Accuracy: {result.document_type_accuracy:.1f}%")
```

### 3. Splitting Validation Workflow (`modules/workflows/splitting_validation_workflow.py`)

Combines PDF processing with splitting validation in a single workflow.

**Example usage:**
```python
from modules.workflows import SplittingValidationWorkflow

workflow = SplittingValidationWorkflow(api_key)
result = workflow.process_document_with_xml_ground_truth(
    'path/to/document.pdf',
    'path/to/ground_truth.xml'
)
```

## Usage

### Command-Line Validation

Use the `validate_splitting.py` script to validate PDFs against XML ground truth:

```bash
# Validate all PDFs in the sampels/combined-sampels directory
python validate_splitting.py

# Validate a specific PDF
python validate_splitting.py --pdf sampels/combined-sampels/81124047_ORG_pxutqxvrveky75v6dwhymg00000000.PDF

# Specify custom directories
python validate_splitting.py --samples-dir path/to/samples --output-dir path/to/results
```

**Requirements:**
- Set `GEMINI_API_KEY` environment variable
- Ensure matching XML file exists for each PDF (same name, different extension)

### Programmatic Usage

```python
import os
from pathlib import Path
from modules.workflows import SplittingValidationWorkflow
from modules.validators import parse_splitted_result_xml

# Setup
api_key = os.getenv('GEMINI_API_KEY')
workflow = SplittingValidationWorkflow(api_key)

# Process and validate
result = workflow.process_document_with_xml_ground_truth(
    'document.pdf',
    'document.xml'
)

# Access results
processing_result = result['processing_result']
splitting_validation = result['splitting_validation']
ground_truth = result['ground_truth']

# Generate report
report = workflow.generate_combined_report(
    processing_result,
    splitting_validation,
    ground_truth
)
print(report)
```

## XML Ground Truth Format

The XML files should follow the `SplittedResult` format:

```xml
<?xml version='1.0' encoding='UTF-8' ?>
<SplittedResult>
 <ParentComId>unique_id</ParentComId>
 <Owner>OWNER_NAME</Owner>
 <User>USER_NAME</User>
 <FilePath>\\path\\to\\original.PDF</FilePath>
 <SplittedDocs>
  <SplitDoc>
   <Entname>ENTITY</Entname>
   <PrimaryNum>12345</PrimaryNum>
   <DocType>FSI</DocType>
   <ProcessedFile>\\path\\to\\output.pdf</ProcessedFile>
   <Pages>
    <Page>
     <PageNum>1</PageNum>
     <Rotate>0</Rotate>
    </Page>
   </Pages>
   <FilingDocTypeCode>FSI</FilingDocTypeCode>
   <FilingDocTypeName>Supplier Invoice</FilingDocTypeName>
  </SplitDoc>
  <!-- More SplitDoc elements... -->
 </SplittedDocs>
</SplittedResult>
```

## Document Type Mapping

The following DocType codes are mapped to internal document types:

| XML Code | XML Name | Internal Type |
|----------|----------|---------------|
| FSI | Supplier Invoice | Invoice |
| FPL | Packing List | Packing List |
| OBL | Ocean Bill of Lading | OBL |
| HAWB | House Air Waybill | HAWB |
| FWA | Waybill | HAWB |

## Output

### Console Report

The validation script produces a detailed console report showing:

```
PDF Splitting Validation Report
================================================================================

Summary:
  Predicted Documents: 2
  Ground Truth Documents: 2
  Document Count Match: ✓

Accuracy Metrics:
  Document Type Accuracy: 100.0%
  Page Count Accuracy: 100.0%
  Page Numbers Accuracy: 100.0%
  Overall Score: 100.0%

Document-by-Document Comparison:
--------------------------------------------------------------------------------

Document #1:
  Predicted: Invoice
    Pages: 1 ([1])
  Ground Truth: Supplier Invoice
    Pages: [1]
  Type Match: ✓
  Page Count Match: ✓
  Page Numbers Match: ✓
  Exact Match: ✓
```

### JSON Output

Detailed results are saved in JSON format:

```json
{
  "pdf_path": "document.pdf",
  "xml_path": "document.xml",
  "timestamp": "2025-10-30T14:42:54.296Z",
  "processing": {
    "total_pages": 2,
    "success": true,
    "total_documents": 2,
    "documents": [
      {
        "type": "Invoice",
        "pages": [1],
        "page_range": "1"
      }
    ]
  },
  "splitting_validation": {
    "total_documents_predicted": 2,
    "total_documents_ground_truth": 2,
    "document_count_match": true,
    "document_type_accuracy": 100.0,
    "page_count_accuracy": 100.0,
    "page_numbers_accuracy": 100.0,
    "overall_score": 100.0
  }
}
```

## Testing

Run the tests to verify the validation functionality:

```bash
# Run all splitting validation tests
python -m pytest tests/test_splitting_validation.py -v

# Run all tests
python -m pytest tests/ --ignore=tests/legacy -v
```

## Examples

The `sampels/combined-sampels` directory contains example PDFs and their matching XML ground truth files for testing and validation.
