
"""Utilities for generating Excel reports."""
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def create_excel_report(results: Dict[str, Any], output_path: Path) -> Path:
    """Create an Excel report from extraction results.
    
    Args:
        results: The validated extraction results dictionary.
        output_path: The path where the Excel file should be saved.
        
    Returns:
        The path to the created Excel file.
    """
    logger.info(f"Creating Excel report at {output_path}")
    
    flattened_data = []
    
    source_pdf = Path(results.get("source_pdf", "Unknown")).name
    
    for doc_idx, doc in enumerate(results.get("documents", [])):
        doc_type = doc.get("DOC_TYPE", "Unknown")
        page_no = doc.get("START_PAGE_NO", "Unknown")
        
        if "DOC_DATA" in doc:
            for field in doc["DOC_DATA"]:
                errors = "; ".join(field.get("errors", []))
                
                row = {
                    "Source PDF": source_pdf,
                    "Document Index": doc_idx + 1,
                    "Document Type": doc_type,
                    "Page": page_no,
                    "Field ID": field.get("field_id"),
                    "Field Value": field.get("field_value"),
                    "Errors": errors,
                    "Has Error": "Yes" if errors else "No"
                }
                flattened_data.append(row)
    
    if not flattened_data:
        logger.warning("No data to write to Excel report")
        # Create an empty DataFrame with columns
        df = pd.DataFrame(columns=["Source PDF", "Document Index", "Document Type", "Page", "Field ID", "Field Value", "Errors", "Has Error"])
    else:
        df = pd.DataFrame(flattened_data)
        
    try:
        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to Excel
        df.to_excel(output_path, index=False, engine='openpyxl')
        logger.info(f"Excel report created successfully: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to create Excel report: {e}")
        raise
