"""Type definitions and protocols for the AI OCR system."""
from typing import Protocol, Dict, Any, List, Optional, Literal
from dataclasses import dataclass
from enum import Enum


class GeminiModel(str, Enum):
    """Supported Gemini models."""
    GEMINI_2_0_FLASH_EXP = "gemini-2.0-flash-exp"
    GEMINI_1_5_FLASH = "gemini-1.5-flash"
    GEMINI_1_5_FLASH_8B = "gemini-1.5-flash-8b"
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"


class DocumentType(str, Enum):
    """Supported document types."""
    INVOICE = "Invoice"
    OBL = "OBL"
    HAWB = "HAWB"
    PACKING_LIST = "Packing List"
    UNKNOWN = "Unknown"


@dataclass
class PageClassification:
    """Classification result for a single page."""
    page_number: int
    document_type: DocumentType
    confidence: Optional[float] = None


@dataclass
class DocumentInstance:
    """Represents a single document that may span multiple pages."""
    document_type: DocumentType
    start_page: int
    end_page: int
    page_numbers: List[int]
    
    @property
    def page_range(self) -> str:
        """Get a human-readable page range."""
        if self.start_page == self.end_page:
            return str(self.start_page)
        return f"{self.start_page}-{self.end_page}"


@dataclass
class ExtractionResult:
    """Result of data extraction from a page or document instance."""
    page_number: int  # For single page, or start page for multi-page
    document_type: DocumentType
    data: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
    page_count: int = 1  # Number of pages in this document
    page_range: Optional[str] = None  # Human-readable page range (e.g., "1-2")


@dataclass
class ValidationResult:
    """Result of validating extracted data against ground truth."""
    page_number: int
    document_type: DocumentType
    extracted: Dict[str, Any]
    ground_truth: Optional[Dict[str, Any]]
    field_comparison: Dict[str, Dict[str, Any]]
    total_fields: int
    correct_fields: int
    score: float
    

@dataclass
class ProcessingResult:
    """Overall processing result for a document."""
    pdf_path: str
    total_pages: int
    classifications: List[PageClassification]
    extractions: List[ExtractionResult]
    validations: List[ValidationResult]
    overall_score: Optional[float] = None
    success: bool = True
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class LLMProvider(Protocol):
    """Protocol for LLM providers."""
    
    def generate_content(
        self,
        prompt: str,
        image_data: Optional[bytes] = None,
        mime_type: Optional[str] = None,
        model: str = "gemini-2.5-flash"
    ) -> str:
        """Generate content using the LLM."""
        ...


class DocumentClassifier(Protocol):
    """Protocol for document classifiers."""
    
    def classify_page(self, page_image: bytes) -> PageClassification:
        """Classify a single page."""
        ...
    
    def classify_document(self, pdf_path: str) -> List[PageClassification]:
        """Classify all pages in a document."""
        ...


class DocumentExtractor(Protocol):
    """Protocol for document extractors."""
    
    def extract(self, page_image: bytes, page_number: int) -> ExtractionResult:
        """Extract data from a page."""
        ...


class Validator(Protocol):
    """Protocol for validators."""
    
    def validate(
        self,
        extracted: ExtractionResult,
        ground_truth: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate extracted data against ground truth."""
        ...


# Schema definitions for each document type
INVOICE_SCHEMA = {
    "INVOICE_NO": "string",
    "INVOICE_DATE": "string (YYYYMMDD00000000)",
    "CURRENCY_ID": "string (3-letter code)",
    "INCOTERMS": "string (uppercase code)",
    "INVOICE_AMOUNT": "number",
    "CUSTOMER_ID": "string"
}

OBL_SCHEMA = {
    "CUSTOMER_NAME": "string or null",
    "WEIGHT": "number or null",
    "VOLUME": "number or null",
    "INCOTERMS": "string or null"
}

HAWB_SCHEMA = {
    "CUSTOMER_NAME": "string or null",
    "CURRENCY": "string or null",
    "CARRIER": "string or null",
    "HAWB_NUMBER": "string or null",
    "PIECES": "number or null",
    "WEIGHT": "number or null"
}

PACKING_LIST_SCHEMA = {
    "CUSTOMER_NAME": "string or null",
    "PIECES": "number or null",
    "WEIGHT": "number or null"
}

DOCUMENT_SCHEMAS = {
    DocumentType.INVOICE: INVOICE_SCHEMA,
    DocumentType.OBL: OBL_SCHEMA,
    DocumentType.HAWB: HAWB_SCHEMA,
    DocumentType.PACKING_LIST: PACKING_LIST_SCHEMA
}
