"""
Unit tests for validate_split_docs.py

Tests the core functionality without requiring API key
"""

import json
from pathlib import Path
import pytest
from validate_split_docs import SplitDocumentValidator


class TestSplitDocumentValidator:
    """Test cases for SplitDocumentValidator"""
    
    def test_parse_org_xml(self):
        """Test parsing of ORG XML files"""
        # Use a real ORG XML file from the samples
        samples_dir = Path(__file__).parent / 'sampels' / 'combined-sampels'
        org_xml_files = list(samples_dir.glob("*_ORG_*.xml"))
        
        if not org_xml_files:
            pytest.skip("No ORG XML files found in samples directory")
        
        # Create validator (no API key needed for parsing)
        validator = SplitDocumentValidator(api_key="dummy")
        
        # Parse the first ORG XML file
        org_xml_path = org_xml_files[0]
        result = validator.parse_org_xml(str(org_xml_path))
        
        # Verify structure
        assert 'parent_com_id' in result
        assert 'split_docs' in result
        assert isinstance(result['split_docs'], list)
        
        # If there are split docs, verify their structure
        if result['split_docs']:
            split_doc = result['split_docs'][0]
            assert 'filing_com_id' in split_doc
            assert 'doc_type_name' in split_doc
            assert 'pages' in split_doc
            assert 'total_pages' in split_doc
            
            print(f"\nParsed ORG XML: {org_xml_path.name}")
            print(f"Parent ComId: {result['parent_com_id']}")
            print(f"Split docs count: {len(result['split_docs'])}")
            print(f"First split doc ComId: {split_doc['filing_com_id']}")
            print(f"First split doc type: {split_doc['doc_type_name']}")
            print(f"First split doc pages: {split_doc['total_pages']}")
    
    def test_parse_split_doc_pages(self):
        """Test parsing of page information from split docs"""
        samples_dir = Path(__file__).parent / 'sampels' / 'combined-sampels'
        org_xml_files = list(samples_dir.glob("*_ORG_*.xml"))
        
        if not org_xml_files:
            pytest.skip("No ORG XML files found in samples directory")
        
        validator = SplitDocumentValidator(api_key="dummy")
        result = validator.parse_org_xml(str(org_xml_files[0]))
        
        # Find a split doc with multiple pages
        multi_page_doc = None
        for split_doc in result['split_docs']:
            if split_doc['total_pages'] > 1:
                multi_page_doc = split_doc
                break
        
        if multi_page_doc:
            print(f"\nMulti-page doc found:")
            print(f"Total pages: {multi_page_doc['total_pages']}")
            print(f"Page details: {multi_page_doc['pages']}")
            
            # Verify page count matches
            assert len(multi_page_doc['pages']) == multi_page_doc['total_pages']
            
            # Verify each page has required fields
            for page in multi_page_doc['pages']:
                assert 'page_num' in page
                assert 'rotate' in page
    
    def test_create_extraction_prompt(self):
        """Test prompt creation for different document types"""
        validator = SplitDocumentValidator(api_key="dummy")
        
        # Test invoice prompt
        invoice_prompt = validator._create_extraction_prompt("Supplier Invoice")
        assert "INVOICE_NO" in invoice_prompt
        assert "INVOICE_DATE" in invoice_prompt
        assert "TOTAL_PAGES" in invoice_prompt
        
        # Test packing list prompt
        packing_prompt = validator._create_extraction_prompt("Packing List")
        assert "PACKING" in packing_prompt.upper()
        assert "TOTAL_PAGES" in packing_prompt
        
        # Test generic prompt
        generic_prompt = validator._create_extraction_prompt("Unknown Doc")
        assert "TOTAL_PAGES" in generic_prompt
    
    def test_remove_code_blocks(self):
        """Test removal of markdown code blocks"""
        validator = SplitDocumentValidator(api_key="dummy")
        
        # Test with json code block
        text = '```json\n{"key": "value"}\n```'
        result = validator._remove_code_blocks(text)
        assert result == '{"key": "value"}'
        
        # Test with plain code block
        text = '```\n{"key": "value"}\n```'
        result = validator._remove_code_blocks(text)
        assert result == '{"key": "value"}'
        
        # Test without code blocks
        text = '{"key": "value"}'
        result = validator._remove_code_blocks(text)
        assert result == '{"key": "value"}'
    
    def test_file_path_construction(self):
        """Test that file paths are constructed correctly"""
        samples_dir = Path(__file__).parent / 'sampels' / 'combined-sampels'
        split_docs_dir = Path(__file__).parent / 'sampels' / 'invoices-sampels'
        
        org_xml_files = list(samples_dir.glob("*_ORG_*.xml"))
        
        if not org_xml_files:
            pytest.skip("No ORG XML files found in samples directory")
        
        validator = SplitDocumentValidator(api_key="dummy")
        result = validator.parse_org_xml(str(org_xml_files[0]))
        
        # Check if we can construct file paths for split docs
        for split_doc in result['split_docs']:
            filing_com_id = split_doc['filing_com_id']
            primary_num = split_doc['primary_num']
            
            base_filename = f"{primary_num}_SC_INVOICE_{filing_com_id}"
            pdf_path = split_docs_dir / f"{base_filename}.PDF"
            
            print(f"\nLooking for: {pdf_path.name}")
            print(f"Exists: {pdf_path.exists()}")
            
            # At least some should exist
            if pdf_path.exists():
                assert pdf_path.suffix == '.PDF'
                break


def test_sample_files_exist():
    """Verify that sample files are available"""
    samples_dir = Path(__file__).parent / 'sampels' / 'combined-sampels'
    split_docs_dir = Path(__file__).parent / 'sampels' / 'invoices-sampels'
    
    assert samples_dir.exists(), f"Samples directory not found: {samples_dir}"
    assert split_docs_dir.exists(), f"Split docs directory not found: {split_docs_dir}"
    
    org_xml_files = list(samples_dir.glob("*_ORG_*.xml"))
    assert len(org_xml_files) > 0, "No ORG XML files found"
    
    print(f"\nFound {len(org_xml_files)} ORG XML files")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
