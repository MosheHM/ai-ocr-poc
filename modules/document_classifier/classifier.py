"""Document classifier module for identifying document types."""
import json
from typing import List
from modules.types import DocumentType, PageClassification
from modules.llm.client import GeminiLLMClient
from modules.utils.pdf_utils import split_pdf_to_pages


CLASSIFICATION_PROMPT = """You are a specialized AI assistant for classifying shipping and logistics documents.

Your task is to identify the type of document shown in the image.

DOCUMENT TYPES:
1. Invoice - Commercial invoice for payment
2. OBL - Ocean Bill of Lading (sea freight)
3. HAWB - House Air Waybill (air freight)
4. Packing List - Detailed list of package contents

Analyze the document carefully and identify its type based on:
- Document title and headers
- Layout and structure
- Key fields and terminology used
- Standard formats for each document type

Return ONLY a JSON object with this exact format:
{
    "document_type": "Invoice" | "OBL" | "HAWB" | "Packing List",
    "confidence": 0.95
}

IMPORTANT:
- document_type must be exactly one of: "Invoice", "OBL", "HAWB", "Packing List"
- confidence should be a number between 0 and 1
- Return ONLY valid JSON, no additional text
"""


class PDFDocumentClassifier:
    """Classifier for identifying document types in PDFs."""
    
    def __init__(self, llm_client: GeminiLLMClient):
        """Initialize the classifier.
        
        Args:
            llm_client: LLM client for making API calls
        """
        self.llm_client = llm_client
    
    def classify_page(self, page_image: bytes, page_number: int = 1) -> PageClassification:
        """Classify a single page.
        
        Args:
            page_image: Image data of the page (PDF or image bytes)
            page_number: Page number in the document
        
        Returns:
            PageClassification result
        """
        try:
            # Call LLM to classify the page
            response = self.llm_client.generate_json_content(
                prompt=CLASSIFICATION_PROMPT,
                image_data=page_image,
                mime_type="application/pdf"
            )
            
            # Parse response
            doc_type_str = response.get("document_type", "Unknown")
            confidence = response.get("confidence", 0.0)
            
            # Map string to DocumentType enum
            try:
                doc_type = DocumentType(doc_type_str)
            except ValueError:
                doc_type = DocumentType.UNKNOWN
            
            return PageClassification(
                page_number=page_number,
                document_type=doc_type,
                confidence=confidence
            )
            
        except Exception as e:
            # If classification fails, mark as unknown
            return PageClassification(
                page_number=page_number,
                document_type=DocumentType.UNKNOWN,
                confidence=0.0
            )
    
    def classify_document(self, pdf_path: str) -> List[PageClassification]:
        """Classify all pages in a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            List of PageClassification results for each page
        """
        # Split PDF into individual pages
        pages = split_pdf_to_pages(pdf_path)
        
        classifications = []
        for page_num, page_data in enumerate(pages, start=1):
            classification = self.classify_page(page_data, page_num)
            classifications.append(classification)
        
        return classifications
