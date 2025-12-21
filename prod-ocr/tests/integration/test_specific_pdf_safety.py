import pytest
import os
from pathlib import Path
from dotenv import load_dotenv
from modules.document_splitter.splitter import split_and_extract_documents

# Load environment variables from .env file
load_dotenv()

@pytest.mark.integration
class TestSpecificPdfSafety:
    """Integration test for specific PDF file to verify safety settings."""

    def test_specific_pdf_extraction(self, tmp_path):
        """
        Test extraction on the specific PDF file:
        84526616_ORG_arzlhvywte2zczalgoitew00000000.PDF
        
        This verifies that the safety settings allow processing of this file
        which previously might have triggered safety blocks.
        """
        # Locate the PDF file
        # Assuming the test is run from the project root (prod-ocr)
        # The file is at ../samples/combined-sampels/84526616_ORG_arzlhvywte2zczalgoitew00000000.PDF
        # We need to resolve this relative to the test file or project root
        
        # Try to find the file relative to project root
        project_root = Path.cwd()
        pdf_path = project_root.parent / "samples" / "combined-sampels" / "84526616_ORG_arzlhvywte2zczalgoitew00000000.PDF"
        
        if not pdf_path.exists():
            # Fallback: try relative to this test file if running from elsewhere
            current_file = Path(__file__)
            pdf_path = current_file.parents[3] / "samples" / "combined-sampels" / "84526616_ORG_arzlhvywte2zczalgoitew00000000.PDF"

        if not pdf_path.exists():
            pytest.skip(f"Specific PDF file not found at {pdf_path}. Skipping test.")

        print(f"Testing with PDF: {pdf_path}")
        
        # Ensure API key is available
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            pytest.fail("GEMINI_API_KEY not found in environment variables")

        # Create output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        try:
            # Run extraction
            result = split_and_extract_documents(
                pdf_path=str(pdf_path),
                output_dir=str(output_dir),
                api_key=api_key
            )

            # Assertions
            assert result is not None
            assert 'documents' in result
            assert len(result['documents']) > 0
            
            # Verify we got some documents
            print(f"\nSuccessfully extracted {len(result['documents'])} documents")
            for doc in result['documents']:
                print(f"- {doc.get('doc_type', 'unknown')}")
                
            # Verify files were created
            assert any(output_dir.iterdir())

        except Exception as e:
            pytest.fail(f"Extraction failed with error: {e}")
