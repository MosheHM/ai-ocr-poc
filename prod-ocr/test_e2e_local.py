
import logging
import os
import shutil
import zipfile
from pathlib import Path
from modules.validators.data_validator import validate_extraction_results
from modules.utils.excel_utils import create_excel_report
from modules.utils.zip_utils import create_results_zip

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_e2e_flow():
    # Setup paths
    base_dir = Path("test_output_e2e")
    output_dir = base_dir / "output"
    
    # Clean previous run
    if base_dir.exists():
        shutil.rmtree(base_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Created test directory: {base_dir}")

    # 1. Mock Extraction Results
    sample_results = {
        "source_pdf": str(base_dir / "test_source.pdf"),
        "total_documents": 1,
        "documents": [
            {
                "DOC_TYPE": "INVOICE",
                "START_PAGE_NO": 1,
                "DOC_DATA": [
                    {"field_id": "INVOICE_NO", "field_value": "INV-2024-001"},
                    {"field_id": "AMOUNT", "field_value": "invalid_number"}, # Error expected
                    {"field_id": "DATE", "field_value": ""} # Error expected for empty
                ]
            }
        ]
    }
    
    # Create dummy source PDF
    Path(sample_results["source_pdf"]).touch()
    
    # Create dummy split PDF in output (to simulate splitter)
    (output_dir / "split_doc_1.pdf").touch()

    try:
        # 2. Validation
        print("\n--- Step 1: Validation ---")
        validated_results = validate_extraction_results(sample_results)
        errors_found = validated_results["documents"][0]["DOC_DATA"][1].get("errors")
        print(f"Validation Errors found: {errors_found}")
        assert errors_found, "Expected validation errors not found!"

        # 3. Excel Generation
        print("\n--- Step 2: Excel Generation ---")
        excel_path = output_dir / "extraction_report.xlsx"
        create_excel_report(validated_results, excel_path)
        
        if excel_path.exists():
            print(f"✅ Excel file created at: {excel_path}")
            print(f"   Size: {excel_path.stat().st_size} bytes")
        else:
            raise Exception("❌ Excel file was NOT created!")

        # 4. Packaging (Zip)
        print("\n--- Step 3: Packaging (Zip) ---")
        zip_path = Path(create_results_zip(str(output_dir), validated_results, "final_results.zip"))
        print(f"✅ Zip file created at: {zip_path}")

        # 5. Verify Zip Content
        print("\n--- Step 4: Verifying Zip Content ---")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            print("Files in ZIP:", file_list)
            
            # Check for Excel file
            if "extraction_report.xlsx" in file_list:
                print("✅ extraction_report.xlsx found in ZIP")
            else:
                raise Exception("❌ extraction_report.xlsx MISSING from ZIP")

            # Check for JSON
            if "extraction_results.json" in file_list:
                print("✅ extraction_results.json found in ZIP")
            else:
                raise Exception("❌ extraction_results.json MISSING from ZIP")

            # Check for Source PDF (optional, based on logic)
            # The logic in zip_utils adds source_pdf if it exists. 
            # Our mock source_pdf is outside output_dir, so it should be added by absolute path logic or name logic.
            # Looking at zip_utils: `zipf.write(source_pdf, arcname=source_filename)`
            if "test_source.pdf" in file_list:
                 print("✅ test_source.pdf found in ZIP")

        print("\n🎉 E2E Verification PASSED!")

    except Exception as e:
        logger.exception("Test Failed")
        raise
    finally:
        # Cleanup
        # if base_dir.exists():
        #    shutil.rmtree(base_dir)
        pass

if __name__ == "__main__":
    test_e2e_flow()
