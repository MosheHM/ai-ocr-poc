
import sys
import os
from pathlib import Path
import json
import logging
import pandas as pd
from modules.transformation.data_processor import DataProcessor
from modules.validators.validation_engine import ValidationEngine
from modules.utils.report_builder import ExcelReportBuilder

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pipeline():
    logger.info("Starting Pipeline Test")
    
    # 1. Mock Data (Simulate Output from Document Splitter)
    mock_results = {
        "documents": [
            {
                "DOC_TYPE": "INVOICE",
                "START_PAGE_NO": 1,
                "DOC_DATA": [
                    {"field_id": "invoice_no", "field_value": "INV-1001"},
                    {"field_id": "invoice_date", "field_value": "2023102600000000"},
                    {"field_id": "currency_id", "field_value": "USD"},
                    {"field_id": "incoterms", "field_value": "CIF"},
                    {"field_id": "invoice_amount", "field_value": 1500.50},
                    {"field_id": "customer_id", "field_value": "CUST-01"}
                ]
            },
            {
                "DOC_TYPE": "INVOICE", # Invalid Invoice
                "START_PAGE_NO": 2,
                "DOC_DATA": [
                    {"field_id": "invoice_no", "field_value": "INV-1002"},
                    {"field_id": "invoice_date", "field_value": "BAD-DATE"}, # Error
                    {"field_id": "currency_id", "field_value": "US"}, # Error (too short)
                    {"field_id": "incoterms", "field_value": "CIF"},
                    {"field_id": "invoice_amount", "field_value": "NotNumber"}, # Error
                    {"field_id": "customer_id", "field_value": "CUST-02"}
                ]
            },
            {
                "DOC_TYPE": "HAWB",
                "START_PAGE_NO": 3,
                "DOC_DATA": [
                    {"field_id": "customer_name", "field_value": "Logistics Co"},
                    {"field_id": "currency", "field_value": "EUR"},
                    {"field_id": "carrier", "field_value": "DHL"},
                    {"field_id": "hawb_number", "field_value": "H123456789"},
                    {"field_id": "pieces", "field_value": 10},
                    {"field_id": "weight", "field_value": 500.25}
                ]
            },
            {
                "DOC_TYPE": "OBL",
                "START_PAGE_NO": 4,
                "DOC_DATA": [
                    {"field_id": "customer_name", "field_value": "Shipping Corp"},
                    {"field_id": "weight", "field_value": 1200.0},
                    {"field_id": "volume", "field_value": 15.5},
                    {"field_id": "incoterms", "field_value": "FOB"}
                ]
            }
        ]
    }

    # 2. Transformation
    logger.info("Running DataProcessor...")
    dataframes = DataProcessor.process_extraction_results(mock_results)
    
    # Assertions for Transformation
    assert "INVOICE" in dataframes
    assert "HAWB" in dataframes
    assert "OBL" in dataframes
    assert len(dataframes["INVOICE"]) == 2
    
    # 3. Validation
    logger.info("Running ValidationEngine...")
    validator = ValidationEngine()
    validated_dfs, errors = validator.validate_all(dataframes)
    
    logger.info(f"Validation complete. Found {len(errors)} errors.")
    
    # Assertions for Validation
    # Invoice 2 should have errors
    invoice_errors = [e for e in errors if e.doc_type == "INVOICE" and e.row == 1] # Row 1 is 2nd record
    assert len(invoice_errors) > 0
    logger.info("Confirmed errors found for invalid invoice.")

    # 4. Reporting
    logger.info("Running ExcelReportBuilder...")
    builder = ExcelReportBuilder()
    output_path = Path("test_output/processing_report.xlsx")
    builder.build_report(validated_dfs, errors, output_path)
    
    assert output_path.exists()
    logger.info(f"Report generated at: {output_path}")
    
    # Optional: Read back excel to verify sheets?
    xls = pd.ExcelFile(output_path)
    sheet_names = xls.sheet_names
    logger.info(f"Generated Sheets: {sheet_names}")
    
    assert "INVOICE" in sheet_names
    assert "HAWB" in sheet_names
    assert "Validation Summary" in sheet_names
    
    logger.info("Test Passed Successfully!")

if __name__ == "__main__":
    test_pipeline()
