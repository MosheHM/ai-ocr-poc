"""Validator module for assessing extraction performance against ground truth."""
from typing import Dict, Any, Optional
from modules.types import ExtractionResult, ValidationResult, DocumentType, DOCUMENT_SCHEMAS


class PerformanceValidator:
    """Validator for comparing extracted data against ground truth."""
    
    def validate(
        self,
        extracted: ExtractionResult,
        ground_truth: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate extracted data against ground truth.
        
        Args:
            extracted: The extraction result to validate
            ground_truth: Ground truth data to compare against (optional)
        
        Returns:
            ValidationResult with comparison details
        """
        if ground_truth is None or not extracted.success:
            # No ground truth or extraction failed
            return ValidationResult(
                page_number=extracted.page_number,
                document_type=extracted.document_type,
                extracted=extracted.data,
                ground_truth=ground_truth,
                field_comparison={},
                total_fields=0,
                correct_fields=0,
                score=0.0
            )
        
        # Handle OCC wrapper if present in ground truth
        gt_fields = ground_truth.get('OCC', ground_truth)
        
        field_comparison = {}
        total_fields = 0
        correct_fields = 0
        
        # Get expected fields for this document type
        expected_fields = []
        if extracted.document_type in DOCUMENT_SCHEMAS:
            expected_fields = list(DOCUMENT_SCHEMAS[extracted.document_type].keys())
        
        # Compare each extracted field with ground truth
        for field_name, extracted_value in extracted.data.items():
            if field_name in gt_fields:
                gt_value = gt_fields[field_name]
                is_correct = self._compare_values(extracted_value, gt_value)
                
                field_comparison[field_name] = {
                    'extracted': extracted_value,
                    'ground_truth': gt_value,
                    'correct': is_correct
                }
                
                total_fields += 1
                if is_correct:
                    correct_fields += 1
        
        # Check for fields in ground truth that are missing from extraction
        # This includes fields that the model didn't recognize, even if ground truth is empty
        for field_name in expected_fields:
            if field_name in gt_fields and field_name not in extracted.data:
                gt_value = gt_fields[field_name]
                
                field_comparison[field_name] = {
                    'extracted': None,
                    'ground_truth': gt_value,
                    'correct': False
                }
                
                total_fields += 1
        
        # Calculate score
        score = (correct_fields / total_fields * 100) if total_fields > 0 else 0.0
        
        return ValidationResult(
            page_number=extracted.page_number,
            document_type=extracted.document_type,
            extracted=extracted.data,
            ground_truth=gt_fields,
            field_comparison=field_comparison,
            total_fields=total_fields,
            correct_fields=correct_fields,
            score=score
        )
    
    @staticmethod
    def _compare_values(extracted: Any, ground_truth: Any) -> bool:
        """Compare two values for equality.
        
        Args:
            extracted: Extracted value
            ground_truth: Ground truth value
        
        Returns:
            True if values match, False otherwise
        """
        # Handle None/null values
        if extracted is None and ground_truth is None:
            return True
        if extracted is None or ground_truth is None:
            return False
        
        # Handle numeric comparisons (allow for float precision)
        if isinstance(extracted, (int, float)) and isinstance(ground_truth, (int, float)):
            return abs(float(extracted) - float(ground_truth)) < 0.01
        
        # Handle string comparisons (case-insensitive for some fields)
        if isinstance(extracted, str) and isinstance(ground_truth, str):
            return extracted.strip() == ground_truth.strip()
        
        # Default: exact match
        return extracted == ground_truth
