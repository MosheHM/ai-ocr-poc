# Tests Directory

This directory contains the pytest-based test suite for the AI OCR POC application.

## Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_prompts.py          # Tests for prompt loading
├── test_extractors.py       # Tests for document extractors
├── test_validators.py       # Tests for validation logic
├── test_workflows.py        # Tests for workflow orchestration
└── test_integration.py      # Integration tests
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=modules --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_prompts.py
```

### Run with verbose output
```bash
pytest -v
```

### Run specific test
```bash
pytest tests/test_prompts.py::test_load_classification_prompt
```

## Test Categories

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test components working together
- **Functional Tests**: Test complete workflows end-to-end

## Requirements

```bash
pip install pytest pytest-cov
```
