"""Tests for validator module."""
import pytest
from modules.types import DocumentType, ExtractionResult, ValidationResult
from modules.validators import PerformanceValidator


class TestPerformanceValidator:
    """Tests for PerformanceValidator class."""
    
    def test_validate_perfect_match(self, sample_invoice_data):
        """Test validation with perfect match."""
        validator = PerformanceValidator()
        
        extraction = ExtractionResult(
            page_number=1,
            document_type=DocumentType.INVOICE,
            data=sample_invoice_data.copy(),
            success=True
        )
        
        result = validator.validate(extraction, sample_invoice_data)
        
        assert result.score == 100.0
        assert result.correct_fields == result.total_fields
        assert result.correct_fields == 6
    
    def test_validate_partial_match(self, sample_invoice_data):
        """Test validation with partial match."""
        validator = PerformanceValidator()
        
        extracted_data = sample_invoice_data.copy()
        extracted_data["INCOTERMS"] = "FOB"  # Different from ground truth
        
        extraction = ExtractionResult(
            page_number=1,
            document_type=DocumentType.INVOICE,
            data=extracted_data,
            success=True
        )
        
        result = validator.validate(extraction, sample_invoice_data)
        
        assert result.score < 100.0
        assert result.score > 0.0
        assert result.correct_fields == 5
        assert result.total_fields == 6
    
    def test_validate_with_missing_fields(self, sample_invoice_data):
        """Test validation with missing fields."""
        validator = PerformanceValidator()
        
        # Extract only some fields
        extracted_data = {
            "INVOICE_NO": sample_invoice_data["INVOICE_NO"],
            "INVOICE_AMOUNT": sample_invoice_data["INVOICE_AMOUNT"]
        }
        
        extraction = ExtractionResult(
            page_number=1,
            document_type=DocumentType.INVOICE,
            data=extracted_data,
            success=True
        )
        
        result = validator.validate(extraction, sample_invoice_data)
        
        # Should track missing fields
        assert result.total_fields == 6  # All ground truth fields
        assert result.correct_fields == 2  # Only 2 extracted correctly
        assert result.score < 50.0
        
        # Check that missing fields are in comparison
        assert "INVOICE_DATE" in result.field_comparison
        assert result.field_comparison["INVOICE_DATE"]["extracted"] is None
        assert result.field_comparison["INVOICE_DATE"]["correct"] is False
    
    def test_validate_with_empty_ground_truth_field(self):
        """Test validation tracks fields with empty ground truth."""
        validator = PerformanceValidator()
        
        extraction = ExtractionResult(
            page_number=1,
            document_type=DocumentType.INVOICE,
            data={"INVOICE_NO": "12345"},
            success=True
        )
        
        ground_truth = {
            "INVOICE_NO": "12345",
            "CUSTOMER_ID": ""  # Empty but should be tracked
        }
        
        result = validator.validate(extraction, ground_truth)
        
        # Should track CUSTOMER_ID even though it's empty in ground truth
        assert "CUSTOMER_ID" in result.field_comparison
        assert result.field_comparison["CUSTOMER_ID"]["extracted"] is None
        assert result.field_comparison["CUSTOMER_ID"]["ground_truth"] == ""
        assert result.field_comparison["CUSTOMER_ID"]["correct"] is False
    
    def test_validate_no_ground_truth(self):
        """Test validation without ground truth."""
        validator = PerformanceValidator()
        
        extraction = ExtractionResult(
            page_number=1,
            document_type=DocumentType.INVOICE,
            data={"INVOICE_NO": "12345"},
            success=True
        )
        
        result = validator.validate(extraction, None)
        
        assert result.score == 0.0
        assert result.total_fields == 0
        assert result.correct_fields == 0
    
    def test_validate_failed_extraction(self):
        """Test validation with failed extraction."""
        validator = PerformanceValidator()
        
        extraction = ExtractionResult(
            page_number=1,
            document_type=DocumentType.INVOICE,
            data={},
            success=False,
            error_message="Extraction failed"
        )
        
        result = validator.validate(extraction, {"INVOICE_NO": "12345"})
        
        assert result.score == 0.0
        assert result.total_fields == 0
    
    def test_compare_numeric_values(self):
        """Test numeric value comparison."""
        validator = PerformanceValidator()
        
        # Should handle float precision
        assert validator._compare_values(7632.00, 7632.0)
        assert validator._compare_values(7632, 7632.00)
        assert not validator._compare_values(7632.00, 7633.00)
    
    def test_compare_string_values(self):
        """Test string value comparison."""
        validator = PerformanceValidator()
        
        # Should trim whitespace
        assert validator._compare_values("FCA", "FCA")
        assert validator._compare_values("FCA ", "FCA")
        assert validator._compare_values(" FCA", "FCA")
        assert not validator._compare_values("FCA", "FOB")
    
    def test_compare_null_values(self):
        """Test null value comparison."""
        validator = PerformanceValidator()
        
        assert validator._compare_values(None, None)
        assert not validator._compare_values(None, "value")
        assert not validator._compare_values("value", None)
    
    def test_validate_obl_document(self, sample_obl_data):
        """Test validation with OBL document."""
        validator = PerformanceValidator()
        
        extraction = ExtractionResult(
            page_number=1,
            document_type=DocumentType.OBL,
            data=sample_obl_data.copy(),
            success=True
        )
        
        result = validator.validate(extraction, sample_obl_data)
        
        assert result.score == 100.0
        assert result.document_type == DocumentType.OBL
