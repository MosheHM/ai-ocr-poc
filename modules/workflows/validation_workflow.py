"""Validation workflow for testing and quality assurance."""
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from modules.types import ProcessingResult, ExtractionResult, ValidationResult
from modules.utils import get_pdf_page_count, find_ground_truth_txt, load_ground_truth_from_txt
from modules.validators import PerformanceValidator
from .base_workflow import BaseWorkflow, logger


class ValidationWorkflow(BaseWorkflow):
    """Workflow for extracting data with validation against ground truth.
    
    This workflow is designed for testing, quality assurance, and model
    performance evaluation. It requires ground truth data for comparison.
    """
    
    def __init__(self, api_key: str):
        """Initialize the validation workflow.
        
        Args:
            api_key: Google Gemini API key
        """
        super().__init__(api_key)
        self.validator = PerformanceValidator()
    
    def process_document(
        self,
        pdf_path: str,
        ground_truth: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ProcessingResult:
        """Process a document with validation.
        
        This method now checks for the existence of a .txt ground truth file.
        If no .txt file exists, the extraction is skipped to avoid unnecessary 
        Gemini API calls.
        
        Pipeline steps:
        1. Check for .txt ground truth file
        2. If .txt exists:
           a. Load ground truth from .txt file
           b. Classify each page to identify document type
           c. Group consecutive pages of same type into document instances
           d. Extract data from each document instance (multi-page extraction)
           e. Validate extracted data against ground truth
        3. If .txt doesn't exist:
           a. Skip extraction and report as skipped
        
        Args:
            pdf_path: Path to the PDF file
            ground_truth: Ground truth data for validation (optional, will be loaded from .txt if not provided)
            **kwargs: Additional options
        
        Returns:
            ProcessingResult with classifications, extractions, and validations
        """
        logger.info(f"Starting validation workflow for: {pdf_path}")
        
        result = ProcessingResult(
            pdf_path=pdf_path,
            total_pages=get_pdf_page_count(pdf_path),
            classifications=[],
            extractions=[],
            validations=[],
            success=True,
            errors=[]
        )
        
        try:
            # Check for .txt ground truth file
            txt_path = find_ground_truth_txt(pdf_path)
            
            if txt_path is None:
                # No .txt file found - skip extraction
                logger.info(f"No .txt ground truth file found for {pdf_path}. Skipping extraction.")
                result.errors.append(f"No .txt ground truth file found. Extraction skipped to avoid unnecessary API calls.")
                result.success = True  # This is not an error, just skipped
                return result
            
            logger.info(f"Found .txt ground truth file: {txt_path}")
            
            # Load ground truth from .txt file if not provided
            if ground_truth is None:
                ground_truth = load_ground_truth_from_txt(txt_path)
                if ground_truth is None:
                    logger.error(f"Failed to load ground truth from {txt_path}")
                    result.errors.append(f"Failed to load ground truth from {txt_path}")
                    result.success = False
                    return result
                logger.info("Ground truth loaded from .txt file")
            
            # Step 1: Classify all pages
            logger.info("Step 1: Classifying pages...")
            result.classifications = self._classify_pages(pdf_path)
            
            # Step 2: Extract data from document instances (multi-page aware)
            logger.info("Step 2: Grouping pages and extracting data from document instances...")
            result.extractions, result.document_instances = self._extract_document_instances(
                pdf_path, result.classifications
            )
            
            # Step 3: Validate extractions
            logger.info("Step 3: Validating extractions...")
            result.validations = self._validate_extractions(
                result.extractions,
                ground_truth
            )
            
            # Calculate overall score
            if result.validations:
                total_score = sum(v.score for v in result.validations)
                result.overall_score = total_score / len(result.validations)
            
            logger.info(f"Validation workflow complete. Success: {result.success}")
            
        except Exception as e:
            logger.error(f"Error in validation workflow: {e}", exc_info=True)
            result.success = False
            result.errors.append(f"Validation workflow error: {str(e)}")
        
        return result
    
    def _validate_extractions(
        self,
        extractions: List[ExtractionResult],
        ground_truth: Dict[str, Any]
    ) -> List[ValidationResult]:
        """Validate all extractions against ground truth.
        
        Args:
            extractions: List of extraction results
            ground_truth: Ground truth data
        
        Returns:
            List of validation results
        """
        validations = []
        
        for extraction in extractions:
            try:
                validation = self.validator.validate(extraction, ground_truth)
                validations.append(validation)
                
                if validation.total_fields > 0:
                    logger.info(
                        f"Page {extraction.page_number}: Score {validation.score:.2f}% "
                        f"({validation.correct_fields}/{validation.total_fields} correct)"
                    )
            
            except Exception as e:
                logger.error(f"Error validating page {extraction.page_number}: {e}")
        
        return validations
    
    def generate_report(self, result: ProcessingResult) -> str:
        """Generate a comprehensive validation report.
        
        Args:
            result: Processing result
        
        Returns:
            Report string
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"Validation Report: {Path(result.pdf_path).name}")
        lines.append("=" * 80)
        lines.append(f"Total Pages: {result.total_pages}")
        lines.append(f"Success: {result.success}")
        lines.append("")
        
        # Document Summary - NEW SECTION
        lines.append("Document Summary:")
        lines.append("-" * 80)
        
        # Count documents by type
        from collections import Counter
        doc_type_counts = Counter(doc.document_type for doc in result.document_instances)
        
        # Display summary with counts
        for doc_type, count in doc_type_counts.items():
            lines.append(f"  {doc_type.value}: {count} document(s)")
        
        lines.append("")
        lines.append("Document Instances:")
        
        # Number each document instance
        for i, doc_instance in enumerate(result.document_instances, 1):
            page_info = f"page {doc_instance.page_range}" if doc_instance.start_page == doc_instance.end_page else f"pages {doc_instance.page_range}"
            lines.append(f"  {i}. {doc_instance.document_type.value} - {page_info}")
        
        lines.append("")
        
        # Classifications
        lines.append("Page Classifications:")
        lines.append("-" * 80)
        for cls in result.classifications:
            lines.append(
                f"  Page {cls.page_number}: {cls.document_type.value} "
                f"(confidence: {cls.confidence:.2f if cls.confidence else 0.0:.2f})"
            )
        lines.append("")
        
        # Extractions
        lines.append("Extracted Documents:")
        lines.append("-" * 80)
        for ext in result.extractions:
            status = "✓ Success" if ext.success else "✗ Failed"
            page_info = f"Pages {ext.page_range}" if ext.page_range else f"Page {ext.page_number}"
            lines.append(f"  {page_info} ({ext.document_type.value}): {status}")
            if ext.success:
                lines.append(f"    Fields extracted: {len(ext.data)}")
                for key, value in ext.data.items():
                    lines.append(f"      - {key}: {value}")
            else:
                lines.append(f"    Error: {ext.error_message}")
        lines.append("")
        
        # Validations
        if result.validations:
            lines.append("Validation Results:")
            lines.append("-" * 80)
            for val in result.validations:
                lines.append(
                    f"  Page {val.page_number}: Score {val.score:.2f}% "
                    f"({val.correct_fields}/{val.total_fields} correct)"
                )
                if val.field_comparison:
                    # Separate calculation fields from regular fields
                    calc_fields = {k: v for k, v in val.field_comparison.items() if v.get('is_calculation', False)}
                    regular_fields = {k: v for k, v in val.field_comparison.items() if not v.get('is_calculation', False)}
                    
                    # Display regular fields first
                    for field, comparison in regular_fields.items():
                        status = "✓" if comparison['correct'] else "✗"
                        extracted = comparison['extracted']
                        expected = comparison['ground_truth']
                        
                        if extracted is None:
                            lines.append(f"    {status} {field}: NOT EXTRACTED (expected: {expected})")
                        elif comparison['correct']:
                            lines.append(f"    {status} {field}: {extracted}")
                        else:
                            lines.append(
                                f"    {status} {field}: {extracted} (expected: {expected}) [MISMATCH]"
                            )
                    
                    # Display calculation fields separately with special marking
                    if calc_fields:
                        lines.append("")
                        lines.append("    Calculation Validations:")
                        for field, comparison in calc_fields.items():
                            status = "✓" if comparison['correct'] else "✗"
                            extracted = comparison['extracted']
                            expected = comparison['ground_truth']
                            
                            if comparison['correct']:
                                lines.append(f"    {status} {field} (calc): {extracted} [CORRECT]")
                            else:
                                lines.append(
                                    f"    {status} {field} (calc): {extracted} (expected: {expected}) [MISMATCH]"
                                )
            
            if result.overall_score is not None:
                lines.append("")
                lines.append(f"Overall Score: {result.overall_score:.2f}%")
        
        # Errors
        if result.errors:
            lines.append("")
            lines.append("Errors:")
            lines.append("-" * 80)
            for error in result.errors:
                lines.append(f"  - {error}")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
