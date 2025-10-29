"""Base extractor class and type-specific extractors."""
from abc import ABC, abstractmethod
from modules.types import DocumentType, ExtractionResult
from modules.llm.client import GeminiLLMClient


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
        return """You are an AI assistant specialized in extracting structured data from invoices.

Extract the following fields from the invoice and return them as a JSON object:

REQUIRED RETURN FIELDS AND FORMATS (THE FORMAT IS JUST FOR RETURN VALIDATION, NOT FOR EXTRACTION):
- INVOICE_NO: Extract as-is, preserving all characters including slashes (e.g., "0004833/E", "INV-25-0026439")
- INVOICE_DATE: Format as YYYYMMDDHHMMSSSS (16 digits)
  * Convert any date format to: YYYYMMDD00000000
  * Example: "30.07.2025" becomes "2025073000000000"
  * Example: "30/07/2025" becomes "2025073000000000"
  * Example: "July 30, 2025" becomes "2025073000000000"
  * Always pad with 00000000 at the end for time portion
- CURRENCY_ID: 3-letter currency code in uppercase (e.g., "EUR", "USD", "GBP")
- INCOTERMS: INCOTERMS code in uppercase (e.g., "FCA", "FOB", "CIF", "EXW")
  * Do NOT include location details or additional text
  * Just the code: "FCA" not "FCA Duisburg, stock Buhlmann"
- INVOICE_AMOUNT: number (integer or float) without currency symbols
  * Example: 7632.00 or 7632
- CUSTOMER_ID: Extract as-is (e.g., "D004345")

CRITICAL FORMAT RULES:
1. INVOICE_DATE must be exactly 16 digits: YYYYMMDD00000000
2. INCOTERMS must be ONLY the code (3 letters usually), no location or extra text
3. INVOICE_AMOUNT must be a number type, not a string
4. Preserve exact formatting for INVOICE_NO (keep slashes, dashes, etc.)
5. Return ONLY valid JSON with these exact field names
6. If a field is not found, omit it from the response

Example output format:
{
    "INVOICE_NO": "0004833/E",
    "INVOICE_DATE": "2025073000000000",
    "CURRENCY_ID": "EUR",
    "INCOTERMS": "FCA",
    "INVOICE_AMOUNT": 7632.00,
    "CUSTOMER_ID": "D004345"
}
"""


class OBLExtractor(BaseExtractor):
    """Extractor for OBL (Ocean Bill of Lading) documents."""
    
    def get_document_type(self) -> DocumentType:
        return DocumentType.OBL
    
    def get_system_prompt(self) -> str:
        return """You are an AI assistant specialized in extracting structured data from Ocean Bill of Lading (OBL) documents.

Extract the following fields from the OBL and return them as a JSON object:

REQUIRED FIELDS:
- CUSTOMER_NAME: Name of the customer/shipper (string or null if not found)
- WEIGHT: Total weight of the shipment (number or null if not found)
- VOLUME: Total volume of the shipment (number or null if not found)
- INCOTERMS: INCOTERMS code in uppercase (string or null if not found)
  * Example: "FOB", "CIF", "CFR"
  * Extract ONLY the code, not location details

CRITICAL FORMAT RULES:
1. Return ONLY valid JSON with these exact field names
2. Use null for fields that are not found
3. WEIGHT and VOLUME should be numbers when found
4. INCOTERMS should be uppercase code only

Example output format:
{
    "CUSTOMER_NAME": "ABC Corporation",
    "WEIGHT": 1500.5,
    "VOLUME": 45.2,
    "INCOTERMS": "FOB"
}

Or if fields are missing:
{
    "CUSTOMER_NAME": "ABC Corporation",
    "WEIGHT": null,
    "VOLUME": null,
    "INCOTERMS": "CIF"
}
"""


class HAWBExtractor(BaseExtractor):
    """Extractor for HAWB (House Air Waybill) documents."""
    
    def get_document_type(self) -> DocumentType:
        return DocumentType.HAWB
    
    def get_system_prompt(self) -> str:
        return """You are an AI assistant specialized in extracting structured data from House Air Waybill (HAWB) documents.

Extract the following fields from the HAWB and return them as a JSON object:

REQUIRED FIELDS:
- CUSTOMER_NAME: Name of the customer/shipper (string or null if not found)
- CURRENCY: 3-letter currency code (string or null if not found)
- CARRIER: Name of the air carrier (string or null if not found)
- HAWB_NUMBER: House Air Waybill number (string or null if not found)
- PIECES: Number of pieces/packages (number or null if not found)
- WEIGHT: Total weight (number or null if not found)

CRITICAL FORMAT RULES:
1. Return ONLY valid JSON with these exact field names
2. Use null for fields that are not found
3. PIECES and WEIGHT should be numbers when found
4. CURRENCY should be 3-letter uppercase code when found

Example output format:
{
    "CUSTOMER_NAME": "XYZ Logistics",
    "CURRENCY": "USD",
    "CARRIER": "Air Freight Co",
    "HAWB_NUMBER": "HAWB-2025-001234",
    "PIECES": 25,
    "WEIGHT": 450.5
}
"""


class PackingListExtractor(BaseExtractor):
    """Extractor for Packing List documents."""
    
    def get_document_type(self) -> DocumentType:
        return DocumentType.PACKING_LIST
    
    def get_system_prompt(self) -> str:
        return """You are an AI assistant specialized in extracting structured data from Packing List documents.

Extract the following fields from the packing list and return them as a JSON object:

REQUIRED FIELDS:
- CUSTOMER_NAME: Name of the customer/recipient (string or null if not found)
- PIECES: Total number of pieces/packages (number or null if not found)
- WEIGHT: Total weight of all packages (number or null if not found)

CRITICAL FORMAT RULES:
1. Return ONLY valid JSON with these exact field names
2. Use null for fields that are not found
3. PIECES and WEIGHT should be numbers when found

Example output format:
{
    "CUSTOMER_NAME": "DEF Manufacturing",
    "PIECES": 100,
    "WEIGHT": 2500.0
}
"""


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
