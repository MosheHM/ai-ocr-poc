"""Extraction workflow for daily use (no validation)."""
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from modules.types import ProcessingResult
from modules.utils import get_pdf_page_count
from .base_workflow import BaseWorkflow, logger


class ExtractionWorkflow(BaseWorkflow):
    """Workflow for extracting data without validation.
    
    This workflow is optimized for production/daily use where you just
    need to extract data from documents without comparing against ground truth.
    """
    
    def process_document(
        self,
        pdf_path: str,
        **kwargs
    ) -> ProcessingResult:
        """Process a document and extract data (no validation).
        
        Pipeline steps:
        1. Classify each page to identify document type
        2. Extract data from each page using type-specific extractors
        
        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional options (unused in this workflow)
        
        Returns:
            ProcessingResult with classifications and extractions
        """
        logger.info(f"Starting extraction workflow for: {pdf_path}")
        
        result = ProcessingResult(
            pdf_path=pdf_path,
            total_pages=get_pdf_page_count(pdf_path),
            classifications=[],
            extractions=[],
            validations=[],  # Always empty for this workflow
            success=True,
            errors=[]
        )
        
        try:
            # Step 1: Classify all pages
            logger.info("Step 1: Classifying pages...")
            result.classifications = self._classify_pages(pdf_path)
            
            # Step 2: Extract data from each page
            logger.info("Step 2: Extracting data from pages...")
            result.extractions = self._extract_pages(pdf_path, result.classifications)
            
            logger.info(f"Extraction complete. Success: {result.success}")
            
        except Exception as e:
            logger.error(f"Error in extraction workflow: {e}", exc_info=True)
            result.success = False
            result.errors.append(f"Extraction error: {str(e)}")
        
        return result
    
    def generate_report(self, result: ProcessingResult) -> str:
        """Generate a human-readable extraction report.
        
        Args:
            result: Processing result
        
        Returns:
            Report string
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"Extraction Report: {Path(result.pdf_path).name}")
        lines.append("=" * 80)
        lines.append(f"Total Pages: {result.total_pages}")
        lines.append(f"Success: {result.success}")
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
        lines.append("Extracted Data:")
        lines.append("-" * 80)
        for ext in result.extractions:
            status = "✓ Success" if ext.success else "✗ Failed"
            lines.append(f"  Page {ext.page_number} ({ext.document_type.value}): {status}")
            if ext.success:
                lines.append(f"    Fields extracted: {len(ext.data)}")
                for key, value in ext.data.items():
                    lines.append(f"      - {key}: {value}")
            else:
                lines.append(f"    Error: {ext.error_message}")
        lines.append("")
        
        # Errors
        if result.errors:
            lines.append("Errors:")
            lines.append("-" * 80)
            for error in result.errors:
                lines.append(f"  - {error}")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
