"""Test the conditional processing based on .txt file existence."""
import os
import tempfile
import json
from pathlib import Path
from modules.utils import find_ground_truth_txt, load_ground_truth_from_txt


def test_find_ground_truth_txt():
    """Test finding .txt files for PDFs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test PDF
        pdf_path = Path(tmpdir) / "test_invoice.PDF"
        pdf_path.write_text("dummy pdf content")
        
        # Test case 1: No .txt file exists
        result = find_ground_truth_txt(str(pdf_path))
        assert result is None, "Should return None when no .txt file exists"
        
        # Test case 2: .txt file exists
        txt_path = Path(tmpdir) / "test_invoice.txt"
        txt_path.write_text('{"test": "data"}')
        
        result = find_ground_truth_txt(str(pdf_path))
        assert result is not None, "Should return path when .txt file exists"
        assert result == str(txt_path), f"Expected {txt_path}, got {result}"
        
        print("✓ test_find_ground_truth_txt passed")


def test_load_ground_truth_from_txt():
    """Test loading ground truth from .txt files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        txt_path = Path(tmpdir) / "test_gt.txt"
        
        # Test case 1: Simple JSON
        simple_data = {"INVOICE_NO": "12345", "AMOUNT": 100.50}
        txt_path.write_text(json.dumps(simple_data))
        
        result = load_ground_truth_from_txt(str(txt_path))
        assert result == simple_data, f"Expected {simple_data}, got {result}"
        
        # Test case 2: JSON with OCC wrapper
        occ_data = {
            "OCC": {
                "INVOICE_NO": "67890",
                "AMOUNT": 200.75
            }
        }
        txt_path.write_text(json.dumps(occ_data))
        
        result = load_ground_truth_from_txt(str(txt_path))
        assert result == occ_data["OCC"], f"Expected {occ_data['OCC']}, got {result}"
        
        # Test case 3: Invalid JSON
        txt_path.write_text("not valid json")
        result = load_ground_truth_from_txt(str(txt_path))
        assert result is None, "Should return None for invalid JSON"
        
        print("✓ test_load_ground_truth_from_txt passed")


def test_with_actual_sample_files():
    """Test with actual sample files from the repository."""
    # Test with an invoice that should have a .txt file
    invoice_pdf = "sampels/combined-sampels/82913549_SC_INVOICE_pzbcjfz29eyk+gzo_+yhoq00000000.PDF"
    
    if Path(invoice_pdf).exists():
        txt_path = find_ground_truth_txt(invoice_pdf)
        assert txt_path is not None, f"Invoice {invoice_pdf} should have a .txt file"
        
        ground_truth = load_ground_truth_from_txt(txt_path)
        assert ground_truth is not None, f"Should be able to load ground truth from {txt_path}"
        assert "INVOICE_NO" in ground_truth, "Ground truth should contain INVOICE_NO field"
        
        print(f"✓ Found and loaded ground truth for {invoice_pdf}")
        print(f"  .txt file: {txt_path}")
        print(f"  Fields: {list(ground_truth.keys())}")
    else:
        print(f"⚠ Sample file {invoice_pdf} not found, skipping test")
    
    # Test with a BOL that should NOT have a .txt file
    bol_pdf = "sampels/combined-sampels/81123207_SC_BOL_izdyfcgqbuc5c5olirpxrg00000000.PDF"
    
    if Path(bol_pdf).exists():
        txt_path = find_ground_truth_txt(bol_pdf)
        assert txt_path is None, f"BOL {bol_pdf} should NOT have a .txt file"
        print(f"✓ Confirmed no .txt file for {bol_pdf}")
    else:
        print(f"⚠ Sample file {bol_pdf} not found, skipping test")


if __name__ == "__main__":
    print("Testing .txt file detection and loading...")
    print("=" * 70)
    
    test_find_ground_truth_txt()
    test_load_ground_truth_from_txt()
    test_with_actual_sample_files()
    
    print("=" * 70)
    print("All tests passed!")
