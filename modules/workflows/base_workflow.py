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
    ProcessingResult,
    DocumentInstance
)
from modules.llm.client import GeminiLLMClient
from modules.document_classifier import PDFDocumentClassifier
from modules.extractors import ExtractorFactory
from modules.utils import split_pdf_to_pages, get_pdf_page_count, combine_pdf_pages, group_pages_into_documents


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
        
        Note: Each page is classified independently to identify its document type.
        Consecutive pages of the same type are later grouped into document instances.
        
        For example, a 5-page PDF where pages 1-2 are invoices and pages 3-5 are 
        packing lists will be classified as:
        - Page 1: Invoice
        - Page 2: Invoice  
        - Page 3: Packing List
        - Page 4: Packing List
        - Page 5: Packing List
        
        These will then be grouped into 2 document instances:
        - Document 1: Invoice (pages 1-2)
        - Document 2: Packing List (pages 3-5)
        
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
    
    def _extract_document_instances(
        self,
        pdf_path: str,
        classifications: List[PageClassification]
    ) -> List[ExtractionResult]:
        """Extract data from document instances (multi-page documents).
        
        This method groups consecutive pages of the same type into document instances
        and extracts data from each instance as a whole, rather than treating each
        page independently.
        
        For example, if pages 1-2 are classified as Invoice and pages 3-5 as Packing List:
        - Creates combined PDF for pages 1-2 and extracts as one Invoice
        - Creates combined PDF for pages 3-5 and extracts as one Packing List
        - Returns 2 extraction results instead of 5
        
        Args:
            pdf_path: Path to the PDF file
            classifications: Page classifications
        
        Returns:
            List of extraction results (one per document instance)
        """
        extractions = []
        
        # Group consecutive pages of the same type
        document_instances = group_pages_into_documents(classifications)
        
        logger.info(f"Grouped {len(classifications)} pages into {len(document_instances)} document instances")
        
        for doc_instance in document_instances:
            try:
                # Log the document instance
                logger.info(
                    f"Processing document instance: {doc_instance.document_type.value} "
                    f"(pages {doc_instance.page_range})"
                )
                
                # Skip unknown document types
                if doc_instance.document_type == DocumentType.UNKNOWN:
                    logger.warning(
                        f"Document instance (pages {doc_instance.page_range}): "
                        f"Skipping extraction for unknown type"
                    )
                    extractions.append(ExtractionResult(
                        page_number=doc_instance.start_page,
                        document_type=doc_instance.document_type,
                        data={},
                        success=False,
                        error_message="Unknown document type",
                        page_count=len(doc_instance.page_numbers),
                        page_range=doc_instance.page_range
                    ))
                    continue
                
                # Combine pages into single PDF for extraction
                combined_pdf = combine_pdf_pages(pdf_path, doc_instance.page_numbers)
                
                # Create appropriate extractor
                extractor = ExtractorFactory.create_extractor(
                    doc_instance.document_type,
                    self.llm_client
                )
                
                # Extract data from the combined document
                extraction = extractor.extract(combined_pdf, doc_instance.start_page)
                
                # Update extraction result with multi-page info
                extraction.page_count = len(doc_instance.page_numbers)
                extraction.page_range = doc_instance.page_range
                
                extractions.append(extraction)
                
                if extraction.success:
                    logger.info(
                        f"Document instance (pages {doc_instance.page_range}): "
                        f"Extracted {len(extraction.data)} fields"
                    )
                else:
                    logger.warning(
                        f"Document instance (pages {doc_instance.page_range}): "
                        f"Extraction failed - {extraction.error_message}"
                    )
            
            except Exception as e:
                logger.error(
                    f"Error extracting document instance (pages {doc_instance.page_range}): {e}"
                )
                extractions.append(ExtractionResult(
                    page_number=doc_instance.start_page,
                    document_type=doc_instance.document_type,
                    data={},
                    success=False,
                    error_message=str(e),
                    page_count=len(doc_instance.page_numbers),
                    page_range=doc_instance.page_range
                ))
        
        return extractions
