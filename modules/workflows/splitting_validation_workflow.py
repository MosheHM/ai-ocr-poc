"""Workflow for validating PDF splitting against XML ground truth."""
import os
import json
from pathlib import Path
from typing import Optional
from modules.workflows.base_workflow import BaseWorkflow
from modules.validators import (
    parse_splitted_result_xml,
    SplittingValidator,
)


class SplittingValidationWorkflow(BaseWorkflow):
    """Workflow that validates PDF splitting against XML ground truth."""
    
    def __init__(self, api_key: str):
        """Initialize the workflow with API key."""
        super().__init__(api_key)
        self.splitting_validator = SplittingValidator()
    
    def process_document_with_xml_ground_truth(
        self,
        pdf_path: str,
        xml_ground_truth_path: str
    ):
        """
        Process a PDF and validate splitting against XML ground truth.
        
        Args:
            pdf_path: Path to PDF file
            xml_ground_truth_path: Path to XML ground truth file
            
        Returns:
            Dictionary with processing result and splitting validation result
        """
        # First, process the PDF normally (classification and extraction)
        processing_result = self.process_document(pdf_path)
        
        # Parse XML ground truth
        try:
            ground_truth = parse_splitted_result_xml(xml_ground_truth_path)
        except Exception as e:
            processing_result.errors.append(f"Failed to parse XML ground truth: {e}")
            return {
                'processing_result': processing_result,
                'splitting_validation': None,
                'error': str(e)
            }
        
        # Validate splitting
        try:
            splitting_validation = self.splitting_validator.validate(
                processing_result,
                ground_truth
            )
        except Exception as e:
            processing_result.errors.append(f"Failed to validate splitting: {e}")
            return {
                'processing_result': processing_result,
                'splitting_validation': None,
                'error': str(e)
            }
        
        return {
            'processing_result': processing_result,
            'splitting_validation': splitting_validation,
            'ground_truth': ground_truth,
        }
    
    def generate_combined_report(
        self,
        processing_result,
        splitting_validation,
        ground_truth
    ) -> str:
        """Generate a combined report with both processing and validation results."""
        lines = []
        
        # Add standard processing report
        lines.append(self.generate_report(processing_result))
        lines.append("\n")
        lines.append("=" * 80)
        lines.append("\n")
        
        # Add splitting validation report
        if splitting_validation:
            lines.append(self.splitting_validator.generate_report(splitting_validation))
        
        return "\n".join(lines)
