"""Document splitter for extracting and splitting PDFs by document type."""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from google import genai
from google.genai import types

from ..system_prompts import UNIFIED_EXTRACTION_PROMPT
from ..utils import extract_pdf_pages

logger = logging.getLogger(__name__)

@dataclass
class SplitResult:
    """Result of splitting a single document from a PDF."""
    doc_type: str
    start_page: int
    end_page: int
    total_pages: int
    extracted_data: Dict[str, Any]
    output_file_path: str


class DocumentSplitter:
    """Splits PDFs into individual documents based on AI classification."""

    def __init__(self, api_key: str, model: str = 'gemini-2.5-flash'):
        """Initialize the document splitter.

        Args:
            api_key: Google Gemini API key
            model: Gemini model to use
        """
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def extract_documents(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract document information from a PDF using Gemini.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            List of document dictionaries with extraction data
        """
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()

        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(
                            data=pdf_data,
                            mime_type="application/pdf"
                        ),
                        types.Part.from_text(text=UNIFIED_EXTRACTION_PROMPT)
                    ]
                )
            ]
        )

        result_text = response.text.strip()
        result_text = self._clean_json_response(result_text)

        try:
            documents = json.loads(result_text)
            if not isinstance(documents, list):
                documents = [documents]
            return documents
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {result_text}")
            raise ValueError(f"Invalid JSON response from Gemini: {e}")

    def split_and_save(
        self,
        pdf_path: str,
        output_dir: str,
        base_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract documents from PDF, split into separate files, and save results.

        Args:
            pdf_path: Path to the input PDF file
            output_dir: Directory to save split files and results
            base_filename: Base name for output files (default: input filename)

        Returns:
            Dictionary with extraction results and file locations
        """
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        if base_filename is None:
            base_filename = pdf_path.stem

        logger.info(f"Processing PDF: {pdf_path}")

        documents = self.extract_documents(str(pdf_path))

        logger.info(f"Found {len(documents)} documents in PDF")

        results = []
        for i, doc in enumerate(documents):
            doc_type = doc.get('DOC_TYPE', 'UNKNOWN')
            start_page = doc.get('START_PAGE_NO', 1)
            end_page = doc.get('END_PAGE_NO', 1)
            total_pages = doc.get('TOTAL_PAGES', end_page - start_page + 1)

            output_filename = f"{base_filename}_{doc_type}_{i+1}_pages_{start_page}-{end_page}.pdf"
            output_path = output_dir / output_filename

            pdf_bytes = extract_pdf_pages(str(pdf_path), start_page, end_page)
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)

            logger.info(f"  Saved {doc_type} (pages {start_page}-{end_page}) to {output_filename}")

            doc['FILE_PATH'] = str(output_path)
            doc['FILE_NAME'] = output_filename

            results.append(doc)

        final_result = {
            'source_pdf': str(pdf_path),
            'output_directory': str(output_dir),
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
        """Remove markdown code blocks from response text."""
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
) -> Dict[str, Any]:
    """Convenience function to extract and split documents from a PDF.

    Args:
        pdf_path: Path to the input PDF file
        output_dir: Directory to save split files and results
        api_key: Google Gemini API key (default: from GEMINI_API_KEY env var)
        model: Gemini model to use
        base_filename: Base name for output files (default: input filename)

    Returns:
        Dictionary with extraction results and file locations

    Example:
        >>> result = split_and_extract_documents(
        ...     "combined_docs.pdf",
        ...     "output/split_docs"
        ... )
        >>> print(f"Found {result['total_documents']} documents")
        >>> for doc in result['documents']:
        ...     print(f"  {doc['DOC_TYPE']}: {doc['FILE_PATH']}")
    """
    if api_key is None:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

    splitter = DocumentSplitter(api_key=api_key, model=model)
    return splitter.split_and_save(pdf_path, output_dir, base_filename)
