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

        expected_fields = list(DOCUMENT_SCHEMAS[extracted.document_type].keys()) if extracted.document_type in DOCUMENT_SCHEMAS else []

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
        
        # Validate calculated fields (e.g., XML calculations for amounts)
        calculation_result = self._validate_calculations(extracted.data, gt_fields, extracted.document_type)
        if calculation_result:
            # Add calculation validation to field comparison
            for calc_field, calc_info in calculation_result.items():
                if calc_field not in field_comparison:
                    field_comparison[calc_field] = calc_info
                    total_fields += 1
                    if calc_info['correct']:
                        correct_fields += 1
        
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
    
    def _validate_calculations(
        self,
        extracted: Dict[str, Any],
        ground_truth: Dict[str, Any],
        document_type: DocumentType
    ) -> Optional[Dict[str, Dict[str, Any]]]:
        """Validate calculated fields in XML/document data.
        
        For invoices and similar documents, validates that calculated amounts
        match the ground truth. If incorrect, adds to mismatch tracking.
        
        Args:
            extracted: Extracted data
            ground_truth: Ground truth data
            document_type: Type of document
        
        Returns:
            Dictionary of calculation validation results, or None if no calculations to validate
        """
        calculation_results = {}
        
        # Define calculation fields by document type
        calculation_fields = {
            DocumentType.INVOICE: ['INVOICE_AMOUNT'],
            DocumentType.OBL: ['WEIGHT', 'VOLUME'],
            DocumentType.HAWB: ['WEIGHT', 'PIECES'],
            DocumentType.PACKING_LIST: ['WEIGHT', 'PIECES']
        }
        
        if document_type not in calculation_fields:
            return None
        
        fields_to_validate = calculation_fields[document_type]
        
        for field_name in fields_to_validate:
            # Only validate if field exists in ground truth and was extracted
            if field_name in ground_truth and field_name in extracted:
                extracted_value = extracted[field_name]
                gt_value = ground_truth[field_name]
                
                # Validate the calculation
                is_correct = self._compare_values(extracted_value, gt_value)
                
                calculation_results[field_name] = {
                    'extracted': extracted_value,
                    'ground_truth': gt_value,
                    'correct': is_correct,
                    'is_calculation': True
                }
        
        return calculation_results if calculation_results else None
    
    @staticmethod
    def _compare_values(extracted: Any, ground_truth: Any) -> bool:
        """Compare two values for equality.
        
        Args:
            extracted: Extracted value
            ground_truth: Ground truth value
        
        Returns:
            True if values match, False otherwise
        """
        if extracted is None and ground_truth is None:
            return True
        if extracted is None or ground_truth is None:
            return False
        
        if isinstance(extracted, (int, float)) and isinstance(ground_truth, (int, float)):
            return abs(float(extracted) - float(ground_truth)) < 0.01
        
        if isinstance(extracted, str) and isinstance(ground_truth, str):
            return extracted.strip() == ground_truth.strip()
        
        return extracted == ground_truth
