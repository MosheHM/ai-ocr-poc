# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered document classification and data extraction POC using Google Gemini API. Processes PDFs to identify document types (Invoice, OBL, HAWB, Packing List) and extract structured data.

## Common Commands

```bash
# Install dependencies
uv sync                      # Recommended: Install with uv
pip install -r requirements.txt  # Legacy: Install with pip

# Run application
uv run python main.py path/to/document.pdf
uv run python main.py path/to/document.pdf --validate-txt
uv run python main.py path/to/document.pdf --ground-truth ground_truth.json

# Run tests
uv run pytest tests/ -v
uv run pytest tests/test_conditional_processing.py -v  # Single test file
uv run pytest -m unit  # Run only unit tests
uv run pytest -m integration  # Run only integration tests

# Demo scripts (in examples/)
uv run python examples/demo_conditional_validation.py
uv run python examples/demo_summary.py
```

## Project Structure

```
ai-ocr-poc/
├── main.py          # Entry point
├── modules/         # Core source code
├── tests/           # Test files
├── examples/        # Demo scripts and examples
├── scripts/         # Utility scripts
└── samples/         # Sample documents
```

## Architecture

### Data Flow
```
PDF Input → Classification (Gemini AI) → Document Grouping → Extraction → Validation (optional) → JSON Output
```

### Key Components

**Workflows** (`modules/workflows/`):
- `BaseWorkflow` - Abstract base with shared classification/extraction logic
- `ExtractionWorkflow` - Production use (extract only)
- `ValidationWorkflow` - Testing/QA (extract + validate against ground truth)

**Core Modules**:
- `modules/types/` - All type definitions, enums, protocols, and `DOCUMENT_SCHEMAS`
- `modules/llm/client.py` - `GeminiLLMClient` for API calls
- `modules/document_classifier/` - `PDFDocumentClassifier` for page type identification
- `modules/document_splitter/` - `DocumentSplitter` for splitting PDFs by document type
- `modules/extractors/` - Type-specific extractors with `ExtractorFactory`
- `modules/validators/` - `PerformanceValidator` for ground truth comparison
- `modules/prompts/` - `.txt` prompt files with `PromptLoader` (cached via `@lru_cache`)
- `modules/utils/` - PDF manipulation and document grouping utilities

**Document Splitting** (`modules/document_splitter/`):
```python
from modules import split_and_extract_documents

# Split PDF into separate files by document type
result = split_and_extract_documents(
    "combined_docs.pdf",
    "output/split_docs"
)
# Returns JSON with file locations for each extracted document
```

### Design Patterns
- **Factory Pattern** - `ExtractorFactory.create_extractor()` for type-specific extractors
- **Protocol/Interface Pattern** - `LLMProvider`, `DocumentClassifier`, `DocumentExtractor`, `Validator`
- **Template Method Pattern** - `BaseWorkflow` defines pipeline, subclasses override behavior

## Document Types

Defined in `modules/types/__init__.py`:
- `INVOICE` - Commercial invoices
- `OBL` - Ocean Bill of Lading
- `HAWB` - House Air Waybill
- `PACKING_LIST` - Packing lists
- `UNKNOWN` - Unclassified pages

## Testing

Test markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`

Tests in `tests/` directory follow pattern `test_*.py`. Fixtures defined in `tests/conftest.py`.

## Configuration

- **API Key**: Set `GEMINI_API_KEY` environment variable
- **Models**: Default is `gemini-2.5-flash`, configurable in `GeminiModel` enum

## Adding New Document Types

1. Add to `DocumentType` enum in `modules/types/__init__.py`
2. Add schema to `DOCUMENT_SCHEMAS`
3. Create extractor class inheriting from `BaseExtractor` in `modules/extractors/`
4. Register in `ExtractorFactory.create_extractor()`
5. Add extraction prompt in `modules/prompts/`
