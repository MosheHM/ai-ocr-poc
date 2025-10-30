"""Base extractor class and type-specific extractors."""
from abc import ABC, abstractmethod
from modules.types import DocumentType, ExtractionResult
from modules.llm.client import GeminiLLMClient
from modules.prompts import (
    get_invoice_extraction_prompt,
    get_obl_extraction_prompt,
    get_hawb_extraction_prompt,
    get_packing_list_extraction_prompt
)


class BaseExtractor(ABC):
    """Base class for document extractors."""
    
    def __init__(self, llm_client: GeminiLLMClient):
        """Initialize the extractor.
        
        Args:
            llm_client: LLM client for making API calls
        """
        self.llm_client = llm_client
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this extractor."""
        pass
    
    @abstractmethod
    def get_document_type(self) -> DocumentType:
        """Get the document type this extractor handles."""
        pass
    
    def extract(self, page_image: bytes, page_number: int) -> ExtractionResult:
        """Extract data from a page.
        
        Args:
            page_image: Image/PDF data of the page
            page_number: Page number in the document
        
        Returns:
            ExtractionResult containing extracted data
        """
        try:
            response = self.llm_client.generate_json_content(
                prompt=self.get_system_prompt(),
                image_data=page_image,
                mime_type="application/pdf"
            )
            
            return ExtractionResult(
                page_number=page_number,
                document_type=self.get_document_type(),
                data=response,
                success=True,
                error_message=None
            )
            
        except Exception as e:
            return ExtractionResult(
                page_number=page_number,
                document_type=self.get_document_type(),
                data={},
                success=False,
                error_message=str(e)
            )


class InvoiceExtractor(BaseExtractor):
    """Extractor for Invoice documents."""
    
    def get_document_type(self) -> DocumentType:
        return DocumentType.INVOICE
    
    def get_system_prompt(self) -> str:
        return get_invoice_extraction_prompt()


class OBLExtractor(BaseExtractor):
    """Extractor for OBL (Ocean Bill of Lading) documents."""
    
    def get_document_type(self) -> DocumentType:
        return DocumentType.OBL
    
    def get_system_prompt(self) -> str:
        return get_obl_extraction_prompt()


class HAWBExtractor(BaseExtractor):
    """Extractor for HAWB (House Air Waybill) documents."""
    
    def get_document_type(self) -> DocumentType:
        return DocumentType.HAWB
    
    def get_system_prompt(self) -> str:
        return get_hawb_extraction_prompt()


class PackingListExtractor(BaseExtractor):
    """Extractor for Packing List documents."""
    
    def get_document_type(self) -> DocumentType:
        return DocumentType.PACKING_LIST
    
    def get_system_prompt(self) -> str:
        return get_packing_list_extraction_prompt()


class ExtractorFactory:
    """Factory for creating the appropriate extractor based on document type."""
    
    @staticmethod
    def create_extractor(document_type: DocumentType, llm_client: GeminiLLMClient) -> BaseExtractor:
        """Create an extractor for the given document type.
        
        Args:
            document_type: Type of document to extract
            llm_client: LLM client for making API calls
        
        Returns:
            Appropriate extractor instance
        
        Raises:
            ValueError: If document type is not supported
        """
        extractors = {
            DocumentType.INVOICE: InvoiceExtractor,
            DocumentType.OBL: OBLExtractor,
            DocumentType.HAWB: HAWBExtractor,
            DocumentType.PACKING_LIST: PackingListExtractor
        }
        
        extractor_class = extractors.get(document_type)
        if extractor_class is None:
            raise ValueError(f"No extractor available for document type: {document_type}")
        
        return extractor_class(llm_client)
