"""Pytest configuration and shared fixtures."""
import pytest
import sys
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_invoice_data():
    """Sample invoice data for testing."""
    return {
        "INVOICE_NO": "0004833/E",
        "INVOICE_DATE": "2025073000000000",
        "CURRENCY_ID": "EUR",
        "INCOTERMS": "FCA",
        "INVOICE_AMOUNT": 7632.00,
        "CUSTOMER_ID": "D004345"
    }


@pytest.fixture
def sample_obl_data():
    """Sample OBL data for testing."""
    return {
        "CUSTOMER_NAME": "ABC Corporation",
        "WEIGHT": 1500.5,
        "VOLUME": 45.2,
        "INCOTERMS": "FOB"
    }


@pytest.fixture
def sample_hawb_data():
    """Sample HAWB data for testing."""
    return {
        "CUSTOMER_NAME": "XYZ Logistics",
        "CURRENCY": "USD",
        "CARRIER": "Air Freight Co",
        "HAWB_NUMBER": "HAWB-2025-001234",
        "PIECES": 25,
        "WEIGHT": 450.5
    }


@pytest.fixture
def sample_packing_list_data():
    """Sample packing list data for testing."""
    return {
        "CUSTOMER_NAME": "DEF Manufacturing",
        "PIECES": 100,
        "WEIGHT": 2500.0
    }


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing without API calls."""
    class MockLLMClient:
        def generate_json_content(self, **kwargs):
            return {}
        
        def generate_content(self, **kwargs):
            return ""
    
    return MockLLMClient()
