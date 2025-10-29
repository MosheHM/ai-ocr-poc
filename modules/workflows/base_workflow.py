"""Base workflow class for document processing."""
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
from modules.types import (
    DocumentType,
    PageClassification,
    ExtractionResult,
    ValidationResult,
    ProcessingResult
)
from modules.llm.client import GeminiLLMClient
from modules.document_classifier import PDFDocumentClassifier
from modules.extractors import ExtractorFactory
from modules.utils import split_pdf_to_pages, get_pdf_page_count


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BaseWorkflow(ABC):
    """Base class for document processing workflows."""
    
    def __init__(self, api_key: str):
        """Initialize the workflow.
        
        Args:
            api_key: Google Gemini API key
        """
        self.llm_client = GeminiLLMClient(api_key)
        self.classifier = PDFDocumentClassifier(self.llm_client)
    
    @abstractmethod
    def process_document(self, pdf_path: str, **kwargs) -> ProcessingResult:
        """Process a document. Must be implemented by subclasses.
        
        Args:
            pdf_path: Path to the PDF file
            **kwargs: Additional keyword arguments
        
        Returns:
            ProcessingResult
        """
        pass
    
    def _classify_pages(self, pdf_path: str) -> List[PageClassification]:
        """Classify all pages in a document.
        
        Note: Each page is classified independently. A PDF with 5 pages where
        pages 1-2 are invoices and pages 3-5 are packing lists will result in
        5 separate classifications (2 Invoice + 3 Packing List).
        
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
