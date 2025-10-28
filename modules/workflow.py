"""Workflow orchestrator for document processing pipeline."""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..types import (
    DocumentType,
    PageClassification,
    ExtractionResult,
    ValidationResult,
    ProcessingResult
)
from ..llm.client import GeminiLLMClient
from ..document_classifier import PDFDocumentClassifier
from ..extractors import ExtractorFactory
from ..validators import PerformanceValidator
from ..utils import split_pdf_to_pages, get_pdf_page_count


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Orchestrator for the complete document processing pipeline."""
    
    def __init__(self, api_key: str):
        """Initialize the document processor.
        
        Args:
            api_key: Google Gemini API key
        """
        self.llm_client = GeminiLLMClient(api_key)
        self.classifier = PDFDocumentClassifier(self.llm_client)
        self.validator = PerformanceValidator()
    
    def process_document(
        self,
        pdf_path: str,
        ground_truth: Optional[Dict[str, Any]] = None
    ) -> ProcessingResult:
        """Process a complete document through the pipeline.
        
        Pipeline steps:
        1. Classify each page to identify document type
        2. Extract data from each page using type-specific extractors
        3. Validate extracted data against ground truth (if provided)
        
        Args:
            pdf_path: Path to the PDF file
            ground_truth: Optional ground truth data for validation
        
        Returns:
            ProcessingResult containing all results
        """
        logger.info(f"Processing document: {pdf_path}")
        
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
            # Step 1: Classify all pages
            logger.info("Step 1: Classifying pages...")
            result.classifications = self._classify_pages(pdf_path)
            
            # Step 2: Extract data from each page
            logger.info("Step 2: Extracting data from pages...")
            result.extractions = self._extract_pages(pdf_path, result.classifications)
            
            # Step 3: Validate extractions if ground truth is provided
            if ground_truth:
                logger.info("Step 3: Validating extractions...")
                result.validations = self._validate_extractions(
                    result.extractions,
                    ground_truth
                )
                
                # Calculate overall score
                if result.validations:
                    total_score = sum(v.score for v in result.validations)
                    result.overall_score = total_score / len(result.validations)
            
            logger.info(f"Processing complete. Success: {result.success}")
            
        except Exception as e:
            logger.error(f"Error processing document: {e}", exc_info=True)
            result.success = False
            result.errors.append(f"Processing error: {str(e)}")
        
        return result
    
    def _classify_pages(self, pdf_path: str) -> List[PageClassification]:
        """Classify all pages in a document.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            List of page classifications
        """
        classifications = []
        
        try:
            classifications = self.classifier.classify_document(pdf_path)
            
            # Log classifications
            for cls in classifications:
                logger.info(
                    f"Page {cls.page_number}: {cls.document_type.value} "
                    f"(confidence: {cls.confidence:.2f})"
                )
        
        except Exception as e:
            logger.error(f"Error classifying pages: {e}")
            # Return unknown classification for single page
            classifications = [PageClassification(
                page_number=1,
                document_type=DocumentType.UNKNOWN,
                confidence=0.0
            )]
        
        return classifications
    
    def _extract_pages(
        self,
        pdf_path: str,
        classifications: List[PageClassification]
    ) -> List[ExtractionResult]:
        """Extract data from all pages.
        
        Args:
            pdf_path: Path to the PDF file
            classifications: Page classifications
        
        Returns:
            List of extraction results
        """
        extractions = []
        pages = split_pdf_to_pages(pdf_path)
        
        for cls, page_data in zip(classifications, pages):
            try:
                # Skip unknown document types
                if cls.document_type == DocumentType.UNKNOWN:
                    logger.warning(
                        f"Page {cls.page_number}: Skipping extraction for unknown type"
                    )
                    extractions.append(ExtractionResult(
                        page_number=cls.page_number,
                        document_type=cls.document_type,
                        data={},
                        success=False,
                        error_message="Unknown document type"
                    ))
                    continue
                
                # Create appropriate extractor
                extractor = ExtractorFactory.create_extractor(
                    cls.document_type,
                    self.llm_client
                )
                
                # Extract data
                extraction = extractor.extract(page_data, cls.page_number)
                extractions.append(extraction)
                
                if extraction.success:
                    logger.info(
                        f"Page {cls.page_number}: Extracted {len(extraction.data)} fields"
                    )
                else:
                    logger.warning(
                        f"Page {cls.page_number}: Extraction failed - {extraction.error_message}"
                    )
            
            except Exception as e:
                logger.error(f"Error extracting page {cls.page_number}: {e}")
                extractions.append(ExtractionResult(
                    page_number=cls.page_number,
                    document_type=cls.document_type,
                    data={},
                    success=False,
                    error_message=str(e)
                ))
        
        return extractions
    
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
        """Generate a human-readable report of the processing results.
        
        Args:
            result: Processing result
        
        Returns:
            Report string
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"Document Processing Report: {Path(result.pdf_path).name}")
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
        lines.append("Data Extractions:")
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
                    for field, comparison in val.field_comparison.items():
                        status = "✓" if comparison['correct'] else "✗"
                        lines.append(
                            f"    {status} {field}: {comparison['extracted']} "
                            f"(expected: {comparison['ground_truth']})"
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
