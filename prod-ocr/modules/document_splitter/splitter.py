"""Document splitter for extracting and splitting PDFs by document type."""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, TypedDict, Literal
from dataclasses import dataclass
from google import genai
from google.genai import types

from ..utils import extract_pdf_pages
from ..result_types import Result, success, failure, is_success

logger = logging.getLogger(__name__)


class PageInfo(TypedDict):
    """Type definition for page rotation information."""
    PAGE_NO: int
    ROTATION: Literal[0, 90, 180, 270]  # 0, 90, 180, or 270 degrees clockwise


class DocumentField(TypedDict):
    """Type definition for extracted document field."""
    field_id: str
    field_value: Any


class ExtractedDocument(TypedDict):
    """Type definition for a single extracted document."""
    DOC_TYPE: str
    DOC_TYPE_CONFIDENCE: float
    TOTAL_PAGES: int
    START_PAGE_NO: int
    END_PAGE_NO: int
    PAGES_INFO: List[PageInfo]
    DOC_DATA: List[DocumentField]


class ExtractionResult(TypedDict):
    """Type definition for complete extraction result."""
    source_pdf: str
    total_documents: int
    documents: List[ExtractedDocument]


DOCUMENT_EXTRACTION_PROMPT = """You are an AI assistant specialized in analyzing unclassified PDF documents. Your task is to identify distinct documents within the file, classify them, and extract structured data.

The input PDF may contain a single document or multiple documents of different types merged together. You must detect the boundaries of each document.

Supported Document Types:
1. Invoice
2. OBL (Ocean Bill of Lading)
3. HAWB (House Air Waybill)
4. Packing List

For each detected document, extract the data according to the specific schema below and return a JSON ARRAY of objects.

--- SCHEMAS & EXTRACTION RULES ---

COMMON FIELDS (Required for ALL types):
- DOC_TYPE: One of ["INVOICE", "OBL", "HAWB", "PACKING_LIST"]
- DOC_TYPE_CONFIDENCE: Float between 0 and 1 indicating confidence in the document type classification (e.g., 0.95 for high confidence, 0.6 for uncertain)
- TOTAL_PAGES: Integer (count of pages for this specific document)
- START_PAGE_NO: Integer (1-based page number where this document starts in the PDF)
- END_PAGE_NO: Integer (1-based page number where this document ends in the PDF)

TYPE 1: INVOICE
- INVOICE_NO: Extract as-is, preserving all characters (e.g., "0004833/E")
- INVOICE_DATE: Format as YYYYMMDDHHMMSSSS (16 digits). Example: "30.07.2025" -> "2025073000000000"
- CURRENCY_ID: 3-letter currency code (e.g., "EUR")
- INCOTERMS: Code only, uppercase (e.g., "FCA"). No location text.
- INVOICE_AMOUNT: Number (float/int), no symbols.
- CUSTOMER_ID: Extract as-is.

TYPE 2: OBL
- CUSTOMER_NAME: String
- WEIGHT: Number
- VOLUME: Number
- INCOTERMS: Code only, uppercase.

TYPE 3: HAWB
- CUSTOMER_NAME: String
- CURRENCY: String
- CARRIER: String
- HAWB_NUMBER: String
- PIECES: Integer
- WEIGHT: Number

TYPE 4: PACKING LIST
- CUSTOMER_NAME: String
- PIECES: Integer
- WEIGHT: Number

--- CRITICAL RULES ---
1. Return ONLY a valid JSON list.
2. If a field is not found, omit it.
3. Ensure START_PAGE_NO and END_PAGE_NO reflect the specific location of the document.
4. Date format must be exactly 16 digits: YYYYMMDD00000000.
5. INCOTERMS must be ONLY the code (3 letters usually), no location or extra text.

--- EXAMPLE OUTPUT ---
[
    {
        "DOC_TYPE": "INVOICE",
        "INVOICE_NO": "0004833/E",
        "INVOICE_DATE": "2025073000000000",
        "CURRENCY_ID": "EUR",
        "INCOTERMS": "FCA",
        "INVOICE_AMOUNT": 7632.00,
        "CUSTOMER_ID": "D004345",
        "DOC_TYPE_CONFIDENCE": 0.95,
        "TOTAL_PAGES": 2,
        "START_PAGE_NO": 1,
        "END_PAGE_NO": 2
    },
    {
        "DOC_TYPE": "PACKING_LIST",
        "CUSTOMER_NAME": "DEF Manufacturing",
        "PIECES": 100,
        "WEIGHT": 2500.0,
        "DOC_TYPE_CONFIDENCE": 0.88,
        "TOTAL_PAGES": 1,
        "START_PAGE_NO": 3,
        "END_PAGE_NO": 3
    }
]
"""

ROTATION_EXTRACTION_PROMPT = """Analyze page orientation and return JSON only.

For each page, determine the clockwise rotation needed to make text upright.

OUTPUT FORMAT - Return ONLY this JSON array, no explanations:
[{"PAGE_NO": 1, "ROTATION": 0}, {"PAGE_NO": 2, "ROTATION": 90}]

ROTATION VALUES (clockwise degrees to fix orientation):
- 0: Already upright
- 90: Text reads bottom-to-top, rotate 90° clockwise
- 180: Upside down, rotate 180°
- 270: Text reads top-to-bottom, rotate 270° clockwise

RULES:
1. Output ONLY the JSON array - no text before or after
2. One entry per page
3. ROTATION must be exactly: 0, 90, 180, or 270
"""

@dataclass(frozen=True)
class SplitResult:
    """Result of splitting a single document from a PDF (immutable)."""
    doc_type: str
    start_page: int
    end_page: int
    total_pages: int
    extracted_data: Dict[str, Any]
    output_file_path: str
    pages_info: List[PageInfo]


def _create_pages_info(start_page: int, end_page: int, rotation_map: Dict[int, int]) -> List[PageInfo]:
    """Pure function: Create pages info list from rotation map.

    Args:
        start_page: First page number (inclusive)
        end_page: Last page number (inclusive)
        rotation_map: Mapping from page number to rotation degrees

    Returns:
        List of PageInfo with page numbers and rotations
    """
    return [
        {'PAGE_NO': page_no, 'ROTATION': rotation_map.get(page_no, 0)}
        for page_no in range(start_page, end_page + 1)
    ]


def _extract_doc_fields(doc: Dict[str, Any], common_fields: set) -> List[DocumentField]:
    """Pure function: Extract non-common fields from document.

    Args:
        doc: Document dictionary
        common_fields: Set of field names to exclude

    Returns:
        List of DocumentField with field_id and field_value
    """
    return [
        {'field_id': field_id, 'field_value': field_value}
        for field_id, field_value in doc.items()
        if field_id not in common_fields
    ]


def _transform_document(
    doc: Dict[str, Any],
    rotation_map: Dict[int, int],
    common_fields: set
) -> ExtractedDocument:
    """Pure function: Transform raw document dict to ExtractedDocument.

    Args:
        doc: Raw document dictionary from extraction
        rotation_map: Mapping from page number to rotation
        common_fields: Set of common field names

    Returns:
        Transformed ExtractedDocument with PAGES_INFO and DOC_DATA
    """
    start_page = doc.get('START_PAGE_NO', 1)
    end_page = doc.get('END_PAGE_NO', 1)

    pages_info = _create_pages_info(start_page, end_page, rotation_map)

    doc_data = _extract_doc_fields(doc, common_fields)

    return {
        'DOC_TYPE': doc.get('DOC_TYPE', 'UNKNOWN'),
        'DOC_TYPE_CONFIDENCE': doc.get('DOC_TYPE_CONFIDENCE', 0.0),
        'TOTAL_PAGES': doc.get('TOTAL_PAGES', end_page - start_page + 1),
        'START_PAGE_NO': start_page,
        'END_PAGE_NO': end_page,
        'PAGES_INFO': pages_info,
        'DOC_DATA': doc_data
    }


class DocumentSplitter:
    """Splits PDFs into individual documents based on AI classification."""

    def __init__(self, api_key: str, model: str = 'gemini-2.5-flash', timeout_seconds: int = 300):
        """Initialize the document splitter.

        Args:
            api_key: Google Gemini API key
            model: Gemini model to use for document extraction (default: 'gemini-2.5-flash')
            timeout_seconds: Timeout for Gemini API calls in seconds (default: 300)
        """
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.rotation_model = 'gemini-3-pro-preview'
        self.timeout_seconds = timeout_seconds

    def _call_gemini_with_pdf(
        self,
        pdf_data: bytes,
        prompt: str,
        model: Optional[str] = None
    ) -> str:
        """Call Gemini API with PDF data and prompt.

        Args:
            pdf_data: PDF file content as bytes
            prompt: Text prompt for the model
            model: Model to use (default: self.model)

        Returns:
            Response text from Gemini

        Raises:
            ValueError: If Gemini response is invalid
            Exception: If API call fails
        """
        if model is None:
            model = self.model

        try:
            response = self.client.models.generate_content(
                model=model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_bytes(
                                data=pdf_data,
                                mime_type="application/pdf"
                            ),
                            types.Part.from_text(text=prompt)
                        ]
                    )
                ],
                config=types.GenerateContentConfig()
            )
        except Exception as e:
            logger.error(f"Gemini API call failed (model={model}): {e}")
            raise

        if not response.text:
            logger.error(f"Gemini returned empty response. Finish reason: {response.candidates[0].finish_reason if response.candidates else 'Unknown'}")
            raise ValueError("Gemini returned empty response")

        return response.text.strip()

    def extract_documents(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract document information from a PDF using Gemini.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of raw document dictionaries with extraction data (before transformation)

        Raises:
            ValueError: If Gemini response is invalid
            TimeoutError: If API call exceeds timeout
        """
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        result_text = self._call_gemini_with_pdf(
            pdf_data,
            DOCUMENT_EXTRACTION_PROMPT,
            model=self.model
        )
        result_text = self._clean_json_response(result_text)

        try:
            documents = json.loads(result_text)
            if not isinstance(documents, list):
                documents = [documents]

            MAX_OUTPUT_FILES = 100
            if len(documents) > MAX_OUTPUT_FILES:
                raise ValueError(
                    f"Too many documents returned by AI: {len(documents)} (max: {MAX_OUTPUT_FILES})"
                )

            return documents
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"Invalid JSON response from Gemini: {e}")

    def extract_rotation_info(self, pdf_path: str) -> List[PageInfo]:
        """Extract page rotation information from a PDF using Gemini.

        This method uses a dedicated LLM call with gemini-3-pro-preview to analyze
        page orientations and determine the rotation needed for each page.

        Args:
            pdf_path: Path to the PDF file (can be a single page or multi-page document)

        Returns:
            List of PageInfo dictionaries with PAGE_NO and ROTATION for each page

        Raises:
            ValueError: If Gemini response is invalid
        """
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        logger.info(f"Extracting rotation info for: {pdf_path}")

        result_text = self._call_gemini_with_pdf(
            pdf_data,
            ROTATION_EXTRACTION_PROMPT,
            model=self.rotation_model
        )
        logger.debug(f"Rotation extraction raw response: {result_text[:500] if result_text else 'EMPTY'}")
        result_text = self._clean_json_response(result_text)

        if not result_text:
            logger.warning("Empty response from Gemini for rotation extraction")
            raise ValueError("Empty response from Gemini rotation extraction")

        try:
            rotation_data = json.loads(result_text)
            if not isinstance(rotation_data, list):
                rotation_data = [rotation_data]

            for page_info in rotation_data:
                if 'ROTATION' in page_info and page_info['ROTATION'] not in [0, 90, 180, 270]:
                    logger.warning(f"Invalid rotation value {page_info['ROTATION']} for page {page_info.get('PAGE_NO')}, defaulting to 0")
                    page_info['ROTATION'] = 0

            return rotation_data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse rotation JSON response: {e}. Response text: {result_text[:200]}")
            raise ValueError(f"Invalid JSON response from Gemini rotation extraction: {e}")

    def extract_rotation_info_safe(self, pdf_path: str) -> Result[List[PageInfo]]:
        """Safely extract page rotation information with explicit error handling.

        This is a safe wrapper around extract_rotation_info that returns a Result type
        instead of raising exceptions, following functional programming patterns.

        Args:
            pdf_path: Path to the PDF file (can be a single page or multi-page document)

        Returns:
            Result containing either:
            - Success with List[PageInfo] if extraction succeeded
            - Failure with error message if extraction failed

        Example:
            >>> result = splitter.extract_rotation_info_safe("doc.pdf")
            >>> if result['status'] == 'success':
            ...     pages = result['data']
            >>> else:
            ...     logger.error(f"Rotation extraction failed: {result['error']}")
        """
        try:
            rotation_info = self.extract_rotation_info(pdf_path)
            return success(rotation_info)
        except Exception as e:
            error_msg = f"Failed to extract rotation info: {type(e).__name__}: {str(e)}"
            logger.warning(error_msg)
            return failure(error_msg)

    def split_and_save(
        self,
        pdf_path: str,
        output_dir: str,
        base_filename: Optional[str] = None
    ) -> ExtractionResult:
        """Extract documents from PDF, split into separate files, and save results.

        Args:
            pdf_path: Path to the input PDF file
            output_dir: Directory to save split files and results
            base_filename: Base name for output files (default: input filename)

        Returns:
            ExtractionResult with structured extraction results and file locations
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        if base_filename is None:
            base_filename = pdf_path.stem

        logger.info(f"Processing PDF: {pdf_path}")

        documents = self.extract_documents(str(pdf_path))

        logger.info(f"Found {len(documents)} documents in PDF")

        all_rotations_result = self.extract_rotation_info_safe(str(pdf_path))
        all_rotations: Dict[int, int] = {}

        if is_success(all_rotations_result):
            rotation_data = all_rotations_result['data']
            all_rotations = {page['PAGE_NO']: page['ROTATION'] for page in rotation_data}
            logger.info(f"Successfully extracted rotation info for {len(all_rotations)} pages")
        else:
            logger.warning(f"Failed to extract rotation info for source PDF: {all_rotations_result['error']}")
            logger.info("Will use default rotation (0°) for all pages")

        common_fields = {
            'DOC_TYPE', 'DOC_TYPE_CONFIDENCE', 'TOTAL_PAGES',
            'START_PAGE_NO', 'END_PAGE_NO', 'PAGES_INFO'
        }

        results = []
        for i, doc in enumerate(documents):
            doc_type = doc.get('DOC_TYPE', 'UNKNOWN')
            start_page = doc.get('START_PAGE_NO', 1)
            end_page = doc.get('END_PAGE_NO', 1)

            output_filename = f"{base_filename}_{doc_type}_{i+1}_pages_{start_page}-{end_page}.pdf"
            output_path = output_dir / output_filename
            pdf_bytes = extract_pdf_pages(str(pdf_path), start_page, end_page)
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)

            logger.info(f"  Saved {doc_type} (pages {start_page}-{end_page}) to {output_filename}")

            transformed_doc = _transform_document(doc, all_rotations, common_fields)
            results.append(transformed_doc)

        final_result = {
            'source_pdf': str(pdf_path),
            'total_documents': len(results),
            'documents': results
        }

        results_filename = f"{base_filename}_extraction_results.json"
        results_path = output_dir / results_filename
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to: {results_path}")

        return final_result

    @staticmethod
    def _clean_json_response(text: str) -> str:
        """Extract JSON from response text, handling markdown and explanatory text."""

        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()


def split_and_extract_documents(
    pdf_path: str,
    output_dir: str,
    api_key: Optional[str] = None,
    model: str = 'gemini-2.5-flash',
    base_filename: Optional[str] = None
) -> ExtractionResult:
    """Convenience function to extract and split documents from a PDF.

    Args:
        pdf_path: Path to the input PDF file
        output_dir: Directory to save split files and results
        api_key: Google Gemini API key (default: from GEMINI_API_KEY env var)
        model: Gemini model to use
        base_filename: Base name for output files (default: input filename)

    Returns:
        ExtractionResult with structured extraction results and file locations

    Example:
        >>> result = split_and_extract_documents(
        ...     "combined_docs.pdf",
        ...     "output/split_docs"
        ... )
        >>> print(f"Found {result['total_documents']} documents")
        >>> for doc in result['documents']:
        ...     print(f"  {doc['DOC_TYPE']}: pages {doc['START_PAGE_NO']}-{doc['END_PAGE_NO']}")
    """
    if api_key is None:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

    splitter = DocumentSplitter(api_key=api_key, model=model)
    return splitter.split_and_save(pdf_path, output_dir, base_filename)
