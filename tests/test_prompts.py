"""Tests for prompt loading functionality."""
import pytest
from modules.prompts import (
    load_prompt,
    get_classification_prompt,
    get_invoice_extraction_prompt,
    get_obl_extraction_prompt,
    get_hawb_extraction_prompt,
    get_packing_list_extraction_prompt,
    PromptLoader
)


class TestPromptLoader:
    """Tests for PromptLoader class."""
    
    def test_load_classification_prompt(self):
        """Test loading classification prompt."""
        prompt = get_classification_prompt()
        assert prompt is not None
        assert len(prompt) > 0
        assert "document type" in prompt.lower() or "classify" in prompt.lower()
    
    def test_load_invoice_prompt(self):
        """Test loading invoice extraction prompt."""
        prompt = get_invoice_extraction_prompt()
        assert prompt is not None
        assert len(prompt) > 0
        assert "invoice" in prompt.lower()
        assert "INVOICE_NO" in prompt or "invoice number" in prompt.lower()
    
    def test_load_obl_prompt(self):
        """Test loading OBL extraction prompt."""
        prompt = get_obl_extraction_prompt()
        assert prompt is not None
        assert len(prompt) > 0
        assert "OBL" in prompt or "bill of lading" in prompt.lower()
    
    def test_load_hawb_prompt(self):
        """Test loading HAWB extraction prompt."""
        prompt = get_hawb_extraction_prompt()
        assert prompt is not None
        assert len(prompt) > 0
        assert "HAWB" in prompt or "air waybill" in prompt.lower()
    
    def test_load_packing_list_prompt(self):
        """Test loading packing list extraction prompt."""
        prompt = get_packing_list_extraction_prompt()
        assert prompt is not None
        assert len(prompt) > 0
        assert "packing list" in prompt.lower()
    
    def test_prompt_caching(self):
        """Test that prompts are cached."""
        loader = PromptLoader()
        
        # Load twice
        prompt1 = loader.load_prompt("classification_prompt")
        prompt2 = loader.load_prompt("classification_prompt")
        
        # Should be the same object (cached)
        assert prompt1 is prompt2
    
    def test_list_available_prompts(self):
        """Test listing available prompts."""
        loader = PromptLoader()
        prompts = loader.list_available_prompts()
        
        assert len(prompts) >= 5
        assert "classification_prompt" in prompts
        assert "invoice_extraction_prompt" in prompts
        assert "obl_extraction_prompt" in prompts
        assert "hawb_extraction_prompt" in prompts
        assert "packing_list_extraction_prompt" in prompts
    
    def test_load_nonexistent_prompt(self):
        """Test loading a non-existent prompt raises error."""
        loader = PromptLoader()
        
        with pytest.raises(FileNotFoundError):
            loader.load_prompt("nonexistent_prompt")
    
    def test_reload_prompt(self):
        """Test reloading a prompt."""
        loader = PromptLoader()
        
        prompt1 = loader.load_prompt("classification_prompt")
        prompt2 = loader.reload_prompt("classification_prompt")
        
        # Content should be the same but might be different objects
        assert prompt1 == prompt2


class TestPromptContent:
    """Tests for prompt content quality."""
    
    def test_classification_prompt_has_document_types(self):
        """Test classification prompt lists all document types."""
        prompt = get_classification_prompt()
        
        assert "Invoice" in prompt
        assert "OBL" in prompt
        assert "HAWB" in prompt
        assert "Packing List" in prompt
    
    def test_invoice_prompt_has_required_fields(self):
        """Test invoice prompt includes all required fields."""
        prompt = get_invoice_extraction_prompt()
        
        required_fields = [
            "INVOICE_NO",
            "INVOICE_DATE",
            "CURRENCY_ID",
            "INCOTERMS",
            "INVOICE_AMOUNT",
            "CUSTOMER_ID"
        ]
        
        for field in required_fields:
            assert field in prompt, f"Field {field} not found in invoice prompt"
    
    def test_prompts_request_json_output(self):
        """Test that all extraction prompts request JSON output."""
        prompts = [
            get_invoice_extraction_prompt(),
            get_obl_extraction_prompt(),
            get_hawb_extraction_prompt(),
            get_packing_list_extraction_prompt()
        ]
        
        for prompt in prompts:
            assert "JSON" in prompt or "json" in prompt.lower()
